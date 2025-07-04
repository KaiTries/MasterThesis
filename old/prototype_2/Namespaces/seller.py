"""
This agent initiates the logistics protocol by generating orders and handling packed responses.
"""

import logging
import random
import asyncio
from bspl.adapter import Adapter
from configuration import systems, agents
import Buy
from Negotiate import Rfq, Quote, Reject, Pay, Give

adapter = Adapter("Seller", systems, agents)

logger = logging.getLogger("seller")
logger.setLevel(logging.DEBUG)





@adapter.reaction(Rfq)
async def givePrice(msg):
    logger.info(f"Received request for quote for item {msg['itemID']} ID {msg['buyID']}")
    await adapter.send(
        Quote(
            price=10,
            **msg.payload
        )
    )
    return msg


@adapter.reaction(Pay)
async def giveItem(msg):
    logger.info(f"Bazaar - Selling {msg['itemID']} for {msg['money']}")
    await adapter.send(
        Give(
            item=msg['itemID'],
            buyID=msg['buyID'],
            itemID=msg['itemID'],
            money=msg['money']
        )
    )



@adapter.reaction(Buy.Pay)
async def packed(msg):
    """Handles packed items by logging their status."""
    logger.info(f"Received buy order {msg['buyID']} for a {msg['itemID']} with bid: {msg['money']}$")
    await adapter.send(Buy.Give(
        buyID=msg['buyID'],
        itemID=msg['itemID'],
        money=msg['money'],
        item=msg['itemID']
    ))
    return msg

if __name__ == "__main__":
    logger.info("Starting Seller...")
    adapter.start()
