"""
This agent initiates the logistics protocol by generating orders and handling packed responses.
"""

import logging
import random
import asyncio
from bspl.adapter import Adapter
from configuration import systems, agents
from Buy import Pay, Give

adapter = Adapter("Buyer", systems, agents)

logger = logging.getLogger("buyer")
# logger.setLevel(logging.DEBUG)

async def order_generator():
    """Generates sample orders with random items and addresses."""
    for orderID in range(2):
        await adapter.send(
            Pay(
                buyID=orderID,
                itemID=random.choice(["rug","tea"]),
                money=random.choice([10, 29]),
            )
        )
        await asyncio.sleep(0)

@adapter.reaction(Give)
async def packed(msg):
    """Handles packed items by logging their status."""
    logger.info(f"Buy order {msg['buyID']} for item {msg['item']} with amount: {msg['money']}$ successful")
    return msg

if __name__ == "__main__":
    logger.info("Starting Buyer...")
    adapter.start(order_generator())
