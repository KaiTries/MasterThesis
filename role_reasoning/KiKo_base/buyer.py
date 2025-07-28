"""
This agent initiates the logistics protocol by generating orders and handling packed responses.
"""

import logging
import bspl
from bspl.adapter import Adapter
from bspl.protocol import Message
from utils import create_systems_for_protocol, role_capable_of, setup_adapter


buy = bspl.load_file("buy.bspl").export("Buy")


agents = {
    "Seller": [("127.0.0.1", 8004)],
    "Buyer": [("127.0.0.1", 8005)]
}


logger = logging.getLogger("buyer")
# logger.setLevel(logging.DEBUG)


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



if __name__ == "__main__":
    logger.info("Starting Buyer...")
    # find protocol
    # reason which role
    role = role_capable_of(capabilities=CAPABILITIES, protocol=buy)
    systems = create_systems_for_protocol(protocol=buy)
    adapter = Adapter(role, systems, agents)
    # setup role
    setup_adapter(reactions=REACTIONS, adapter=adapter, protocol=buy, role=role)
    # start adapter
    # try to buy something if we are buyer
    if role == "Buyer":
        initial_message = buy.roles[role].messages()["Pay"]
        adapter.start(adapter.send(pay_message(initial_message,1,"item",1)))