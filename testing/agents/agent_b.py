import configuration
import asyncio
from bspl.adapter import Adapter, MetaAdapter
from bspl.adapter.message import Message
# from MetaAdapter import MetaAdapter

NAME = "AgentB"
SELF = [("127.0.0.1", 8002)]


adapter = MetaAdapter(name="AgentB", systems={}, agents={NAME:SELF}, debug=True)

@adapter.reaction("Protocol/GiveItem")
async def messageHandler(msg):
    print(f"[AgentB] Received item message: id {msg['id']} item {msg['item']}")
    await adapter.send(
        configuration.protocol.messages["TellItem"](
            id=msg['id'],
            item=msg['item'],
        )
    )
    return msg

@adapter.reaction("RoleNegotiation/OfferRole")
async def role_proposed_handler(msg: Message):
    proposed_protocol = msg['protocolName']
    proposed_system_name = msg['systemName']
    proposed_role = msg['proposedRole']
    if proposed_protocol in msg.adapter.protocols:
        print(f"[AgentB] Accepting role proposal: {msg}")
        await adapter.send(
            configuration.role_negotiation.messages["Accept"](
                system=msg.system,
                protocolName=msg['protocolName'],
                systemName=msg['systemName'],
                proposedRole=msg['proposedRole'],
                accept=True,
            )
        )
    else:
        print(f"[AgentB] Rejecting role proposal: {msg}")
        await adapter.send(
            configuration.role_negotiation.messages["Reject"](
                system=msg.system,
                protocolName=msg['protocolName'],
                systemName=msg['systemName'],
                proposedRole=msg['proposedRole'],
                reject=True,
            )
        )
    return msg

@adapter.reaction("RoleNegotiation/SystemDetails")
async def system_details_handler(msg: Message):
    print(f"[AgentB] Received system details: {msg}")
    system = msg['enactmentSpecs']
    system['protocol'] = adapter.protocols[msg['protocolName']]
    adapter.add_system(msg['systemName'],system)
    return msg