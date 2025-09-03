from rdflib.namespace import RDF
import requests
import bspl
from rdflib import Graph, Namespace, Literal, URIRef, BNode
from rdflib.collection import Collection
from bspl.protocol import Protocol
from bspl.adapter import Adapter
import logging

logger = logging.getLogger("agent")


class Agent:
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
        self.body = getModel(body_graph)
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
        return self.name

    def set_roles(self):
        if self.body is None:
            raise ValueError("Body not parsed yet")
        for role in self.body.objects(subject=URIRef(self.body_uri), predicate=self.bspl_uri.hasRole):
            if isinstance(role, Literal):
                self.roles.append(str(role))
            elif isinstance(role, BNode):
                for item in Collection(self.body, role):
                    if isinstance(item, Literal):
                        self.roles.append(str(item))
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


def getModel(data: str, format='turtle'):
    return Graph().parse(data=data, format=format)


def joinWorkspace(workspace_uri, WEB_ID, AgentName, metadata):
    headers = {
        'X-Agent-WebID': WEB_ID,
        'X-Agent-LocalName': AgentName,
        'Content-Type': 'text/turtle'
    }

    response = requests.post(workspace_uri + 'join',headers=headers, data=metadata)
    g = getModel(response.text)
    artifact_address = None
    for subj in g.subjects(RDF.type, JACAMO.Body):
        artifact_address = str(subj)
        break

    return response.status_code == 200, artifact_address

def leaveWorkspace(workspace_uri, WEB_ID, AgentName):
    headers = {
        'X-Agent-WebID': WEB_ID,
        'X-Agent-LocalName': AgentName,
        'Content-Type': 'text/turtle'
    }

    response = requests.post(workspace_uri + 'leave',headers=headers)
    return response.status_code == 200

def postWorkspace(workspace_uri, WEB_ID, AgentName):
    headers = {
        'X-Agent-WebID': WEB_ID,
        'X-Agent-LocalName': AgentName,
        'Content-Type': 'text/turtle'
    }

    response = requests.post(workspace_uri,headers=headers)
    return response.status_code

def updateBody(body_uri,WEB_ID, AgentName,metadata):
    old_representation = requests.get(body_uri).text

    headers = {
        'X-Agent-WebID': WEB_ID,
        'X-Agent-LocalName': AgentName,
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
HTV = Namespace("http://www.w3.org/2011/http#")
HCTL = Namespace("https://www.w3.org/2019/wot/hypermedia#")
JACAMO = Namespace("https://purl.org/hmas/jacamo/")


def getAction(model: Graph, affordanceName: str):
    for action in model.subjects(RDF.type, TD.ActionAffordance):
        name = model.value(action, TD.name)
        if name == Literal(affordanceName):
            logger.info(f"found action '{name}'")
            print("found action", name)
            return action

def getForm(model: Graph, target_action: Graph):
    return model.value(subject=target_action, predicate=TD.hasForm)

def createRequest(model: Graph, form: Graph):
    http_method = model.value(form, HTV.methodName)
    target_url = model.value(form, HCTL.hasTarget)
    content_type = model.value(form, HCTL.forContentType)

    return {
        "method": str(http_method),
        "url": str(target_url),
        "headers": {"Accept": str(content_type)} if content_type else {},
    }

def getProtocol(workspace, protocolName):
    response = requests.get(workspace)
    workspace = getModel(response.text)
    action = getAction(workspace, 'getProtocol')
    form = getForm(workspace, action)
    params = createRequest(workspace, form)
    response = requests.request(**params)
    protocol = bspl.load(response.text).protocols[protocolName]
    return protocol

def get_kiko_adapter_target(model):
    # Find all ActionAffordances
    for action in model.subjects(RDF.type, TD.ActionAffordance):
        name = model.value(action, TD.name)
        if name == Literal("kikoAdapter"):
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
def getAgentsIn(workspace: str, ownAddr: str):
    response = requests.get(workspace + 'artifacts/')
    containedArtifacts = getModel(response.text)
    artifacts = list(containedArtifacts.subjects(RDF.type, HMAS.Artifact))
    agents = []
    for artifact in artifacts:
        if "body_" in str(artifact):
            agents.append(str(artifact))

    agents_list: list[Agent] = []
    for agent in agents:
        if agent != ownAddr:
            response = requests.get(str(agent))
            new_agent = Agent(str(agent))
            new_agent.parse_agent(response.text)
            agents_list.append(new_agent)

    return agents_list

def getAgents(workspace, ownAddr):
    agents_in_workspace = getAgentsIn(workspace=workspace, ownAddr=ownAddr)
    return agents_in_workspace

# Return first role that agent is capable of
def role_capable_of(capabilities, protocol: Protocol):
    roles = protocol.roles
    capabilities_for_role = {}
    for rname, role in roles.items():
        capabilities_for_role[rname] = []
        messages = role.messages()
        for mname, message in messages.items():
            if message.sender == role:
                capabilities_for_role[rname].append(message)           

    for rolename, needed_capabilities in capabilities_for_role.items():
        if all([a.name in capabilities for a in needed_capabilities]):
            return rolename


def setup_adapter(reactions, adapter: Adapter, protocol: Protocol, role):
    messages = protocol.roles[role].messages()
    for mname, message in messages.items():
        if mname in reactions:
             adapter.reaction(message)(reactions[mname])
 