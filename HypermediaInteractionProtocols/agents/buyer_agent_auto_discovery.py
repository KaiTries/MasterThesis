"""
Buyer Agent with Automatic Workspace Discovery

This is the simplest version - workspace discovery happens automatically!

The agent only needs:
- Base URL
- Goal artifact URI
- Capabilities

Everything else (workspace discovery, joining, protocol/agent discovery)
is handled automatically by HypermediaMetaAdapter.
"""

from HypermediaMetaAdapter import HypermediaMetaAdapter
import asyncio
import time


# =================================================================
# Configuration
# =================================================================
NAME = "BuyerAgent"
BASE_URL = 'http://localhost:8080/'
GOAL_ITEM = 'http://localhost:8080/workspaces/bazaar/artifacts/rug#artifact'
ADAPTER_PORT = 8011


# =================================================================
# Create adapter with AUTOMATIC workspace discovery
# =================================================================
try:
    adapter = HypermediaMetaAdapter(
        name=NAME,
        base_uri=BASE_URL,                    # Start here
        goal_artifact_uri=GOAL_ITEM,          # Find this
        web_id=f'http://localhost:{ADAPTER_PORT}',
        adapter_endpoint=str(ADAPTER_PORT),
        capabilities={"Pay"},
        debug=False,
        auto_discover_workspace=True,          # ← Automatic discovery!
        auto_join=True                         # ← Automatic join!
    )
    # At this point, workspace is already discovered and joined!
    print(f"✓ Workspace discovered and joined: {adapter.workspace_uri}")
except ValueError as e:
    print(f"✗ Failed to discover workspace: {e}")
    print("\nMake sure the Yggdrasil environment is running:")
    print("  cd HypermediaInteractionProtocols")
    print("  ./start.sh")
    exit(1)
except Exception as e:
    print(f"✗ Unexpected error: {e}")
    print("\nMake sure the Yggdrasil environment is running:")
    print("  cd HypermediaInteractionProtocols")
    print("  ./start.sh")
    exit(1)


# =================================================================
# Capabilities
# =================================================================
@adapter.reaction("Give")
async def give_reaction(msg):
    adapter.info(f"✓ Received item: {msg['item']} for ${msg['money']}")
    return msg


# =================================================================
# Helper
# =================================================================
def generate_buy_params(system_id: str, item_name: str, money: int) -> dict:
    return {
        "system": system_id,
        "itemID": item_name,
        "buyID": str(int(time.time())),
        "money": money
    }


# =================================================================
# Main - Very Simple!
# =================================================================
async def main():
    """
    Simple workflow - workspace already discovered and joined!
    """
    adapter.info("🚀 Buyer agent started (workspace auto-discovered)")
    adapter.start_in_loop()

    # Discover protocol
    protocol = adapter.discover_protocol_for_goal(GOAL_ITEM)
    if not protocol:
        adapter.leave_workspace()
        return

    await asyncio.sleep(2)

    # High-level workflow
    system_name = await adapter.discover_and_propose_system(
        protocol_name=protocol.name,
        system_name="BuySystem",
        my_role="Buyer",
        goal_item_uri=None  # Already have protocol
    )

    if not system_name:
        adapter.leave_workspace()
        return

    # Wait for system
    if await adapter.wait_for_system_formation(system_name, timeout=10.0):
        await asyncio.sleep(2)

        # Execute purchases
        adapter.info("💰 Making purchases...")
        await adapter.initiate_protocol(
            "Buy/Pay",
            generate_buy_params(system_name, "rug", 10)
        )

        await asyncio.sleep(2)

        await adapter.initiate_protocol(
            "Buy/Pay",
            generate_buy_params(system_name, "rug", 20)
        )

        await asyncio.sleep(3)

    # Clean up
    adapter.leave_workspace()
    adapter.info("✓ Agent completed successfully")


if __name__ == "__main__":
    asyncio.run(main())
