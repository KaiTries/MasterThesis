from rdflib.namespace import RDF
import requests
import logging
import bspl
from bspl.protocol import Message
from rdflib import Graph, Namespace, Literal
import time
from agents.utils.helpers import *
from agents.buyer.knowledge import *
from agents.agent.core import HypermediaAgent
# Must buy groceries
# Will go into the bazaar and initiate the protocol to buy something
logger = logging.getLogger("buyer")


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

class BuyerAgent(HypermediaAgent):
    def __init__(self):
        super().__init__(
            name="buyer",
            web_id=WEB_ID,
            agent_name=AgentName,
            bazaar_uri=BAZAAR_URI,
            self_uri=SELF,
            me=ME,
            my_roles=MY_ROLES,
            body_metadata=BODY_METADATA,
            capabilities=CAPABILITIES,
            reactions=REACTIONS
        )

    def initial_message_func(self):
        initial_message = self.protocol.roles[self.my_roles[0]].messages()["Pay"]
        return pay_message(initial_message,1,'item',1)


if __name__ == '__main__':
    agent = BuyerAgent()
    agent.run(
        protocol_name="Buy",
        initial_message_func=agent.initial_message_func
    )

# if __name__ == '__main__':
#     success = postWorkspace(BAZAAR_URI + 'join',WEB_ID=WEB_ID, AgentName=AgentName) 
#     success = updateBody(BAZAAR_URI + 'artifacts/body_buyer',WEB_ID=WEB_ID, AgentName=AgentName,metadata=BODY_METADATA)
#     protocol = getProtocol(BAZAAR_URI,"Buy")
#     agents = getAgents(BAZAAR_URI, SELF, MY_ROLES, ME)
#     systems = create_systems_for_protocol(protocol=protocol)
#     print(agents)
#     adapter = Adapter(MY_ROLES[0],systems=systems, agents=agents)
#     setup_adapter(reactions=REACTIONS, adapter=adapter, protocol=protocol, role=MY_ROLES[0])
#     time.sleep(5)
#     initial_message = protocol.roles[MY_ROLES[0]].messages()['Pay']
#     adapter.start(adapter.send(pay_message(initial_message,1,'item',1)))

#     success = postWorkspace(BAZAAR_URI + 'leave',WEB_ID=WEB_ID,AgentName=AgentName)
#     pass