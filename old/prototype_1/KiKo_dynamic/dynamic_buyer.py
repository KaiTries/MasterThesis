"""
This agent initiates the logistics protocol by generating orders and handling packed responses.
"""

import logging
import random
import bspl
import asyncio
from bspl.adapter import Adapter

adapter = None
me = ('127.0.0.1', 8001)
logger = logging.getLogger("buyer")

# find parts of configuration dynamically
# also find protocol dynamically!

# Assume we found the protocol
def learnProtocol():
    buy_protocol = bspl.load_file("buy.bspl").export("Buy")
    return buy_protocol

def find_other_agents():
    agents = {
        "Seller": [("127.0.0.1", 8010)],
    }

    return agents




async def packed(msg):
    """Handles packed items by logging their status."""
    logger.info(f"Buy order {msg['buyID']} for item {msg['item']} with amount: {msg['money']}$ successful")
    return msg


def agent_loop():
    global adapter
    buy_protocol = learnProtocol()


    agents = find_other_agents()
    agents["Buyer"] = [me]

    systems = {
        buy_protocol.name : {
            "protocol" : buy_protocol,
            "roles" : {

            }
        }
    }

    # TODO need some logic to decide who fills which roles
    for role in buy_protocol.roles:
        systems[buy_protocol.name]["roles"][buy_protocol.roles[role]] = role

    
    
    adapter = Adapter("Buyer", systems, agents)
    adapter.reaction(buy_protocol.module.Give)(packed)
    adapter.start(order_generator(buy_protocol))





async def order_generator(buy_protocol):
    """Generates sample orders with random items and addresses."""
    await adapter.send(
            buy_protocol.module.Pay(
                buyID=1,
                itemID=random.choice(["rug","tea"]),
                money=random.choice([10, 29]),
            )
        )
    logger.info("sent pay message")
    await asyncio.sleep(0)




if __name__ == "__main__":
    logger.info("Starting Buyer...")
    agent_loop()
