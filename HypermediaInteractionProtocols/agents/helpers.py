from rdflib.namespace import RDF
import requests
import bspl
from rdflib import Graph, Namespace, Literal


def getModel(data: str, format='turtle'):
    return Graph().parse(data=data, format=format)

##############################
### Helper functions to read a TD get the wanted action
### and then parse the action and execute the request
### in our context it will be used to obtain a BSPL protocol
################################
TD = Namespace('https://www.w3.org/2019/wot/td#')   
HTV = Namespace("http://www.w3.org/2011/http#")
HCTL = Namespace("https://www.w3.org/2019/wot/hypermedia#")


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

def getProtocol(workspace):
    response = requests.get(workspace)
    workspace = getModel(response.text)
    action = getAction(workspace, 'getProtocol')
    form = getForm(workspace, action)
    params = createRequest(workspace, form)
    response = requests.request(**params)
    protocol = bspl.load(response.text)
    return protocol


################################
### Helper functions to get all
### Agents that are in the same
### workspace as us
################################
def getAgentsIn(workspace: str):
    response = requests.get(workspace + 'artifacts/')
    containedArtifacts = getModel(response.text)
    print(response.text)
    pass