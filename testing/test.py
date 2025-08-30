#!/usr/bin/env python3
import asyncio
import logging
import random

# Use your real config & agents
from configuration import systems as BASE_SYSTEMS, agents as BASE_AGENTS, logistics as LOGISTICS
from Logistics import RequestLabel, RequestWrapping, Packed, Wrapped

# Import your existing agent modules (they define module-level `adapter` and reactions)
import merchant
import wrapper
import labeler
import packer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
log = logging.getLogger("demo")

async def timeline():
    # Start all adapters *in the same loop* (non-owning)
    merchant.adapter.start_in_loop(merchant.order_generator())
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

    @alt.reaction(RequestWrapping)
    async def wrap_alt(msg):
        wrapping = "bubblewrap" if msg["item"] in ["plate", "glass"] else "paper"
        await alt.send(Wrapped(system=msg.system, wrapping=wrapping, **msg.payload))
        return msg

    alt.start_in_loop()

    # Update topology in *all* adapters
    for ad in (merchant.adapter, wrapper.adapter, labeler.adapter, packer.adapter, alt):
        await ad.upsert_agent("AltWrapper", alt_eps)
        await ad.reassign_role("logistics", LOGISTICS.Wrapper, "AltWrapper")

    log.info("Reassigned Wrapper -> AltWrapper at runtime")
    await asyncio.sleep(0.6)

    # 2) Add a new system logistics2 on the fly
    systems["logistics2"] = {
        "protocol": LOGISTICS,
        "roles": {
            LOGISTICS.Merchant: "Merchant",
            LOGISTICS.Wrapper:  "AltWrapper",
            LOGISTICS.Labeler:  "Labeler",
            LOGISTICS.Packer:   "Packer",
        },
    }
    for ad in (merchant.adapter, wrapper.adapter, labeler.adapter, packer.adapter, alt):
        await ad.add_system("logistics2", systems["logistics2"])

    # Send traffic into both systems
    async def send_order(sysname, n):
        item = random.choice(["ball", "bat", "plate", "glass"])
        await merchant.adapter.send(
            RequestLabel(system=sysname, orderID=n, address=f"{sysname}-{n}"),
            RequestWrapping(system=sysname, orderID=n, itemID=n*10, item=item),
        )
    await send_order("logistics",  9001)
    await send_order("logistics2", 9002)
    await asyncio.sleep(0.8)

    # 3) Update Merchant endpoints (listener rebind) across all adapters
    new_eps = [("127.0.0.1", 8100)]
    for ad in (merchant.adapter, wrapper.adapter, labeler.adapter, packer.adapter, alt):
        await ad.upsert_agent("Merchant", new_eps)
    log.info("Merchant re-bound to %s", new_eps)

    await send_order("logistics",  9003)
    await send_order("logistics2", 9004)
    await asyncio.sleep(0.8)

    # 4) Remove logistics2
    for ad in (merchant.adapter, wrapper.adapter, labeler.adapter, packer.adapter, alt):
        await ad.remove_system("logistics2")
    log.info("Removed system 'logistics2' at runtime")

    # (Optional) try to send to removed system to see behavior
    try:
        await send_order("logistics2", 9999)
    except Exception as e:
        log.info("Expected failure after removal: %r", e)

    log.info("✅ Demo complete")

if __name__ == "__main__":
    asyncio.run(timeline())