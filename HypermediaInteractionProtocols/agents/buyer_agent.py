from rdflib.namespace import RDF
import requests
import bspl
from rdflib import Graph, Namespace, Literal
import time
from helpers import getProtocol, getAgentsIn

# Must buy groceries
# Will go into the bazaar and initiate the protocol to buy something
WEB_ID = 'http://localhost:8011'
AgentName = 'buyer'
BAZAAR_URI = 'http://localhost:8080/workspaces/bazaar/'

BODY_METADATA = """
@prefix td: <https://www.w3.org/2019/wot/td#>.
@prefix hctl: <https://www.w3.org/2019/wot/hypermedia#> .
@prefix htv: <http://www.w3.org/2011/http#> .

<workspaces/bazaar/artifacts/body_buyer#artifact> td:hasActionAffordance [ a td:ActionAffordance;
    td:name "kikoAdapter";
    td:hasForm [
        htv:methodName "GET";
        hctl:hasTarget <http://127.0.0.1:8011/>;
        hctl:forContentType "text/plain";
        hctl:hasOperationType td:invokeAction;
    ]
].
"""

def postWorkspace(workspace_uri):
    headers = {
        'X-Agent-WebID': WEB_ID,
        'X-Agent-LocalName': AgentName,
        'Content-Type': 'text/turtle'
    }

    response = requests.post(workspace_uri,headers=headers,data=BODY_METADATA)
    return response.status_code

def updateBody(body_uri):
    old_representation = requests.get(body_uri).text

    headers = {
        'X-Agent-WebID': WEB_ID,
        'X-Agent-LocalName': AgentName,
        'Content-Type': 'text/turtle'
    }

    response = requests.put(body_uri,headers=headers,data=old_representation + BODY_METADATA)
    return response.status_code

if __name__ == '__main__':
    success = postWorkspace(BAZAAR_URI + 'join') 
    success = updateBody(BAZAAR_URI + 'artifacts/body_buyer')
    protocol = getProtocol(BAZAAR_URI)
    agents = getAgentsIn(BAZAAR_URI)
    time.sleep(5)

    success = postWorkspace(BAZAAR_URI + 'leave')
    pass