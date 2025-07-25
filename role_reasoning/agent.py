import logging
import random
import asyncio
from bspl.adapter import Adapter
import bspl
from bspl.protocol import Message, Protocol, Role

buy = bspl.load_file("buy.bspl").export("Buy")
from Buy import Buyer, Seller

agents = {
    "Seller": [("127.0.0.1", 8004)],
    "Buyer": [("127.0.0.1", 8005)]
}

systems = {
    "buy": {
        "protocol": buy,
        "roles": {
            Buyer: "Buyer",
            Seller: "Seller"
        }
    }
}

# Maybe also seperate message functions and generator functions?



##### Simple Agent that reasons if he can do a role in a protocol
roles = buy.roles

##### Simplest form simply check if we know message name. Assume everyone means the same thing when refering to a message of same name

##### Capabilities are then just the message names and the corresponding functions
def pay_function(pay_message, buyID, itemID, money) -> Message:
    return pay_message(
        buyID=buyID,
        itemID=itemID,
        money=money
    )

def give_function(give_message, buyID, itemID, money, item):
    return give_message(
        buyID=buyID,
        itemID=itemID,
        money=money,
        item=item
    )

def standard_reaction(message: Message):
    print(message)


Capabilities = {"Pay":pay_function}

capabilities_for_role = {}
for rname, role in roles.items():
    capabilities_for_role[rname] = []
    messages = role.messages()
    for mname, message in messages.items():
        if message.sender == role:
            capabilities_for_role[rname].append(message)           

Capable_Roles = []
for rolename, needed_capabilities in capabilities_for_role.items():
    if all([a.name in Capabilities for a in needed_capabilities]):
        Capable_Roles.append(rolename)

adapter = Adapter(Capable_Roles[0], systems, agents)

buyer_messages = buy.roles[Capable_Roles[0]].messages()

for mname, message in buyer_messages.items():
    if mname in Capabilities:
        pass
