from rdflib.namespace import RDF
import requests
import bspl
from rdflib import Graph, Namespace, Literal
from bspl.protocol import Protocol
from bspl.adapter import Adapter

# Namespaces
TD = Namespace('https://www.w3.org/2019/wot/td#')   
HTV = Namespace("http://www.w3.org/2011/http#")
HCTL = Namespace("https://www.w3.org/2019/wot/hypermedia#")
JACAMO = Namespace("https://purl.org/hmas/jacamo/")

# Given raw text returns RDF Graph
def getModel(data: str, format='turtle'):
    return Graph().parse(data=data, format=format)


# post request to a workspace
def postWorkspace(workspace_uri, WEB_ID, AgentName):
    headers = {
        'X-Agent-WebID': WEB_ID,
        'X-Agent-LocalName': AgentName,
        'Content-Type': 'text/turtle'
    }

    response = requests.post(workspace_uri,headers=headers)
    return response.status_code

# update body of agent in specific workspace
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
def getAction(model: Graph, affordanceName: str):
    for action in model.subjects(RDF.type, TD.ActionAffordance):
        name = model.value(action, TD.name)
        if name == Literal(affordanceName):
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
    protocol = bspl.load(response.text).export(protocolName)
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
    agents = list(containedArtifacts.subjects(RDF.type, JACAMO.Body))
    print("Agents of type jacamo:Body:", agents)
    agentsList = {}
    for agent in agents:
        if str(agent) != ownAddr:
            response = requests.get(agent)
            target = get_kiko_adapter_target(getModel(response.text))
            target_clean = target.removeprefix('http://').removesuffix('/').split(':')
            agentsList[str(agent)] = (target_clean[0],int(target_clean[1]))
    return agentsList

def getAgents(workspace, ownAddr, my_role, me):
    agents_in_workspace = getAgentsIn(workspace=workspace, ownAddr=ownAddr)
    agents = {}
    agents[my_role] = me
    print(agents_in_workspace)
    print("test")

    for agent in agents_in_workspace:
        agents['Seller'] = agents_in_workspace[agent]
    return agents

def create_systems_for_protocol(protocol: Protocol):
    return {
        protocol.name.lower() : {
            "protocol" : protocol,
            "roles" : {
                protocol.roles[role] : role for role in protocol.roles
            }
        }
    }

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
 