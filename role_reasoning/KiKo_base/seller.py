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

def give_message(msg: Message, priorMsg: Message, item):
    return msg(
        item=priorMsg['itemID'],
        **priorMsg.payload
    )


def pay_reaction(pay_reaction_message: Message):
    async def packed_generic(msg: Message):
        logger.info(f"Received buy order {msg['buyID']} for a {msg['itemID']} with bid: {msg['money']}$")
        response = give_message(pay_reaction_message, msg, msg["itemID"])

        await adapter.send(response)
        return msg
    return packed_generic



def setup_reactions(protocol: Protocol, reactions, reaction_mappings):
    fitted_reactions = {}

    for inc, out in reaction_mappings.items():
        correct_function = reactions[inc](protocol.messages[out])
        fitted_reactions[inc] = correct_function


    return fitted_reactions
    
CAPABILITIES = {"Give": give_message}
REACTIONS = {"Pay" : pay_reaction}
REACTION_MAPPINGS = {"Pay": "Give"}



if __name__ == "__main__":
    logger.info("Starting Seller...")

    role = role_capable_of(capabilities=CAPABILITIES, protocol=buy)
    systems = create_systems_for_protocol(buy)
    adapter = Adapter(role, systems=systems, agents=agents)
    reactions_for_adapter = setup_reactions(protocol=buy, reactions=REACTIONS, reaction_mappings=REACTION_MAPPINGS)
    setup_adapter(reactions=reactions_for_adapter, adapter=adapter, protocol=buy, role=role)

    adapter.start()
