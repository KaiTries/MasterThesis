import logging
import random
import asyncio
from bspl.adapter import Adapter
import bspl


class genericMessage:
    def __init__(self,name,sender,recipient,parameters):
        self.name = name
        self.sender = sender
        self.recipient = recipient
        self.parameters = parameters

##### Simple Agent that reasons if he can do a role in a protocol
buy = bspl.load_file("buy.bspl").export("Buy")
roles = buy.roles

for role in roles:
    messages = roles[role].messages()
    for message in messages:
        print(messages[message])




# generic message function
def send_pay_message():
    pass