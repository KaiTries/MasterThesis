"""
This agent initiates the logistics protocol by generating orders and handling packed responses.
"""

import logging
import random
import asyncio
from bspl.adapter import Adapter
from configuration import systems, agents
import Buy
from Negotiate import Rfq, Quote, Accept, Reject, HandOver

adapter = Adapter("Buyer", systems, agents)


logger = logging.getLogger("B")
logger.setLevel(logging.DEBUG)

async def order_generator(coin):
    """Generates sample orders with random items and addresses."""
    if coin:
        await adapter.send(Rfq(
            buyID=1,
            itemID='groceries'
        ))
    else:
        await adapter.send(
            Buy.Pay(
                buyID=1,
                itemID='groceries',
                money=15
            )
        )
    await asyncio.sleep(1)

@adapter.reaction(Buy.Give)
async def packed(msg):
    """Handles packed items by logging their status."""
    logger.info(f"Buy order {msg['buyID']} for item {msg['item']} with amount: {msg['money']}$ successful")
    return msg

@adapter.reaction(Quote)
async def decide(msg):
    logger.info(f"Received quote for item {msg['itemID']} and ID {msg['buyID']}: {msg['price']}$")
    await adapter.send(
        Accept(
            money=msg['price'],
            buyID=msg['buyID'],
            itemID=msg['itemID']
        )
    )
    return msg



@adapter.reaction(HandOver)
async def getItem(msg):
    logger.info(f"Received {msg['itemID']} from bazaar")


if __name__ == "__main__":
    logger.info("Starting Buyer...")
    coin = random.choice([True, False])

    logger.info(f"Going to the {'bazaar' if coin else 'supermarket'} to buy groceries")
    adapter.start(order_generator(coin))
