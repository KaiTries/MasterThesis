import configuration
import asyncio
from bspl.adapter import Adapter, MetaAdapter
#from MetaAdapter import MetaAdapter





NAME = "AgentC"
SELF = [("127.0.0.1", 8003)]


adapter = MetaAdapter(name="AgentC", systems={}, agents={NAME: SELF})

@adapter.reaction("Protocol/TellItem")
async def messageHandler(msg):
    print(f"[AgentC] Received item message: {msg['id']} - item {msg['item']}")
    await adapter.send(
        configuration.protocol.messages["TellPrice"](
            id=msg['id'],
            item=msg['item'],
            price=100,
        )
    )
    return msg

@adapter.reaction("RoleNegotiation/OfferRole")
async def role_proposed_handler(msg):
    proposed_protocol = msg['protocolName']
    proposed_system_name = msg['systemName']
    proposed_role = msg['proposedRole']
    if proposed_protocol in msg.adapter.protocols:
        print(f"[AgentC] Accepting role proposal: {msg}")
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
        print(f"[AgentC] Rejecting role proposal: {msg}")
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
async def system_details_handler(msg):
    print(f"[AgentC] Received system details: {msg}")
    system = msg['enactmentSpecs']
    system['protocol'] = adapter.protocols[msg['protocolName']]
    adapter.add_system(msg['systemName'],system)

    return msg