import configuration
import asyncio
from bspl.adapter import Adapter





NAME = "AgentD"
SELF = [("127.0.0.1", 8004)]


adapter = Adapter(name=NAME, systems={}, agents={NAME: SELF})

@adapter.reaction("Protocol/TellItem")
async def messageHandler(msg):
    print(f"[AgentD] Received item message: {msg['id']} - item {msg['item']}")
    await adapter.send(
        configuration.protocol.messages["TellPrice"](
            id=msg['id'],
            item=msg['item'],
            price=100,
        )
    )
    return msg