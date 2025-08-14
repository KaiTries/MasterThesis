from rdflib.namespace import RDF
import requests
import logging
import bspl
from bspl.protocol import Message
from rdflib import Graph, Namespace, Literal
import time
from agents.utils.helpers import *
from agents.agent.knowledge import *
# Must buy groceries
# Will go into the bazaar and initiate the protocol to buy something
logger = logging.getLogger("buyer")

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



##### Capabilities
def pay_message(msg: Message, buyID, itemID, money):
    return msg(
        buyID=buyID,
        itemID=itemID,
        money=money
    )

async def give_reaction(msg):
    logger.info(f"Buy order {msg['buyID']} for item {msg['item']} with amount: {msg['money']}$ successful")
    return msg

CAPABILITIES = {"Pay":pay_message}
REACTIONS = {"Give":give_reaction}




if __name__ == '__main__':
    success = postWorkspace(BAZAAR_URI + 'join') 
    success = updateBody(BAZAAR_URI + 'artifacts/body_buyer')
    protocol = getProtocol(BAZAAR_URI,"Buy")
    agents = getAgents(BAZAAR_URI, SELF, MY_ROLES, ME)
    systems = create_systems_for_protocol(protocol=protocol)
    print(agents)
    adapter = Adapter(MY_ROLES[0],systems=systems, agents=agents)
    setup_adapter(reactions=REACTIONS, adapter=adapter, protocol=protocol, role=MY_ROLES[0])
    time.sleep(5)
    initial_message = protocol.roles[MY_ROLES[0]].messages()['Pay']
    adapter.start(adapter.send(pay_message(initial_message,1,'item',1)))

    success = postWorkspace(BAZAAR_URI + 'leave')
    pass