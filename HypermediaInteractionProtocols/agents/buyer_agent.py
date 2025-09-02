from rdflib.namespace import RDF
import requests
import logging
import bspl
from bspl.adapter import MetaAdapter
from bspl.protocol import Message
from knowledge import *
from helpers import *
import time
# Must buy groceries
# Will go into the bazaar and initiate the protocol to buy something
logger = logging.getLogger("buyer")
NAME = "BuyerAgent"
SELF = [('127.0.0.1',8011)]
OWN_ADDR = 'http://localhost:8080/workspaces/bazaar/artifacts/body_buyer#artifact'

adapter = MetaAdapter(name=NAME, systems={}, agents={NAME: SELF}, debug=True)

##### Capabilities
def pay_message(msg: Message, buyID, itemID, money):
    logger.info(f"Initiating buy protocol for {itemID}")
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
    success, artifact_address = joinWorkspace(BAZAAR_URI,WEB_ID=WEB_ID, AgentName=NAME)
    if not success:
        logger.error("Could not join the bazaar workspace")
        exit(1)
    success = updateBody(artifact_address,WEB_ID=WEB_ID, AgentName=NAME,metadata=get_body_metadata(artifact_address))
    print("Updated body metadata:", success)
    #protocol = getProtocol(BAZAAR_URI,"Buy")
    agents = getAgents(BAZAAR_URI, artifact_address)
    for agent in agents:
        adapter.upsert_agent(agent.name, agent.addresses)
    time.sleep(10)
    success = leaveWorkspace(BAZAAR_URI,WEB_ID=WEB_ID,AgentName=NAME)
    pass