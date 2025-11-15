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
from typing import Optional
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
# Workspace Discovery and Crawling
# =============================================================================

def get_workspaces_in(workspace_uri: str) -> list[str]:
    """
    Discover sub-workspaces within a workspace.

    Args:
        workspace_uri: URI of the workspace to explore

    Returns:
        List of sub-workspace URIs (cleaned, without fragments)
    """
    try:
        response = requests.get(workspace_uri)
        if response.status_code != 200:
            return []

        graph = get_model(response.text)

        # Query for contained workspaces
        query = f"""
        PREFIX hmas: <https://purl.org/hmas/>

        SELECT ?workspace WHERE {{
          ?workspace a hmas:Workspace .
        }}
        """

        workspaces = []
        for row in graph.query(query):
            workspace_str = str(row.workspace)

            # Clean up the URI: remove fragment identifier and ensure trailing slash
            workspace_clean = clean_workspace_uri(workspace_str)

            # Only include if it's a different workspace (not self)
            workspace_uri_clean = clean_workspace_uri(workspace_uri)
            if workspace_clean != workspace_uri_clean:
                workspaces.append(workspace_clean)

        return workspaces
    except Exception as e:
        print(f"Error discovering workspaces in {workspace_uri}: {e}")
        return []


def clean_workspace_uri(uri: str) -> str:
    """
    Clean a workspace URI by removing fragment identifiers and normalizing.

    Args:
        uri: Raw workspace URI (may include #fragment)

    Returns:
        Cleaned workspace URI without fragment, ending with /

    Example:
        "http://localhost:8080/workspaces/bazaar#workspace"
        -> "http://localhost:8080/workspaces/bazaar/"
    """
    # Remove fragment identifier (everything after #)
    if '#' in uri:
        uri = uri.split('#')[0]

    # Ensure it ends with /
    if not uri.endswith('/'):
        uri += '/'

    return uri


def get_artifacts_in(workspace_uri: str) -> list[str]:
    """
    Get all artifacts in a workspace.

    Args:
        workspace_uri: URI of the workspace

    Returns:
        List of artifact URIs
    """
    try:
        # Check the artifacts endpoint
        artifacts_uri = workspace_uri.rstrip('/') + '/artifacts/'
        response = requests.get(artifacts_uri)
        if response.status_code != 200:
            return []

        graph = get_model(response.text)

        # Query for all artifacts
        query = """
        PREFIX hmas: <https://purl.org/hmas/>

        SELECT ?artifact WHERE {
          ?artifact a hmas:Artifact .
        }
        """

        artifacts = []
        for row in graph.query(query):
            artifacts.append(str(row.artifact))

        return artifacts
    except Exception as e:
        print(f"Error discovering artifacts in {workspace_uri}: {e}")
        return []


def find_workspace_containing_artifact(
    base_uri: str,
    goal_artifact_uri: str,
    max_depth: int = 5,
    _current_depth: int = 0
) -> Optional[str]:
    """
    Recursively crawl workspaces to find the one containing a goal artifact.
    This implements true hypermedia-driven discovery.

    Args:
        base_uri: Starting URI (can be root or a workspace)
        goal_artifact_uri: URI of the artifact to find
        max_depth: Maximum depth to search (prevent infinite loops)
        _current_depth: Internal parameter for recursion tracking

    Returns:
        URI of workspace containing the artifact, or None if not found
    """
    if _current_depth >= max_depth:
        print(f"Max depth {max_depth} reached, stopping search")
        return None

    print(f"{'  ' * _current_depth}Searching workspace: {base_uri}")

    # Ensure base_uri ends with /
    if not base_uri.endswith('/'):
        base_uri += '/'

    # Check if goal artifact is in current workspace
    artifacts = get_artifacts_in(base_uri)
    print(f"{'  ' * _current_depth}Found {len(artifacts)} artifacts")

    for artifact in artifacts:
        # Check if this artifact matches the goal (exact match or contains the fragment)
        if artifact == goal_artifact_uri or goal_artifact_uri in artifact:
            # Clean the workspace URI before returning
            clean_uri = clean_workspace_uri(base_uri)
            print(f"{'  ' * _current_depth}✓ Found goal artifact in workspace: {clean_uri}")
            return clean_uri

    # If not found, search sub-workspaces
    sub_workspaces = get_workspaces_in(base_uri)
    print(f"{'  ' * _current_depth}Found {len(sub_workspaces)} sub-workspaces")

    for sub_workspace in sub_workspaces:
        result = find_workspace_containing_artifact(
            sub_workspace,
            goal_artifact_uri,
            max_depth,
            _current_depth + 1
        )
        if result:
            return result

    # Not found in this branch
    return None


def discover_workspace_for_goal(
    base_uri: str,
    goal_artifact_uri: str,
    max_depth: int = 5
) -> Optional[str]:
    """
    Discover which workspace contains a goal artifact by crawling from a base URI.
    This is the main entry point for workspace discovery.

    Example:
        # Start with just the base URL
        workspace = discover_workspace_for_goal(
            "http://localhost:8080/",
            "http://localhost:8080/workspaces/bazaar/artifacts/rug#artifact"
        )
        # Returns: "http://localhost:8080/workspaces/bazaar/"

    Args:
        base_uri: Base URI to start crawling from (e.g., "http://localhost:8080/")
        goal_artifact_uri: Full URI of the goal artifact
        max_depth: Maximum depth to search (default: 5)

    Returns:
        URI of workspace containing the artifact, or None if not found
    """
    print(f"\n=== Starting workspace discovery ===")
    print(f"Base URI: {base_uri}")
    print(f"Goal artifact: {goal_artifact_uri}")
    print(f"Max depth: {max_depth}")
    print()

    # Try to find workspaces at the base URI first
    workspaces = get_workspaces_in(base_uri)

    if not workspaces:
        # No workspaces at base, treat base as a workspace itself
        print("No sub-workspaces found at base, checking base as workspace...")
        result = find_workspace_containing_artifact(base_uri, goal_artifact_uri, max_depth)
    else:
        # Search through discovered workspaces
        print(f"Found {len(workspaces)} workspaces at base URI")
        result = None
        for workspace in workspaces:
            result = find_workspace_containing_artifact(workspace, goal_artifact_uri, max_depth)
            if result:
                break

    if result:
        print(f"\n✓ Discovery successful! Workspace: {result}")
    else:
        print(f"\n✗ Discovery failed. Artifact not found in any workspace.")

    print("=== Workspace discovery complete ===\n")
    return result


def get_artifacts_by_class(workspace_uri: str, artifact_class: str) -> list[str]:
    """
    Get artifacts of a specific RDF class from a workspace.

    This function queries individual artifacts since the collection endpoint
    doesn't include all type information.

    Example:
        # Find all rugs in a workspace
        rugs = get_artifacts_by_class(
            "http://localhost:8080/workspaces/bazaar/",
            "http://example.org/Rug"
        )
        # Returns: ["http://localhost:8080/workspaces/bazaar/artifacts/rug#artifact"]

    Args:
        workspace_uri: URI of the workspace to search
        artifact_class: Full URI of the RDF class (e.g., "http://example.org/Rug")

    Returns:
        List of artifact URIs that are instances of the given class
    """
    try:
        # Step 1: Get all artifacts from the collection endpoint
        artifacts_uri = workspace_uri.rstrip('/') + '/artifacts/'
        response = requests.get(artifacts_uri)
        if response.status_code != 200:
            return []

        graph = get_model(response.text)

        # Get all artifacts (just their URIs)
        query_all = """
        PREFIX hmas: <https://purl.org/hmas/>
        SELECT ?artifact WHERE {
          ?artifact a hmas:Artifact .
        }
        """

        all_artifacts = []
        for row in graph.query(query_all):
            all_artifacts.append(str(row.artifact))

        # Step 2: Query each individual artifact for its full type information
        matching_artifacts = []
        for artifact_uri in all_artifacts:
            # Remove fragment to get the artifact's representation URI
            artifact_repr_uri = artifact_uri.split('#')[0]

            # Fetch the individual artifact
            try:
                artifact_response = requests.get(artifact_repr_uri, timeout=5)
                if artifact_response.status_code == 200:
                    artifact_graph = get_model(artifact_response.text)

                    # Check if this artifact has the requested class
                    check_query = f"""
                    SELECT ?s WHERE {{
                      ?s a <{artifact_class}> .
                    }}
                    """
                    results = list(artifact_graph.query(check_query))
                    if results:
                        # Found an artifact with the matching class
                        matching_artifacts.append(artifact_uri)
            except Exception as e:
                print(f"  Warning: Could not fetch artifact {artifact_repr_uri}: {e}")
                continue

        return matching_artifacts
    except Exception as e:
        print(f"Error discovering artifacts of class {artifact_class} in {workspace_uri}: {e}")
        return []


def find_workspace_containing_artifact_class(
    base_uri: str,
    artifact_class: str,
    max_depth: int = 5,
    _current_depth: int = 0
) -> tuple[Optional[str], Optional[str]]:
    """
    Recursively crawl workspaces to find one containing an artifact of a specific class.
    This enables truly autonomous discovery - agents only need to know what TYPE of thing
    they're looking for, not the exact URI.

    Example:
        # Find any rug, wherever it may be
        workspace, artifact = find_workspace_containing_artifact_class(
            "http://localhost:8080/",
            "http://example.org/Rug"
        )
        # Returns: ("http://localhost:8080/workspaces/bazaar/",
        #           "http://localhost:8080/workspaces/bazaar/artifacts/rug#artifact")

    Args:
        base_uri: Starting URI (can be root or a workspace)
        artifact_class: Full URI of the RDF class to search for
        max_depth: Maximum depth to search (prevent infinite loops)
        _current_depth: Internal parameter for recursion tracking

    Returns:
        Tuple of (workspace_uri, artifact_uri) or (None, None) if not found
    """
    if _current_depth >= max_depth:
        print(f"Max depth {max_depth} reached, stopping search")
        return None, None

    print(f"{'  ' * _current_depth}Searching workspace: {base_uri}")

    # Ensure base_uri ends with /
    if not base_uri.endswith('/'):
        base_uri += '/'

    # Check if an artifact of this class exists in current workspace
    artifacts = get_artifacts_by_class(base_uri, artifact_class)
    print(f"{'  ' * _current_depth}Found {len(artifacts)} artifact(s) of class")

    if artifacts:
        # Return the first matching artifact
        clean_uri = clean_workspace_uri(base_uri)
        print(f"{'  ' * _current_depth}✓ Found artifact of class in workspace: {clean_uri}")
        return clean_uri, artifacts[0]

    # If not found, search sub-workspaces
    sub_workspaces = get_workspaces_in(base_uri)
    print(f"{'  ' * _current_depth}Found {len(sub_workspaces)} sub-workspaces")

    for sub_workspace in sub_workspaces:
        workspace, artifact = find_workspace_containing_artifact_class(
            sub_workspace,
            artifact_class,
            max_depth,
            _current_depth + 1
        )
        if workspace:
            return workspace, artifact

    # Not found in this branch
    return None, None


def discover_workspace_by_artifact_class(
    base_uri: str,
    artifact_class: str,
    max_depth: int = 5
) -> tuple[Optional[str], Optional[str]]:
    """
    Discover which workspace contains an artifact of a specific class.
    This is the main entry point for class-based workspace discovery.

    This represents the most autonomous form of discovery - the agent only needs:
    - A base URI to start from
    - The semantic type of artifact it's looking for

    Everything else (workspace location, exact artifact URI) is discovered through
    hypermedia traversal and semantic queries.

    Example:
        # Agent only knows it wants a rug (ex:Rug class)
        workspace, rug_uri = discover_workspace_by_artifact_class(
            "http://localhost:8080/",
            "http://example.org/Rug"
        )
        # Discovers: ("http://localhost:8080/workspaces/bazaar/",
        #             "http://localhost:8080/workspaces/bazaar/artifacts/rug#artifact")

    Args:
        base_uri: Base URI to start crawling from
        artifact_class: Full URI of the RDF class to search for
        max_depth: Maximum depth to search (default: 5)

    Returns:
        Tuple of (workspace_uri, artifact_uri) or (None, None) if not found
    """

    # Try to find workspaces at the base URI first
    workspaces = get_workspaces_in(base_uri)

    if not workspaces:
        # No workspaces at base, treat base as a workspace itself
        workspace, artifact = find_workspace_containing_artifact_class(
            base_uri, artifact_class, max_depth
        )
    else:
        # Search through discovered workspaces
        workspace = None
        artifact = None
        for ws in workspaces:
            workspace, artifact = find_workspace_containing_artifact_class(
                ws, artifact_class, max_depth
            )
            if workspace:
                break

    return workspace, artifact


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
# Semantic Role Reasoning
# =============================================================================

def get_role_semantics(protocol_uri: str) -> dict:
    """
    Get semantic information about roles in a protocol.

    Queries the protocol for role descriptions including goals, required capabilities,
    and message sending/receiving patterns. This enables agents to reason about which
    role they should take.

    Example:
        semantics = get_role_semantics("http://localhost:8005/protocols/buy_protocol")
        # Returns: {
        #     "Buyer": {
        #         "goal": "http://purl.org/goodrelations/v1#Buy",
        #         "required_capability": "Pay",
        #         "sends": ["Pay"],
        #         "receives": ["Give"],
        #         "description": "Acquires items by paying"
        #     },
        #     "Seller": { ... }
        # }

    Args:
        protocol_uri: URI of the protocol

    Returns:
        Dictionary mapping role names to their semantic properties,
        or empty dict if no semantics found
    """
    try:
        # Fetch protocol metadata
        response = requests.get(protocol_uri, timeout=5)
        if response.status_code != 200:
            print(f"Could not fetch protocol at {protocol_uri}")
            return {}

        # Parse RDF
        graph = get_model(response.text)

        # Query for role semantics
        query = """
        PREFIX bspl: <https://purl.org/hmas/bspl/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT ?role ?roleName ?goal ?capability ?sends ?receives ?description WHERE {
          ?role a bspl:Role ;
                bspl:roleName ?roleName .

          OPTIONAL { ?role bspl:hasGoal ?goal }
          OPTIONAL { ?role bspl:requiresCapability ?capability }
          OPTIONAL { ?role bspl:sendsMessage ?sends }
          OPTIONAL { ?role bspl:receivesMessage ?receives }
          OPTIONAL { ?role rdfs:comment ?description }
        }
        """

        # Build result dictionary
        roles = {}
        for row in graph.query(query):
            role_name = str(row.roleName)

            if role_name not in roles:
                roles[role_name] = {
                    "uri": str(row.role),
                    "goal": str(row.goal) if row.goal else None,
                    "required_capability": str(row.capability) if row.capability else None,
                    "sends": [],
                    "receives": [],
                    "description": str(row.description) if row.description else None
                }

            # Collect messages (there may be multiple)
            if row.sends and str(row.sends) not in roles[role_name]["sends"]:
                roles[role_name]["sends"].append(str(row.sends))
            if row.receives and str(row.receives) not in roles[role_name]["receives"]:
                roles[role_name]["receives"].append(str(row.receives))

        return roles

    except Exception as e:
        print(f"Error getting role semantics for {protocol_uri}: {e}")
        return {}


def score_role_match(
    role_name: str,
    role_semantics: dict,
    agent_goal: str,
    agent_capabilities: set
) -> int:
    """
    Calculate how well a role matches an agent's goal and capabilities.

    Scoring system (strict matching):
    - Goal must match for role to be viable
    - Goal match: +10
    - Goal mismatch: incompatible (return 0)
    - Required capability available: +5
    - Missing required capability: incompatible (return 0)
    - Additional compatible capabilities: +1 each

    Args:
        role_name: Name of the role
        role_semantics: Semantic properties of the role
        agent_goal: Agent's goal URI (e.g., "http://purl.org/goodrelations/v1#Buy")
        agent_capabilities: Set of agent's capabilities (e.g., {"Pay", "Give"})

    Returns:
        Compatibility score (higher is better, 0 means incompatible)
    """
    score = 0

    # Goal alignment (REQUIRED - if goal doesn't match, role is unsuitable)
    if role_semantics.get("goal") == agent_goal:
        score += 10
        print(f"  {role_name}: goal matches ({agent_goal}) +10")
    else:
        # Goal mismatch - this role is not suitable for the agent's goal
        print(f"  {role_name}: goal mismatch (want {agent_goal}, role has {role_semantics.get('goal')}) - incompatible")
        return 0  # Incompatible due to goal mismatch

    # Required capability match (important - weight: 5)
    required_cap = role_semantics.get("required_capability")
    if required_cap:
        if required_cap in agent_capabilities:
            score += 5
            print(f"  {role_name}: has required capability ({required_cap}) +5")
        else:
            # Can't take this role - missing required capability
            print(f"  {role_name}: missing required capability ({required_cap}) - incompatible")
            return 0  # Incompatible
    else:
        print(f"  {role_name}: no required capability specified")

    # Additional message capabilities (nice to have - weight: 1 each)
    for msg in role_semantics.get("sends", []):
        if msg in agent_capabilities:
            score += 1
            print(f"  {role_name}: can send {msg} +1")

    print(f"  {role_name}: total score = {score}")
    return score


def reason_role_for_goal(
    protocol_uri: str,
    agent_goal: str,
    agent_capabilities: set,
    verbose: bool = True
) -> Optional[str]:
    """
    Reason which role an agent should take in a protocol based on its goal and capabilities.

    This implements semantic role reasoning - the agent doesn't need to know role names,
    it only needs to know what it wants to do (goal) and what it can do (capabilities).

    Example:
        role = reason_role_for_goal(
            "http://localhost:8005/protocols/buy_protocol",
            "http://purl.org/goodrelations/v1#Buy",  # I want to buy
            {"Pay"}  # I can pay
        )
        # Returns: "Buyer"

    Args:
        protocol_uri: URI of the protocol
        agent_goal: Agent's goal (e.g., gr:Buy, gr:Sell)
        agent_capabilities: Set of agent's capabilities
        verbose: Print reasoning steps (default: True)

    Returns:
        Role name that best matches, or None if no compatible role found
    """
    if verbose:
        print(f"\n=== Role Reasoning ===")
        print(f"Protocol: {protocol_uri}")
        print(f"Agent goal: {agent_goal}")
        print(f"Agent capabilities: {agent_capabilities}")
        print()

    # Get role semantics
    roles = get_role_semantics(protocol_uri)

    if not roles:
        if verbose:
            print("✗ No role semantics found for protocol")
        return None

    if verbose:
        print(f"Found {len(roles)} role(s) with semantics: {list(roles.keys())}")
        print()

    # Score each role
    scores = {}
    for role_name, role_sem in roles.items():
        if verbose:
            print(f"Evaluating {role_name}:")
        score = score_role_match(role_name, role_sem, agent_goal, agent_capabilities)
        scores[role_name] = score
        if verbose:
            print()

    # Find best role
    if not scores or max(scores.values()) == 0:
        if verbose:
            print("✗ No compatible role found")
        return None

    best_role = max(scores, key=scores.get)
    best_score = scores[best_role]

    if verbose:
        print(f"✓ Best role: {best_role} (score: {best_score})")
        print("=== Role Reasoning Complete ===\n")

    return best_role


# =============================================================================
# Convenience Aliases
# =============================================================================

# Keep backward compatibility with old function names
get_body_metadata = generate_body_metadata
body_role_metadata = generate_role_metadata
get_protocol_name_from_goal_two = get_protocol_name_from_goal_offering
get_kiko_adapter_target = get_adapter_endpoint
