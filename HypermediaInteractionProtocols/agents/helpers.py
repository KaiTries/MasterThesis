from rdflib.namespace import RDF
import requests
import bspl
from rdflib import Graph, Namespace, Literal, URIRef, BNode

class HypermediaAgent:
    # uris
    bspl_uri = Namespace("https://purl.org/hmas/bspl/")
    td_uri = Namespace('https://www.w3.org/2019/wot/td#')

    def __init__(self, body_uri: str):
        self.body_uri = body_uri
        self.name = None
        self.addresses = []
        self.roles = []
        self.body: Graph = None

    def parse_agent(self, body_graph: str):
        self.body = get_model(body_graph)
        self.set_name()
        self.set_roles()
        self.set_addresses()

    def set_name(self):
        # get the name of the agent
        if self.body is None:
            raise ValueError("Body not parsed yet")
        name = self.body.value(subject=URIRef(self.body_uri), predicate=self.td_uri.title)
        if name:
            self.name = str(name)
        else:
            raise ValueError("Body not parsed yet")
        return self.name

    def set_roles(self):
        if self.body is None:
            raise ValueError("Body not parsed yet")
        q = f"""
        PREFIX bspl: <{str(self.bspl_uri)}>
        SELECT ?roleName ?protocolName
        WHERE {{
          <{self.body_uri}> bspl:hasRole ?role .
          OPTIONAL {{ ?role bspl:roleName ?roleName . }}
          OPTIONAL {{ ?role bspl:protocolName ?protocolName . }}
        }}
        """
        results = []
        for row in self.body.query(q):
            results.append(str(row.roleName))
        # possible extension
        #    results.append({
        #        "roleName": str(row.roleName) if row.roleName else None,
        #        "protocolName": str(row.protocolName) if row.protocolName else None,
        #    })
        self.roles = results
        return self.roles

    def set_addresses(self):
        if self.body is None:
            raise ValueError("Body not parsed yet")
        target = get_kiko_adapter_target(self.body)
        if target:
            target = target.removeprefix("http://")
            target = target.removeprefix("https://")
            target = target.removesuffix("/")
            target = target.split(":")
            self.addresses.append((target[0], int(target[1]) if len(target) > 1 else 80))
        return self.addresses

    def __str__(self):
        return f"Agent(name={self.name}, body_uri={self.body_uri}, addresses={self.addresses}, roles={self.roles})"

    def __repr__(self):
        return self.__str__()


def get_model(data: str, rdf_format='turtle'):
    return Graph().parse(data=data, format=rdf_format)


def join_workspace(workspace_uri, web_id, agent_name, metadata):
    response = post_workspace(workspace_uri + 'join', web_id, agent_name, metadata)

    g = get_model(response.text)
    artifact_address = None
    for subj in g.subjects(RDF.type, JACAMO.Body):
        artifact_address = str(subj)
        break

    return response.status_code == 200, artifact_address

def leave_workspace(workspace_uri, web_id, agent_name):
    response = post_workspace(workspace_uri + 'leave', web_id, agent_name)
    return response.status_code == 200

def post_workspace(workspace_uri, web_id, agent_name, metadata=None):
    headers = {
        'X-Agent-WebID': web_id,
        'X-Agent-LocalName': agent_name,
        'Content-Type': 'text/turtle'
    }

    return requests.post(workspace_uri,headers=headers, data=metadata)

def update_body(body_uri, web_id, agent_name, metadata):
    old_representation = requests.get(body_uri).text

    headers = {
        'X-Agent-WebID': web_id,
        'X-Agent-LocalName': agent_name,
        'Content-Type': 'text/turtle'
    }

    response = requests.put(body_uri,headers=headers,data=old_representation + metadata)
    return response.status_code


##############################
### Helper functions to read a TD get the wanted action
### and then parse the action and execute the request
### in our context it will be used to obtain a BSPL protocol
################################
TD = Namespace('https://www.w3.org/2019/wot/td#')
HMAS = Namespace('https://purl.org/hmas/')
BSPL = Namespace("https://purl.org/hmas/bspl/")
HTV = Namespace("http://www.w3.org/2011/http#")
HCTL = Namespace("https://www.w3.org/2019/wot/hypermedia#")
JACAMO = Namespace("https://purl.org/hmas/jacamo/")


def get_action(model: Graph, affordance_name: str):
    for action in model.subjects(RDF.type, TD.ActionAffordance):
        name = model.value(action, TD.name)
        if name == Literal(affordance_name):
            return action
    return None


def get_form(model: Graph, target_action: Graph):
    return model.value(subject=target_action, predicate=TD.hasForm)

def create_request(model: Graph, form: Graph):
    http_method = model.value(form, HTV.methodName)
    target_url = model.value(form, HCTL.hasTarget)
    content_type = model.value(form, HCTL.forContentType)

    return {
        "method": str(http_method),
        "url": str(target_url),
        "headers": {"Accept": str(content_type)} if content_type else {},
    }


def get_contained_protocol_refs(workspace: Graph):
    protocols = []
    for triple in workspace.triples((None, BSPL.protocol, None)):
        protocols.append(str(triple[2]))
    return protocols

def get_protocols_as_string(protocol_links):
    protocols = ""
    for link in protocol_links:
        protocols += requests.get(link).text
        protocols += "\n"
    return protocols

def get_protocol(workspace, protocol_name = None):
    response = requests.get(workspace)
    workspace = get_model(response.text)
    contained_protocol_links = get_contained_protocol_refs(workspace)
    protocols_str = get_protocols_as_string(contained_protocol_links)
    protocols = bspl.load(protocols_str)
    if protocol_name:
        protocol = protocols.protocols[protocol_name]
    else:
        first_key = next(iter(protocols.protocols))
        protocol = protocols.protocols[first_key]
    return protocol

def get_kiko_adapter_target(model):
    # Find all ActionAffordances
    for action in model.subjects(RDF.type, TD.ActionAffordance):
        name = model.value(action, TD.name)
        if name == Literal("sendMessage"):
            # Get the form node
            form = model.value(action, TD.hasForm)
            # Get the target URL
            target = model.value(form, HCTL.hasTarget)
            return str(target)
    return None

################################
### Helper functions to get all
### Agents that are in the same
### workspace as us
################################
def get_agents_in(workspace: str, own_addr: str):
    response = requests.get(workspace + 'artifacts/')
    contained_artifacts = get_model(response.text)
    artifacts = list(contained_artifacts.subjects(RDF.type, HMAS.Artifact))
    agents = []
    for artifact in artifacts:
        if "body_" in str(artifact):
            agents.append(str(artifact))

    agents_list: list[HypermediaAgent] = []
    for agent in agents:
        if agent != own_addr:
            response = requests.get(str(agent))
            new_agent = HypermediaAgent(str(agent))
            new_agent.parse_agent(response.text)
            agents_list.append(new_agent)

    return agents_list

def get_agents(workspace, own_addr):
    agents_in_workspace = get_agents_in(workspace=workspace, own_addr=own_addr)
    return agents_in_workspace