"""
HypermediaTools - Consolidated Hypermedia Interaction Utilities

This module provides all hypermedia-related functionality for agents:
- RDF/Turtle parsing and graph operations
- W3C Thing Description (TD) parsing
- Workspace operations (join/leave/update)
- Agent discovery and management
- Protocol discovery through semantic links
- Metadata generation for agent descriptions
"""

import requests
import bspl
from rdflib import Graph, Namespace, Literal, URIRef, BNode
from rdflib.namespace import RDF


# =============================================================================
# RDF Namespaces
# =============================================================================

TD = Namespace('https://www.w3.org/2019/wot/td#')
HMAS = Namespace('https://purl.org/hmas/')
BSPL = Namespace("https://purl.org/hmas/bspl/")
HTV = Namespace("http://www.w3.org/2011/http#")
HCTL = Namespace("https://www.w3.org/2019/wot/hypermedia#")
JACAMO = Namespace("https://purl.org/hmas/jacamo/")
GOODRELATIONS = Namespace("http://purl.org/goodrelations/v1#")


# =============================================================================
# RDF/Graph Utilities
# =============================================================================

def get_model(data: str, rdf_format='turtle') -> Graph:
    """
    Parse RDF data into an RDFLib Graph.

    Args:
        data: RDF data as string
        rdf_format: Format of the RDF data (default: 'turtle')

    Returns:
        RDFLib Graph object
    """
    return Graph().parse(data=data, format=rdf_format)


# =============================================================================
# Agent Discovery and Management
# =============================================================================

class HypermediaAgent:
    """
    Represents an agent discovered through hypermedia.
    Parses agent Thing Descriptions to extract name, addresses, and roles.
    """

    def __init__(self, body_uri: str):
        self.body_uri = body_uri
        self.name = None
        self.addresses = []
        self.roles = []
        self.body: Graph = None

    def parse_agent(self, body_graph: str):
        """
        Parse agent Thing Description from RDF/Turtle.

        Args:
            body_graph: Agent TD as Turtle string
        """
        self.body = get_model(body_graph)
        self.set_name()
        self.set_roles()
        self.set_addresses()

    def set_name(self):
        """Extract agent name from Thing Description."""
        if self.body is None:
            raise ValueError("Body not parsed yet")
        name = self.body.value(subject=URIRef(self.body_uri), predicate=TD.title)
        if name:
            self.name = str(name)
        else:
            raise ValueError("Agent name not found in Thing Description")
        return self.name

    def set_roles(self):
        """Extract roles the agent can enact from Thing Description."""
        if self.body is None:
            raise ValueError("Body not parsed yet")

        query = f"""
        PREFIX bspl: <{str(BSPL)}>
        SELECT ?roleName ?protocolName
        WHERE {{
          <{self.body_uri}> bspl:hasRole ?role .
          OPTIONAL {{ ?role bspl:roleName ?roleName . }}
          OPTIONAL {{ ?role bspl:protocolName ?protocolName . }}
        }}
        """

        results = []
        for row in self.body.query(query):
            results.append(str(row.roleName))

        self.roles = results
        return self.roles

    def set_addresses(self):
        """Extract communication endpoint from Thing Description."""
        if self.body is None:
            raise ValueError("Body not parsed yet")

        target = get_adapter_endpoint(self.body)
        if target:
            # Parse URL to extract host and port
            target = target.removeprefix("http://")
            target = target.removeprefix("https://")
            target = target.removesuffix("/")
            parts = target.split(":")
            host = parts[0]
            port = int(parts[1]) if len(parts) > 1 else 80
            self.addresses.append((host, port))

        return self.addresses

    def __str__(self):
        return f"Agent(name={self.name}, body_uri={self.body_uri}, addresses={self.addresses}, roles={self.roles})"

    def __repr__(self):
        return self.__str__()


def get_agents_in_workspace(workspace_uri: str, own_address: str) -> list[HypermediaAgent]:
    """
    Discover all agents in a workspace by traversing artifacts.

    Args:
        workspace_uri: URI of the workspace
        own_address: URI of own artifact (to exclude self)

    Returns:
        List of HypermediaAgent objects
    """
    response = requests.get(workspace_uri + 'artifacts/')
    artifacts_graph = get_model(response.text)

    # Find all artifacts in workspace
    artifacts = list(artifacts_graph.subjects(RDF.type, HMAS.Artifact))

    agents = []
    for artifact in artifacts:
        # Only process agent bodies (not own body)
        if "body_" in str(artifact) and str(artifact) != own_address:
            agents.append(str(artifact))

    # Parse each agent's Thing Description
    agents_list = []
    for agent_uri in agents:
        response = requests.get(agent_uri)
        agent = HypermediaAgent(agent_uri)
        agent.parse_agent(response.text)
        agents_list.append(agent)

    return agents_list


def get_agents(workspace_uri: str, own_address: str) -> list[HypermediaAgent]:
    """
    Convenience wrapper for get_agents_in_workspace.

    Args:
        workspace_uri: URI of the workspace
        own_address: URI of own artifact

    Returns:
        List of discovered HypermediaAgent objects
    """
    return get_agents_in_workspace(workspace_uri, own_address)


# =============================================================================
# Workspace Operations
# =============================================================================

def join_workspace(workspace_uri: str, web_id: str, agent_name: str, metadata: str) -> tuple[bool, str | None]:
    """
    Join a workspace and register agent presence.

    Args:
        workspace_uri: URI of the workspace to join
        web_id: Agent's web identifier
        agent_name: Agent's local name
        metadata: RDF metadata describing the agent (Thing Description)

    Returns:
        Tuple of (success: bool, artifact_address: str | None)
    """
    response = post_workspace(workspace_uri + 'join', web_id, agent_name, metadata)

    # Extract artifact address from response
    graph = get_model(response.text)
    artifact_address = None
    for subj in graph.subjects(RDF.type, JACAMO.Body):
        artifact_address = str(subj)
        break

    return response.status_code == 200, artifact_address


def leave_workspace(workspace_uri: str, web_id: str, agent_name: str) -> bool:
    """
    Leave a workspace and unregister agent presence.

    Args:
        workspace_uri: URI of the workspace to leave
        web_id: Agent's web identifier
        agent_name: Agent's local name

    Returns:
        True if successful, False otherwise
    """
    response = post_workspace(workspace_uri + 'leave', web_id, agent_name)
    return response.status_code == 200


def post_workspace(workspace_uri: str, web_id: str, agent_name: str, metadata: str = None) -> requests.Response:
    """
    Send a POST request to a workspace endpoint.

    Args:
        workspace_uri: URI to POST to
        web_id: Agent's web identifier
        agent_name: Agent's local name
        metadata: Optional RDF metadata to include

    Returns:
        HTTP Response object
    """
    headers = {
        'X-Agent-WebID': web_id,
        'X-Agent-LocalName': agent_name,
        'Content-Type': 'text/turtle'
    }

    return requests.post(workspace_uri, headers=headers, data=metadata)


def update_body(body_uri: str, web_id: str, agent_name: str, metadata: str) -> int:
    """
    Update an agent's Thing Description in the workspace.

    Args:
        body_uri: URI of the agent's body artifact
        web_id: Agent's web identifier
        agent_name: Agent's local name
        metadata: RDF metadata to append

    Returns:
        HTTP status code
    """
    # Get current representation
    old_representation = requests.get(body_uri).text

    headers = {
        'X-Agent-WebID': web_id,
        'X-Agent-LocalName': agent_name,
        'Content-Type': 'text/turtle'
    }

    # Append new metadata to existing
    response = requests.put(body_uri, headers=headers, data=old_representation + metadata)
    return response.status_code


# =============================================================================
# Protocol Discovery
# =============================================================================

def get_protocol(workspace_uri: str, protocol_name: str = None) -> bspl.protocol.Protocol:
    """
    Discover and load a BSPL protocol from the workspace.

    Args:
        workspace_uri: URI of the workspace
        protocol_name: Optional specific protocol name to load

    Returns:
        BSPL Protocol object
    """
    response = requests.get(workspace_uri)
    workspace_graph = get_model(response.text)

    # Find all protocol links in workspace
    protocol_links = get_protocol_references(workspace_graph)

    # Fetch and concatenate all protocol specifications
    protocols_str = get_protocols_as_string(protocol_links)

    # Parse BSPL specifications
    spec = bspl.load(protocols_str)

    if protocol_name:
        return spec.protocols[protocol_name]
    else:
        # Return first protocol if no name specified
        first_key = next(iter(spec.protocols))
        return spec.protocols[first_key]


def get_protocol_references(workspace_graph: Graph) -> list[str]:
    """
    Extract protocol URIs from workspace RDF graph.

    Args:
        workspace_graph: RDFLib Graph of workspace

    Returns:
        List of protocol URIs
    """
    protocols = []
    for triple in workspace_graph.triples((None, BSPL.protocol, None)):
        protocols.append(str(triple[2]))
    return protocols


def get_protocols_as_string(protocol_links: list[str]) -> str:
    """
    Fetch protocol specifications from URIs and concatenate.

    Args:
        protocol_links: List of protocol URIs

    Returns:
        Concatenated BSPL protocol specifications
    """
    protocols = ""
    for link in protocol_links:
        protocols += requests.get(link).text
        protocols += "\n"
    return protocols


# =============================================================================
# Semantic Protocol Discovery (Goal-oriented)
# =============================================================================

def get_protocol_name_from_goal(workspace_uri: str, goal_item: str) -> str | None:
    """
    Discover protocol needed for a goal item through semantic reasoning.
    First checks if item is offered, then finds associated protocol.

    Args:
        workspace_uri: URI of the workspace
        goal_item: URI of the goal item/artifact

    Returns:
        Protocol name or None if not found
    """
    # Check if item is being offered
    workspace_description = requests.get(workspace_uri).text
    model = get_model(workspace_description)

    query_offering = f"""
    PREFIX gr: <http://purl.org/goodrelations/v1#>

    SELECT ?offering WHERE {{
      ?offering a gr:Offering ;
          gr:includesObject ?taq .

      ?taq a gr:TypeAndQuantityNode ;
          gr:typeOfGood <{goal_item}> .
    }}
    """

    qres = model.query(query_offering)
    if len(qres) == 0:
        print("No offering found for wanted artifact")
        return None

    # Check artifact for protocol link
    artifact_description = requests.get(goal_item).text
    model = get_model(artifact_description)

    query_protocol = f"""
    PREFIX hmas: <https://purl.org/hmas/>
    PREFIX bspl: <https://purl.org/hmas/bspl/>
    PREFIX td: <https://www.w3.org/2019/wot/td#>

    SELECT ?protocol_name WHERE {{
      <{goal_item}> a hmas:Artifact ;
          bspl:useProtocol ?protocol_name .
    }}
    """

    qres = model.query(query_protocol)
    if len(qres) == 0:
        print("No interaction protocol found for wanted artifact")
        return None

    for q in qres:
        return q.protocol_name.value

    return None


def get_protocol_name_from_goal_offering(workspace_uri: str, goal_item: str) -> str | None:
    """
    Alternative approach: Find protocol directly from offering.
    Protocol link is on the offering rather than the item.

    Args:
        workspace_uri: URI of the workspace
        goal_item: URI of the goal item/artifact

    Returns:
        Protocol name or None if not found
    """
    workspace_description = requests.get(workspace_uri).text
    model = get_model(workspace_description)

    query = f"""
    PREFIX gr: <http://purl.org/goodrelations/v1#>
    PREFIX bspl: <https://purl.org/hmas/bspl/>

    SELECT ?protocol_name WHERE {{
      ?offering a gr:Offering ;
          bspl:useProtocol ?protocol_name ;
          gr:includesObject ?taq .

      ?taq a gr:TypeAndQuantityNode ;
          gr:typeOfGood <{goal_item}> .
    }}
    """

    qres = model.query(query)
    if len(qres) == 0:
        print("No offering found for wanted artifact")
        return None

    for q in qres:
        return q.protocol_name.value

    return None


# =============================================================================
# Thing Description Parsing
# =============================================================================

def get_action(model: Graph, affordance_name: str) -> URIRef | None:
    """
    Find an action affordance by name in a Thing Description.

    Args:
        model: RDFLib Graph of Thing Description
        affordance_name: Name of the action to find

    Returns:
        URIRef of action or None if not found
    """
    for action in model.subjects(RDF.type, TD.ActionAffordance):
        name = model.value(action, TD.name)
        if name == Literal(affordance_name):
            return action
    return None


def get_form(model: Graph, target_action: URIRef) -> URIRef | None:
    """
    Get the form associated with an action.

    Args:
        model: RDFLib Graph of Thing Description
        target_action: URIRef of the action

    Returns:
        URIRef of form or None
    """
    return model.value(subject=target_action, predicate=TD.hasForm)


def create_request(model: Graph, form: URIRef) -> dict:
    """
    Extract HTTP request information from a form.

    Args:
        model: RDFLib Graph
        form: URIRef of the form

    Returns:
        Dictionary with method, url, and headers
    """
    http_method = model.value(form, HTV.methodName)
    target_url = model.value(form, HCTL.hasTarget)
    content_type = model.value(form, HCTL.forContentType)

    return {
        "method": str(http_method),
        "url": str(target_url),
        "headers": {"Accept": str(content_type)} if content_type else {},
    }


def get_adapter_endpoint(model: Graph) -> str | None:
    """
    Extract the BSPL adapter endpoint from an agent's Thing Description.
    Looks for the "sendMessage" action affordance.

    Args:
        model: RDFLib Graph of agent's Thing Description

    Returns:
        Endpoint URL or None
    """
    for action in model.subjects(RDF.type, TD.ActionAffordance):
        name = model.value(action, TD.name)
        if name == Literal("sendMessage"):
            form = model.value(action, TD.hasForm)
            target = model.value(form, HCTL.hasTarget)
            return str(target)
    return None


# =============================================================================
# Metadata Generation
# =============================================================================

def generate_body_metadata(adapter_endpoint: str) -> str:
    """
    Generate RDF metadata for an agent's body (Thing Description).
    Includes the sendMessage action affordance for BSPL adapter.

    Args:
        adapter_endpoint: Port number for the adapter endpoint

    Returns:
        RDF/Turtle string
    """
    return f"""
    @prefix td: <https://www.w3.org/2019/wot/td#>.
    @prefix hctl: <https://www.w3.org/2019/wot/hypermedia#> .
    @prefix htv: <http://www.w3.org/2011/http#> .

    <#artifact>
        td:hasActionAffordance [ a td:ActionAffordance;
        td:name "sendMessage";
        td:hasForm [
            htv:methodName "GET";
            hctl:hasTarget <http://127.0.0.1:{adapter_endpoint}/>;
            hctl:forContentType "text/plain";
            hctl:hasOperationType td:invokeAction;
        ]
    ].
    """


def generate_role_metadata(artifact_address: str, role_names: list[str], protocol_name: str) -> str:
    """
    Generate RDF metadata advertising agent roles.
    Used to inform other agents which roles this agent can enact.

    Args:
        artifact_address: URI of the agent's artifact
        role_names: List of role names the agent can enact
        protocol_name: Name of the protocol these roles belong to

    Returns:
        RDF/Turtle string
    """
    # Generate RDF blocks for each role
    roles_rdf = "\n".join(
        f"""        [
                a bspl:Role ;
                bspl:roleName "{role}" ;
                bspl:protocolName "{protocol_name}" ;
            ]"""
        for role in role_names
    )

    # Combine into final RDF string
    rdf_output = f"""@prefix bspl: <https://purl.org/hmas/bspl/> .

    <{artifact_address}>
        bspl:hasRole
    {roles_rdf} .
    """

    return rdf_output


# =============================================================================
# Convenience Aliases
# =============================================================================

# Keep backward compatibility with old function names
get_body_metadata = generate_body_metadata
body_role_metadata = generate_role_metadata
get_protocol_name_from_goal_two = get_protocol_name_from_goal_offering
get_kiko_adapter_target = get_adapter_endpoint
