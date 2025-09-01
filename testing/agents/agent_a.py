import configuration
import asyncio
from bspl.adapter import Adapter, MetaAdapter
# from MetaAdapter import MetaAdapter
from bspl.adapter.message import Message


NAME = "AgentA"
SELF = [("127.0.0.1", 8001)]


adapter = MetaAdapter(name="AgentA", systems={}, agents={NAME: SELF}, debug=True)

@adapter.reaction("Protocol/TellPrice")
async def receivePrice(msg):
    print(f"[AgentA] Received price message: id {msg['id']} - item {msg['item']} - price {msg['price']}")
    return msg


@adapter.reaction("RoleNegotiation/Accept")
async def role_accepted_handler(msg):
    print(f"[AgentA] Role proposal accepted: {msg}")
    candidate = msg.meta['system'].split("::")[-1]
    proposed_system = msg['systemName']
    system = adapter.proposed_systems.get_system(proposed_system)
    system.roles[msg['proposedRole']] = candidate

    if system.is_well_formed():
        print(f"[AgentA] System {proposed_system} is well-formed with roles {system.roles}, sharing details")
        adapter.add_system(proposed_system, system.to_dict())
        await adapter.share_system_details(proposed_system)


    return msg