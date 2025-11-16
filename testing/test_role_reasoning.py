#!/usr/bin/env python3
"""
Test script for semantic role reasoning functionality.

Tests that agents can reason which role they should take in a protocol
based on their goals and capabilities, without hardcoding role names.
"""

import HypermediaTools

def test_role_semantics_parsing():
    """Test that we can parse role semantics from protocol metadata."""
    print("=" * 60)
    print("Test 1: Parsing Role Semantics")
    print("=" * 60)
    print()

    # Note: This test requires the protocol server to be running
    # Role semantics are served at the protocol_descriptions endpoint
    protocol_uri = "http://localhost:8005/protocol_descriptions/buy_protocol"

    try:
        semantics = HypermediaTools.get_role_semantics(protocol_uri)

        if not semantics:
            print("⚠️  No role semantics found")
            print("   This is expected if:")
            print("   1. Protocol server not running")
            print("   2. Role semantics not yet integrated into protocol")
            print()
            return False

        print(f"✓ Found semantics for {len(semantics)} role(s)")
        for role_name, props in semantics.items():
            print(f"\n{role_name}:")
            print(f"  Goal: {props.get('goal')}")
            print(f"  Required capability: {props.get('required_capability')}")
            print(f"  Sends: {props.get('sends')}")
            print(f"  Receives: {props.get('receives')}")
            print(f"  Description: {props.get('description')}")

        print()
        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_buyer_role_reasoning():
    """Test reasoning for a buyer agent (goal=Buy, capabilities={Pay})."""
    print("=" * 60)
    print("Test 2: Buyer Role Reasoning")
    print("=" * 60)
    print()

    protocol_uri = "http://localhost:8005/protocol_descriptions/buy_protocol"
    agent_goal = "http://purl.org/goodrelations/v1#Buy"
    agent_capabilities = {"Pay"}

    print(f"Agent profile:")
    print(f"  Goal: {agent_goal} (wants to acquire/buy)")
    print(f"  Capabilities: {agent_capabilities}")
    print()

    try:
        role = HypermediaTools.reason_role_for_goal(
            protocol_uri,
            agent_goal,
            agent_capabilities,
            verbose=True
        )

        if role == "Buyer":
            print("✓ Correct! Agent should be Buyer")
            return True
        elif role:
            print(f"✗ Unexpected role: {role} (expected: Buyer)")
            return False
        else:
            print("⚠️  Could not reason role (semantics may not be available)")
            return False

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_seller_role_reasoning():
    """Test reasoning for a seller agent (goal=Sell, capabilities={Give})."""
    print("=" * 60)
    print("Test 3: Seller Role Reasoning")
    print("=" * 60)
    print()

    protocol_uri = "http://localhost:8005/protocol_descriptions/buy_protocol"
    agent_goal = "http://purl.org/goodrelations/v1#Sell"
    agent_capabilities = {"Give"}

    print(f"Agent profile:")
    print(f"  Goal: {agent_goal} (wants to provide/sell)")
    print(f"  Capabilities: {agent_capabilities}")
    print()

    try:
        role = HypermediaTools.reason_role_for_goal(
            protocol_uri,
            agent_goal,
            agent_capabilities,
            verbose=True
        )

        if role == "Seller":
            print("✓ Correct! Agent should be Seller")
            return True
        elif role:
            print(f"✗ Unexpected role: {role} (expected: Seller)")
            return False
        else:
            print("⚠️  Could not reason role (semantics may not be available)")
            return False

    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_capability_mismatch():
    """Test that agent can't take role if missing required capability."""
    print("=" * 60)
    print("Test 4: Capability Mismatch")
    print("=" * 60)
    print()

    protocol_uri = "http://localhost:8005/protocol_descriptions/buy_protocol"
    agent_goal = "http://purl.org/goodrelations/v1#Buy"
    agent_capabilities = {"Give"}  # Wrong capability for Buyer!

    print(f"Agent profile:")
    print(f"  Goal: {agent_goal} (wants to buy)")
    print(f"  Capabilities: {agent_capabilities} (but can only Give, not Pay!)")
    print()

    try:
        role = HypermediaTools.reason_role_for_goal(
            protocol_uri,
            agent_goal,
            agent_capabilities,
            verbose=True
        )

        if role is None:
            print("✓ Correct! Agent cannot take any role (missing Pay capability)")
            return True
        else:
            print(f"✗ Unexpected: Agent got role {role} despite capability mismatch")
            return False

    except Exception as e:
        print(f"✗ Error: {e}")
        return False


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("SEMANTIC ROLE REASONING TESTS")
    print("=" * 60)
    print()
    print("These tests demonstrate semantic role reasoning:")
    print("- Agents reason which role to take based on goals + capabilities")
    print("- No hardcoded role names needed!")
    print()
    print("IMPORTANT: These tests require:")
    print("1. Protocol server running (./start.sh)")
    print("2. Role semantics integrated into buy_protocol")
    print()

    # Run all tests
    results = []
    results.append(("Role Semantics Parsing", test_role_semantics_parsing()))
    results.append(("Buyer Role Reasoning", test_buyer_role_reasoning()))
    results.append(("Seller Role Reasoning", test_seller_role_reasoning()))
    results.append(("Capability Mismatch", test_capability_mismatch()))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")

    print()
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("\n🎉 All tests passed!")
        print("\nNext steps:")
        print("1. Integrate role semantics into protocol server")
        print("2. Update buyer agent to use role reasoning")
        print("3. Test end-to-end with full environment")
    else:
        print("\n⚠️  Some tests failed")
        print("\nThis is expected if:")
        print("- Protocol server not running")
        print("- Role semantics not yet served by protocol server")
        print("\nTo fix:")
        print("1. Make sure ./start.sh is running")
        print("2. Ensure buy_protocol includes role semantics")

    exit(0 if passed == total else 1)
