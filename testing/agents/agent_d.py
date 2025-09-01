import configuration
import asyncio
from bspl.adapter import Adapter





NAME = "AgentC"
SELF = [("127.0.0.1", 8003)]


adapter = Adapter(name="AgentC", systems={}, agents={NAME: SELF}, debug=True)

@adapter.reaction(configuration.protocol.messages["TellItem"])
async def messageHandler(msg):
    print(f"Received message: {msg}")
    await adapter.send(
        configuration.protocol.messages["TellPrice"](
            id=msg['id'],
            item=msg['item'],
            price=100,
        )
    )
    return msg