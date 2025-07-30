"""
This agent initiates the logistics protocol by generating orders and handling packed responses.
"""

import logging
from bspl.adapter import Adapter
from bspl.protocol import Message, Protocol
import bspl
from utils import create_systems_for_protocol, role_capable_of, setup_adapter

buy = bspl.load_file("buy.bspl").export("Buy")

agents = {
    "Seller": [("127.0.0.1", 8004)],
    "Buyer": [("127.0.0.1", 8005)]
}

logger = logging.getLogger("seller")

async def give_m(msg):
    logger.info(f"Received buy order {msg['buyID']} for a {msg['itemID']} with bid: {msg['money']}$")
    msg['item'] =  msg['itemID']
    return msg

REACTIONS = {}
CAPABILITIES = {"Give": give_m}



if __name__ == "__main__":
    logger.info("Starting Seller...")

    role = role_capable_of(capabilities=CAPABILITIES, protocol=buy)
    systems = create_systems_for_protocol(buy)
    adapter = Adapter(role, systems=systems, agents=agents)
    setup_adapter(reactions=REACTIONS, adapter=adapter, protocol=buy, role=role)
    adapter.enabled(buy.messages["Give"])(give_m)


    adapter.start()
