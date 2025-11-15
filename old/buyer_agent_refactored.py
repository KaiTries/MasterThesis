"""
Refactored Buyer Agent using HypermediaMetaAdapter.

This demonstrates the simplified agent implementation when using
HypermediaMetaAdapter instead of manually coordinating MetaAdapter + HypermediaTools.

Compare this with buyer_agent.py to see the improvements:
- No manual workspace join/leave calls
- No manual agent discovery and address book management
- No manual Thing Description generation
- Cleaner, more declarative code
- Built-in context manager support
"""

from HypermediaMetaAdapter import HypermediaMetaAdapter
import asyncio
import time


# =================================================================
# Configuration
# =================================================================
NAME = "BuyerAgent"
WORKSPACE_URI = 'http://localhost:8080/workspaces/bazaar/'
GOAL_ITEM = 'http://localhost:8080/workspaces/bazaar/artifacts/rug#artifact'
ADAPTER_PORT = 8011

# Create adapter with hypermedia capabilities
adapter = HypermediaMetaAdapter(
    name=NAME,
    workspace_uri=WORKSPACE_URI,
    web_id=f'http://localhost:{ADAPTER_PORT}',
    adapter_endpoint=str(ADAPTER_PORT),
    capabilities={"Pay"},  # This agent can send Pay messages
    debug=False,
    auto_join=True  # Automatically join workspace
)


# =================================================================
# Capabilities - Define message handlers
# =================================================================
@adapter.reaction("Give")
async def give_reaction(msg):
    """Handle Give messages - the item delivery."""
    adapter.info(f"Buy order {msg['buyID']} for item {msg['item']} with amount: {msg['money']}$ successful")
    return msg


# =================================================================
# Helper Functions
# =================================================================
def generate_buy_params(system_id: str, item_name: str, money: int) -> dict:
    """
    Generate parameters for initiating the Buy protocol.

    Args:
        system_id: System identifier
        item_name: Item to purchase
        money: Amount to pay

    Returns:
        Parameter dictionary for Buy/Pay message
    """
    return {
        "system": system_id,
        "itemID": item_name,
        "buyID": str(int(time.time())),
        "money": money
    }


# =================================================================
# Main Agent Logic
# =================================================================
async def main():
    """
    Main buyer agent workflow:
    1. Start adapter
    2. Discover protocol from goal item
    3. Discover agents and propose system
    4. Wait for system formation
    5. Initiate buy transactions
    6. Clean up and leave workspace
    """
    # Start the adapter
    adapter.start_in_loop()

    # Discover protocol from goal item (using semantic reasoning)
    protocol = adapter.discover_protocol_for_goal(GOAL_ITEM)
    if not protocol:
        adapter.logger.error(f"Could not discover protocol for goal item {GOAL_ITEM}")
        adapter.leave_workspace()
        return

    # Wait a moment for other agents to be ready
    await asyncio.sleep(2)

    # Discover and propose system (all-in-one operation)
    proposed_system_name = await adapter.discover_and_propose_system(
        protocol_name=protocol.name,  # Not used since we have protocol already
        system_name="BuySystem",
        my_role="Buyer",  # We take the Buyer role
        goal_item_uri=None  # We already discovered the protocol
    )

    if not proposed_system_name:
        adapter.logger.error("Failed to propose system")
        adapter.leave_workspace()
        return

    # Wait for system to become well-formed (all roles filled)
    system_ready = await adapter.wait_for_system_formation(
        proposed_system_name,
        timeout=10.0
    )

    if not system_ready:
        adapter.info("System not well-formed, cannot initiate protocol")
        adapter.leave_workspace()
        return

    # Give a moment for system details to propagate
    await asyncio.sleep(2)

    # Initiate the Buy protocol (make purchases)
    adapter.info("System ready, initiating buy transactions...")

    # First purchase
    await adapter.initiate_protocol(
        "Buy/Pay",
        generate_buy_params(proposed_system_name, "rug", 10)
    )

    await asyncio.sleep(2)

    # Second purchase
    await adapter.initiate_protocol(
        "Buy/Pay",
        generate_buy_params(proposed_system_name, "rug", 20)
    )

    await asyncio.sleep(3)

    # Clean up - leave workspace
    success = adapter.leave_workspace()
    adapter.info(f"Left workspace: {success}")


if __name__ == "__main__":
    asyncio.run(main())
