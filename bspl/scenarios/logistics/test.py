#!/usr/bin/env python3
import asyncio
import logging
import random

# Use your real config & agents
from configuration import systems as BASE_SYSTEMS, agents as BASE_AGENTS, logistics as LOGISTICS
from Logistics import RequestLabel, RequestWrapping, Packed, Wrapped, Merchant, Wrapper, Labeler, Packer

# Import your existing agent modules (they define module-level `adapter` and reactions)
import merchant
import wrapper
import labeler
import packer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
log = logging.getLogger("demo")

async def send_order(sysname, n):
        item = random.choice(["ball", "bat", "plate", "glass"])
        await merchant.adapter.send(
            RequestLabel(system=sysname, orderID=n, address=f"{sysname}-{n}")
        )
        await merchant.adapter.send(
            RequestWrapping(system=sysname, orderID=n, itemID = 21, item=item)
        )


async def timeline():
    # Start all adapters *in the same loop* (non-owning)
    merchant.adapter.start_in_loop()
    wrapper.adapter.start_in_loop()
    labeler.adapter.start_in_loop()
    packer.adapter.start_in_loop()

    # Let baseline run briefly
    await asyncio.sleep(1.0)

    # 1) Dynamically add a new Wrapper agent and reassign role
    from bspl.adapter import Adapter  # your Adapter
    systems = {k: dict(v) for k, v in BASE_SYSTEMS.items()}
    agents = {k: list(v) for k, v in BASE_AGENTS.items()}

    alt_eps = [("127.0.0.1", 8004)]
    alt = Adapter("AltWrapper", systems, {**agents, "AltWrapper": alt_eps})

    
    adapters = (merchant.adapter, wrapper.adapter, labeler.adapter, packer.adapter, alt)


    @alt.reaction(RequestWrapping)
    async def wrap_alt(msg):
        wrapping = "bubblewrap" if msg["item"] in ["plate", "glass"] else "paper"
        log.info(f"AltWrapper: Order {msg['orderID']} item {msg['itemID']} ({msg['item']}) wrapped with {wrapping}")
        await alt.send(Wrapped(wrapping=wrapping, **msg.payload))
        return msg

    alt.start_in_loop()

    # await packer.adapter.reload_protocol('logistics', LOGISTICS)

    log.info("Reassigned Wrapper -> AltWrapper at runtime")
    await asyncio.sleep(0.6)

    await send_order("logistics",  10)
    await asyncio.sleep(5)


    log.info("✅ Demo complete")

if __name__ == "__main__":
    asyncio.run(timeline())