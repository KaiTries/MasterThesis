from rdflib.namespace import RDF
import requests
import bspl
from rdflib import Graph, Namespace, Literal
import time

# Must buy groceries
# Will go into the bazaar and initiate the protocol to buy something
WEB_ID = 'http://localhost:8001'
AgentName = 'buyer'
BAZAAR_URI = 'http://localhost:8080/workspaces/bazaar/'
TD = Namespace('https://www.w3.org/2019/wot/td#')   
HTV = Namespace("http://www.w3.org/2011/http#")
HCTL = Namespace("https://www.w3.org/2019/wot/hypermedia#")

def postWorkspace(workspace_uri):
    headers = {
        'X-Agent-WebID': WEB_ID,
        'X-Agent-LocalName': AgentName
    }

    response = requests.post(workspace_uri,headers=headers)
    return response.status_code



def getAction(model: Graph, affordanceName: str):
    for action in model.subjects(RDF.type, TD.ActionAffordance):
        name = model.value(action, TD.name)
        if name == Literal(affordanceName):
            print("found action", action)
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
    workspace = Graph().parse(data=response.text,format='turtle')
    action = getAction(workspace, 'getProtocol')
    form = getForm(workspace, action)
    params = createRequest(workspace, form)
    response = requests.request(**params)
    protocol = bspl.load(response.text)
    print(protocol)







if __name__ == '__main__':
    success = postWorkspace(BAZAAR_URI + 'join') 

    getProtocol(BAZAAR_URI)
    time.sleep(5)

    success = postWorkspace(BAZAAR_URI + 'leave')
    pass