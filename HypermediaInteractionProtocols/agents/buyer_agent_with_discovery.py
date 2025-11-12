"""
Buyer Agent with Workspace Discovery

This agent demonstrates true hypermedia-driven discovery:
1. Starts with only a base URL (e.g., http://localhost:8080/)
2. Crawls through workspaces to find the one containing the goal artifact
3. Joins the discovered workspace
4. Discovers protocol and agents
5. Negotiates roles and completes transaction

This is the most autonomous version - the agent only needs:
- Base URL of the environment
- URI of the goal artifact
- Its own capabilities

Everything else is discovered through hypermedia traversal!
"""

from HypermediaMetaAdapter import HypermediaMetaAdapter
import asyncio
import time


# =================================================================
# Configuration
# =================================================================
NAME = "BuyerAgent"
BASE_URL = 'http://localhost:8080/'  # Only the base URL!
GOAL_ITEM_CLASS = 'http://example.org/Rug'  # Only knows the semantic class!
ADAPTER_PORT = 8011

# Create adapter with workspace discovery
# Note: workspace_uri is NOT provided - will be discovered by class!
adapter = HypermediaMetaAdapter(
    name=NAME,
    base_uri=BASE_URL,  # Start here
    goal_artifact_class=GOAL_ITEM_CLASS,  # Find any artifact of this class
    web_id=f'http://localhost:{ADAPTER_PORT}',
    adapter_endpoint=str(ADAPTER_PORT),
    capabilities={"Pay"},
    debug=False,
    auto_join=False,  # Don't join yet - need to discover workspace first
    auto_discover_workspace=False  # Manual discovery for demonstration
)


# =================================================================
# Capabilities - Define message handlers
# =================================================================
@adapter.reaction("Give")
async def give_reaction(msg):
    """Handle Give messages - the item delivery."""
    adapter.info(f"✓ Buy order {msg['buyID']} for item {msg['item']} (${msg['money']}) successful!")
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
# Main Agent Logic - Demonstrates Workspace Discovery
# =================================================================
async def main():
    """
    Main buyer agent workflow with class-based workspace discovery:

    1. Discover workspace by artifact class (crawl from base URL)
    2. Join discovered workspace
    3. Discover protocol from discovered artifact
    4. Discover agents and propose system
    5. Wait for system formation
    6. Initiate buy transactions
    7. Clean up and leave workspace
    """
    adapter.info("=" * 60)
    adapter.info("BUYER AGENT STARTING - CLASS-BASED DISCOVERY MODE")
    adapter.info("=" * 60)
    adapter.info(f"Base URL: {BASE_URL}")
    adapter.info(f"Goal Item Class: {GOAL_ITEM_CLASS}")
    adapter.info("")

    # Start the adapter
    adapter.start_in_loop()

    # ========================================
    # STEP 1: Discover Workspace by Artifact Class
    # ========================================
    adapter.info("STEP 1: Discovering workspace through semantic class search...")
    discovered_workspace, discovered_artifact = adapter.discover_workspace_by_class(
        BASE_URL, GOAL_ITEM_CLASS
    )

    if not discovered_workspace:
        adapter.logger.error(f"✗ Could not discover workspace for artifact class: {GOAL_ITEM_CLASS}")
        return

    adapter.info(f"✓ Discovered workspace: {discovered_workspace}")
    adapter.info(f"✓ Discovered artifact: {discovered_artifact}")
    adapter.workspace_uri = discovered_workspace
    adapter.goal_artifact_uri = discovered_artifact
    adapter.info("")

    # ========================================
    # STEP 2: Join Discovered Workspace
    # ========================================
    adapter.info("STEP 2: Joining discovered workspace...")
    success, artifact_address = adapter.join_workspace()
    if not success:
        adapter.logger.error("✗ Failed to join workspace")
        return

    adapter.info(f"✓ Joined workspace at: {artifact_address}")
    adapter.info("")

    # ========================================
    # STEP 3: Discover Protocol
    # ========================================
    adapter.info("STEP 3: Discovering protocol from discovered artifact...")
    protocol = adapter.discover_protocol_for_goal(adapter.goal_artifact_uri)
    if not protocol:
        adapter.logger.error("✗ Could not discover protocol for discovered artifact")
        adapter.leave_workspace()
        return

    adapter.info(f"✓ Discovered protocol: {protocol.name}")
    adapter.info("")

    # Wait for other agents to be ready
    await asyncio.sleep(2)

    # ========================================
    # STEP 4: Discover Agents & Propose System
    # ========================================
    adapter.info("STEP 4: Discovering agents and proposing system...")

    # Discover agents
    agents = adapter.discover_agents()
    adapter.info(f"✓ Discovered {len(agents)} agent(s)")

    # Propose system with discovered protocol
    system_dict = {
        "protocol": protocol,
        "roles": {
            "Buyer": NAME,
            "Seller": None  # To be negotiated
        }
    }
    proposed_system_name = adapter.propose_system("BuySystem", system_dict)
    adapter.info(f"✓ Proposed system: {proposed_system_name}")

    # Offer roles to discovered agents
    await adapter.offer_roles(system_dict, proposed_system_name, agents)
    adapter.info("✓ Offered roles to discovered agents")
    adapter.info("")

    # ========================================
    # STEP 5: Wait for System Formation
    # ========================================
    adapter.info("STEP 5: Waiting for system formation...")
    system_ready = await adapter.wait_for_system_formation(
        proposed_system_name,
        timeout=10.0
    )

    if not system_ready:
        adapter.info("✗ System not well-formed, cannot initiate protocol")
        adapter.leave_workspace()
        return

    adapter.info("✓ System is well-formed and ready!")
    adapter.info("")

    # Give system details time to propagate
    await asyncio.sleep(2)

    # ========================================
    # STEP 6: Execute Buy Transactions
    # ========================================
    adapter.info("STEP 6: Initiating buy transactions...")

    # First purchase
    adapter.info("→ Initiating purchase #1 (10$)...")
    await adapter.initiate_protocol(
        "Buy/Pay",
        generate_buy_params(proposed_system_name, "rug", 10)
    )

    await asyncio.sleep(2)

    # Second purchase
    adapter.info("→ Initiating purchase #2 (20$)...")
    await adapter.initiate_protocol(
        "Buy/Pay",
        generate_buy_params(proposed_system_name, "rug", 20)
    )

    adapter.info("")
    await asyncio.sleep(3)

    # ========================================
    # STEP 7: Clean Up
    # ========================================
    adapter.info("STEP 7: Cleaning up...")
    success = adapter.leave_workspace()
    adapter.info(f"✓ Left workspace: {success}")

    adapter.info("")
    adapter.info("=" * 60)
    adapter.info("BUYER AGENT COMPLETED SUCCESSFULLY")
    adapter.info("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        adapter.info("Agent interrupted by user")
        if adapter._joined:
            adapter.leave_workspace()
    except ConnectionRefusedError:
        print("\n✗ Connection refused. Make sure the Yggdrasil environment is running:")
        print("  cd HypermediaInteractionProtocols")
        print("  ./start.sh")
    except Exception as e:
        print(f"\n✗ Agent error: {e}")
        print("\nMake sure the Yggdrasil environment is running:")
        print("  cd HypermediaInteractionProtocols")
        print("  ./start.sh")
        if adapter._joined:
            adapter.leave_workspace()
