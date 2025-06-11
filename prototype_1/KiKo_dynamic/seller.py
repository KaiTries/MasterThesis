"""
This agent initiates the logistics protocol by generating orders and handling packed responses.
"""

import logging
import random
import asyncio
from bspl.adapter import Adapter
from configuration import systems, agents
from Buy import Pay, Give

adapter = Adapter("Seller", systems, agents)

logger = logging.getLogger("seller")
# logger.setLevel(logging.DEBUG)


@adapter.reaction(Pay)
async def packed(msg):
    """Handles packed items by logging their status."""
    logger.info(f"Received buy order {msg['buyID']} for a {msg['itemID']} with bid: {msg['money']}$")
    await adapter.send(Give(
        item=msg['itemID'],
        **msg.payload
    ))
    return msg

if __name__ == "__main__":
    logger.info("Starting Seller...")
    adapter.start()
