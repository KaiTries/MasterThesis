"""
Buyer Agent with Automatic Role Reasoning

This agent demonstrates the highest level of autonomy:
1. Class-based workspace discovery (only knows artifact type, not URI)
2. Automatic role reasoning (only knows goal, not role name)

The agent only needs to know:
- Base URL to start from
- What type of thing it wants (ex:Rug)
- What it wants to do with it (gr:Buy)
- What it can do (Pay)

Everything else is discovered and reasoned autonomously!
"""

from HypermediaMetaAdapter import HypermediaMetaAdapter
import asyncio
import time


# =================================================================
# Configuration - Only high-level goals and capabilities!
# =================================================================
NAME = "BuyerAgent"
BASE_URL = 'http://localhost:8080/'
GOAL_ITEM_CLASS = 'http://example.org/Rug'  # What I want
GOAL_TYPE = 'http://purl.org/goodrelations/v1#Buy'  # What I want to do with it
ADAPTER_PORT = 8011


# =================================================================
# Create adapter with full autonomy
# =================================================================
try:
    adapter = HypermediaMetaAdapter(
        name=NAME,

        # Discovery: Find workspace with artifact of this class
        base_uri=BASE_URL,
        goal_artifact_class=GOAL_ITEM_CLASS,
        auto_discover_workspace=True,

        # Role reasoning: Determine role from goal
        goal_type=GOAL_TYPE,  # ← NEW: I want to acquire/buy
        capabilities={"Pay"},
        auto_reason_role=True,  # ← NEW: Automatic role reasoning

        web_id=f'http://localhost:{ADAPTER_PORT}',
        adapter_endpoint=str(ADAPTER_PORT),
        debug=False,
        auto_join=True
    )

    print(f"✓ Workspace discovered: {adapter.workspace_uri}")
    print(f"✓ Artifact discovered: {adapter.goal_artifact_uri}")

except ValueError as e:
    print(f"✗ Failed to initialize: {e}")
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
# Main - Fully Autonomous Agent
# =================================================================
async def main():
    """
    Fully autonomous workflow:
    1. Workspace already discovered by class
    2. Artifact already discovered
    3. Discover protocol from artifact
    4. REASON which role to take (NEW!)
    5. Discover other agents
    6. Propose system with reasoned role
    7. Execute protocol
    """
    adapter.info("=" * 60)
    adapter.info("FULLY AUTONOMOUS BUYER AGENT")
    adapter.info("=" * 60)
    adapter.info(f"Goal Type: {GOAL_TYPE}")
    adapter.info(f"Capabilities: {adapter.capabilities}")
    adapter.info("")

    adapter.start_in_loop()

    # ========================================
    # STEP 1: Discover Protocol
    # ========================================
    adapter.info("STEP 1: Discovering protocol from artifact...")
    protocol = adapter.discover_protocol_for_goal(adapter.goal_artifact_uri)
    if not protocol:
        adapter.leave_workspace()
        return

    adapter.info(f"✓ Discovered protocol: {protocol.name}")
    adapter.info("")

    # ========================================
    # STEP 2: Reason My Role (NEW!)
    # ========================================
    adapter.info("STEP 2: Reasoning which role I should take...")
    adapter.info(f"  My goal: {adapter.goal_type}")
    adapter.info(f"  My capabilities: {adapter.capabilities}")
    adapter.info("")

    my_role = adapter.reason_my_role(protocol)

    if not my_role:
        adapter.logger.error("✗ Could not reason appropriate role")
        adapter.leave_workspace()
        return

    adapter.info(f"✓ Reasoned role: {my_role}")
    adapter.info("  (No hardcoded role name needed!)")
    adapter.info("")

    await asyncio.sleep(2)

    # ========================================
    # STEP 3: Propose System with Reasoned Role
    # ========================================
    adapter.info("STEP 3: Proposing system with reasoned role...")
    adapter.info(f"  Using role: {my_role} (reasoned from goal + capabilities)")
    adapter.info("")

    # Use high-level helper with reasoned role
    proposed_system_name = await adapter.discover_and_propose_system(
        protocol_name=protocol.name,
        system_name="BuySystem",
        my_role=my_role,  # ← Using reasoned role instead of hardcoded!
        goal_item_uri=None  # Already have protocol
    )

    if not proposed_system_name:
        adapter.info("✗ System formation failed")
        adapter.leave_workspace()
        return

    adapter.info(f"✓ System '{proposed_system_name}' formed with my role: {my_role}")
    adapter.info("")

    # ========================================
    # STEP 4: Wait for System Formation
    # ========================================
    adapter.info("STEP 4: Waiting for system to be well-formed...")
    system_ready = await adapter.wait_for_system_formation(
        proposed_system_name,
        timeout=10.0
    )

    if not system_ready:
        adapter.info("✗ System not well-formed")
        adapter.leave_workspace()
        return

    adapter.info("✓ System is well-formed!")
    adapter.info("")

    await asyncio.sleep(2)

    # ========================================
    # STEP 5: Execute Protocol
    # ========================================
    adapter.info("STEP 5: Executing protocol...")
    adapter.info(f"  My role: {my_role}")
    adapter.info(f"  Protocol: {protocol.name}")
    adapter.info("")

    # First purchase
    adapter.info("→ Purchase #1 (10$)...")
    await adapter.initiate_protocol(
        "Buy/Pay",
        generate_buy_params(proposed_system_name, "rug", 10)
    )

    await asyncio.sleep(2)

    # Second purchase
    adapter.info("→ Purchase #2 (20$)...")
    await adapter.initiate_protocol(
        "Buy/Pay",
        generate_buy_params(proposed_system_name, "rug", 20)
    )

    await asyncio.sleep(3)

    # ========================================
    # STEP 6: Clean Up
    # ========================================
    adapter.leave_workspace()

    adapter.info("")
    adapter.info("=" * 60)
    adapter.info("AGENT COMPLETED SUCCESSFULLY")
    adapter.info("=" * 60)
    adapter.info("")
    adapter.info("Summary:")
    adapter.info(f"  ✓ Discovered workspace by artifact class")
    adapter.info(f"  ✓ Discovered artifact: {adapter.goal_artifact_uri}")
    adapter.info(f"  ✓ Discovered protocol: {protocol.name}")
    adapter.info(f"  ✓ Reasoned my role: {my_role} (from goal + capabilities)")
    adapter.info(f"  ✓ Completed 2 purchases")
    adapter.info("")
    adapter.info("No hardcoded URIs or role names - fully autonomous!")


if __name__ == "__main__":
    asyncio.run(main())
