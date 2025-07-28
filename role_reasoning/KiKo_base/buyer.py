"""
This agent initiates the logistics protocol by generating orders and handling packed responses.
"""

import logging
import bspl
from bspl.adapter import Adapter
from bspl.protocol import Message, Protocol


buy = bspl.load_file("buy.bspl").export("Buy")


agents = {
    "Seller": [("127.0.0.1", 8004)],
    "Buyer": [("127.0.0.1", 8005)]
}


def create_systems_for_protocol(protocol: Protocol):
    return {
        protocol.name.lower() : {
            "protocol" : protocol,
            "roles" : {
                protocol.roles[role] : role for role in protocol.roles
            }
        }
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

# Return first role that agent is capable of
def role_capable_of(protocol: Protocol):
    roles = protocol.roles
    capabilities_for_role = {}
    for rname, role in roles.items():
        capabilities_for_role[rname] = []
        messages = role.messages()
        for mname, message in messages.items():
            if message.sender == role:
                capabilities_for_role[rname].append(message)           

    for rolename, needed_capabilities in capabilities_for_role.items():
        if all([a.name in CAPABILITIES for a in needed_capabilities]):
            return rolename


def setup_adapter(adapter: Adapter, protocol: Protocol, role):
    messages = protocol.roles[role].messages()
    for mname, message in messages.items():
        if mname in REACTIONS:
             adapter.reaction(message)(REACTIONS[mname])
 


if __name__ == "__main__":
    logger.info("Starting Buyer...")
    # find protocol
    # reason which role
    role = role_capable_of(buy)
    systems = create_systems_for_protocol(buy)
    adapter = Adapter(role, systems, agents)
    # setup role
    setup_adapter(adapter, buy, role)
    # start adapter
    # try to buy something if we are buyer
    if role == "Buyer":
        initial_message = buy.roles[role].messages()["Pay"]
        adapter.start(adapter.send(pay_message(initial_message,1,"item",1)))