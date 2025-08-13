from rdflib.namespace import RDF
import requests
import bspl
from rdflib import Graph, Namespace, Literal
import time
from agents.utils.helpers import getProtocol, getAgentsIn
from agents.agent.knowledge import *
# Must buy groceries
# Will go into the bazaar and initiate the protocol to buy something


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