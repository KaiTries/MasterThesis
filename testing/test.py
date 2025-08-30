#!/usr/bin/env python3
"""
Dynamic BSPL Adapter demo that matches your project's usage:
- Imports systems/agents from configuration.py
- Uses the same Logistics protocol and message types
- Shows reassign_role, add_system, upsert_agent, reload_protocol, remove_system
Run:
    python demo_dynamic_runtime.py
"""

import asyncio
import logging
import random
from typing import Dict, Tuple

# --- your project imports (as in wrapper.py / merchant.py / labeler.py / packer.py)
from bspl.adapter import Adapter
from configuration import systems as BASE_SYSTEMS, agents as BASE_AGENTS, logistics as LOGISTICS  # logistics is the module returned by bspl.load_file(...).export("Logistics")
from Logistics import RequestLabel, RequestWrapping, Labeled, Wrapped, Packed

Address = Tuple[str, int]
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
log = logging.getLogger("demo")

# ----------- Inline "agent" behaviors (copy of your modules, but embedded) -----------

def make_merchant_adapter(systems: Dict, agents: Dict) -> Adapter:
    adapter = Adapter("Merchant", systems, agents)
    mlog = logging.getLogger("Merchant")

    async def order_generator():
        order_id = 1
        while True:
            # send both requests required to eventually enable Packed
            item_id = random.randint(100, 999)
            item = random.choice(["ball", "bat", "plate", "glass"])
            address = f"C-{order_id:04d}"

            mlog.info(f"[logistics] placing order {order_id} item {item_id} ({item}) for {address}")
            await adapter.send(
                RequestLabel(system="logistics", orderID=order_id, address=address),
                RequestWrapping(system="logistics", orderID=order_id, itemID=item_id, item=item),
            )
            await asyncio.sleep(0.05)
            order_id += 1
            if order_id > 3:  # keep baseline short
                break

    @adapter.reaction(Packed)
    async def on_packed(msg):
        mlog.info(f"[{msg.system}] received Packed: order {msg['orderID']} item {msg['itemID']} status={msg['status']}")
        return msg

    # start with a short burst of orders
    adapter.start(order_generator())
    return adapter


def make_wrapper_adapter(name: str, systems: Dict, agents: Dict) -> Adapter:
    adapter = Adapter(name, systems, agents)
    wlog = logging.getLogger(name)

    @adapter.reaction(RequestWrapping)
    async def wrap(msg):
        wrapping = "bubblewrap" if msg["item"] in ["plate", "glass"] else "paper"
        wlog.info(f"[{msg.system}] wrap: order {msg['orderID']} item {msg['itemID']} ({msg['item']}) -> {wrapping}")
        await adapter.send(Wrapped(system=msg.system, wrapping=wrapping, **msg.payload))
        return msg

    adapter.start()
    return adapter


def make_labeler_adapter(systems: Dict, agents: Dict) -> Adapter:
    import uuid
    adapter = Adapter("Labeler", systems, agents)
    llog = logging.getLogger("Labeler")

    @adapter.reaction(RequestLabel)
    async def label(msg):
        label = str(uuid.uuid4())
        llog.info(f"[{msg.system}] label: order {msg['orderID']} -> {label[:8]}…")
        await adapter.send(Labeled(system=msg.system, label=label, **msg.payload))
        return msg

    adapter.start()
    return adapter


def make_packer_adapter(systems: Dict, agents: Dict) -> Adapter:
    adapter = Adapter("Packer", systems, agents)
    plog = logging.getLogger("Packer")

    # In your project you used @adapter.enabled(Packed). We keep that here so
    # Packed becomes enabled once both Wrapped and Labeled have arrived.
    @adapter.enabled(Packed)
    async def pack(msg):
        msg["status"] = "packed"
        plog.info(f"[{msg.system}] pack: order {msg['orderID']} item {msg['itemID']} "
                  f"wrapping={msg['wrapping']} label={msg['label']}")
        return msg

    adapter.start()
    return adapter

# --------------------- Demo flow (dynamic changes) ---------------------

async def demo_flow():
    # Make local copies so we can mutate systems/agents safely for the demo
    systems = {k: dict(v) for k, v in BASE_SYSTEMS.items()}
    agents = {k: list(v) for k, v in BASE_AGENTS.items()}

    log.info("=== Starting baseline adapters on system 'logistics' ===")

    merchant = make_merchant_adapter(systems, agents)
    wrapper  = make_wrapper_adapter("Wrapper", systems, agents)
    labeler  = make_labeler_adapter(systems, agents)
    packer   = make_packer_adapter(systems, agents)

    # Let baseline run for a moment
    await asyncio.sleep(0.8)

    # 1) Reassign role Wrapper -> AltWrapper, live
    log.info("=== 1) Reassign role: Wrapper -> AltWrapper (dynamic join) ===")
    agents["AltWrapper"] = [("127.0.0.1", 8004)]
    alt_wrapper = make_wrapper_adapter("AltWrapper", systems, agents)

    # Every adapter should learn about the reassignment (directory is per adapter in many setups,
    # so we call on all four to keep them consistent)
    for ad in (merchant, wrapper, labeler, packer, alt_wrapper):
        await ad.upsert_agent("AltWrapper", agents["AltWrapper"])
        await ad.reassign_role("logistics", "Wrapper", "AltWrapper")
    log.info("Reassigned 'Wrapper' role to AltWrapper")

    # Send a couple more orders (merchant already runs a short burst; kick another burst to observe effect)
    async def more_orders():
        for i in range(4, 6):
            item_id = random.randint(100, 999)
            item = random.choice(["ball", "bat", "plate", "glass"])
            address = f"C-{i:04d}"
            await merchant.send(
                RequestLabel(system="logistics", orderID=i, address=address),
                RequestWrapping(system="logistics", orderID=i, itemID=item_id, item=item),
            )
            await asyncio.sleep(0.05)
    asyncio.create_task(more_orders())
    await asyncio.sleep(0.8)

    # 2) Add a new system at runtime
    log.info("=== 2) Add new system 'logistics2' (roles point to Merchant, AltWrapper, Labeler, Packer) ===")
    systems["logistics2"] = {
        "protocol": LOGISTICS,  # reuse same protocol module
        "roles": {
            # exact Role names from the exported module:
            LOGISTICS.Merchant: "Merchant",
            LOGISTICS.Wrapper: "AltWrapper",
            LOGISTICS.Labeler: "Labeler",
            LOGISTICS.Packer: "Packer",
        },
    }
    for ad in (merchant, wrapper, labeler, packer, alt_wrapper):
        await ad.add_system("logistics2", systems["logistics2"])

    # Send traffic to the new system
    async def system2_orders():
        for i in range(1001, 1004):
            item_id = random.randint(100, 999)
            item = random.choice(["ball", "bat", "plate", "glass"])
            address = f"S2-{i}"
            await merchant.send(
                RequestLabel(system="logistics2", orderID=i, address=address),
                RequestWrapping(system="logistics2", orderID=i, itemID=item_id, item=item),
            )
            await asyncio.sleep(0.05)
    asyncio.create_task(system2_orders())
    await asyncio.sleep(0.8)

    # 3) Update endpoints (rebind) for Merchant
    log.info("=== 3) Update Merchant endpoints (live rebind) ===")
    new_eps = [("127.0.0.1", 8100)]
    for ad in (merchant, wrapper, labeler, packer, alt_wrapper):
        await ad.upsert_agent("Merchant", new_eps)
    log.info("Merchant endpoints updated to %s", new_eps)

    # Verify a message still completes through the flow on both systems
    await merchant.send(
        RequestLabel(system="logistics",  orderID=9001, address="R-9001"),
        RequestWrapping(system="logistics",  orderID=9001, itemID=42, item="plate"),
    )
    await merchant.send(
        RequestLabel(system="logistics2", orderID=9002, address="R-9002"),
        RequestWrapping(system="logistics2", orderID=9002, itemID=43, item="bat"),
    )
    await asyncio.sleep(0.6)

    # 4) (Optional) Hot-reload protocol for 'logistics'
    log.info("=== 4) Hot-reload protocol for 'logistics' (registry rebuild) ===")
    # You can re-export a modified protocol or just pass LOGISTICS again for the demo
    for ad in (merchant, wrapper, labeler, packer, alt_wrapper):
        await ad.reload_protocol("logistics", LOGISTICS)
    await asyncio.sleep(0.3)

    # 5) Remove the extra system to show teardown
    log.info("=== 5) Remove 'logistics2' at runtime ===")
    for ad in (merchant, wrapper, labeler, packer, alt_wrapper):
        await ad.remove_system("logistics2")
    # Attempting to send to removed system should now fail or be ignored (depending on your impl)
    try:
        await merchant.send(
            RequestLabel(system="logistics2", orderID=9999, address="ghost"),
            RequestWrapping(system="logistics2", orderID=9999, itemID=1, item="bat"),
        )
    except Exception as e:
        log.info("As expected, sending to removed system failed: %r", e)

    log.info("✅ Demo complete. You just saw join/reassign/add-system/rebind/reload/remove in action.")


if __name__ == "__main__":
    asyncio.run(demo_flow())