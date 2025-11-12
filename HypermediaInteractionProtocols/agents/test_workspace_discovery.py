#!/usr/bin/env python3
"""
Test script for workspace discovery functionality.

Tests that the HypermediaMetaAdapter initializes correctly with workspace
discovery parameters without actually running the discovery (which requires
the Yggdrasil environment to be running).
"""

from HypermediaMetaAdapter import HypermediaMetaAdapter
from HypermediaTools import clean_workspace_uri

def test_uri_cleaning():
    """Test that workspace URIs are cleaned correctly."""
    print("=" * 60)
    print("Testing Workspace URI Cleaning")
    print("=" * 60)
    print()

    test_cases = [
        ('http://localhost:8080/workspaces/bazaar#workspace', 'http://localhost:8080/workspaces/bazaar/'),
        ('http://localhost:8080/workspaces/bazaar', 'http://localhost:8080/workspaces/bazaar/'),
        ('http://localhost:8080/workspaces/bazaar/', 'http://localhost:8080/workspaces/bazaar/'),
        ('http://localhost:8080/workspaces/bazaar#workspace/', 'http://localhost:8080/workspaces/bazaar/'),
    ]

    all_passed = True
    for input_uri, expected in test_cases:
        result = clean_workspace_uri(input_uri)
        passed = result == expected
        all_passed = all_passed and passed
        status = '✓' if passed else '✗'
        print(f'{status} {input_uri}')
        print(f'   -> {result}')
        if not passed:
            print(f'   Expected: {expected}')

    print()
    if all_passed:
        print("✓ All URI cleaning tests passed")
    else:
        print("✗ Some URI cleaning tests failed")
        return False

    print()
    return True


def test_initialization():
    """Test that adapter initializes without errors."""
    print("=" * 60)
    print("Testing HypermediaMetaAdapter Initialization")
    print("=" * 60)
    print()

    # Test 1: Basic initialization without discovery
    print("Test 1: Basic initialization (no discovery)")
    try:
        adapter = HypermediaMetaAdapter(
            name='TestAgent1',
            workspace_uri='http://localhost:8080/workspaces/bazaar/',
            web_id='http://localhost:9999',
            adapter_endpoint='9999',
            capabilities={'Test'},
            auto_join=False,
            debug=False
        )
        print("  ✓ Basic initialization successful")
        print(f"  - Name: {adapter.name}")
        print(f"  - Workspace: {adapter.workspace_uri}")
        print(f"  - Logger exists: {hasattr(adapter, 'logger')}")
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        return False

    print()

    # Test 2: Initialization with discovery parameters (but not enabled)
    print("Test 2: Initialization with discovery parameters (disabled)")
    try:
        adapter = HypermediaMetaAdapter(
            name='TestAgent2',
            base_uri='http://localhost:8080/',
            goal_artifact_uri='http://localhost:8080/workspaces/bazaar/artifacts/rug#artifact',
            web_id='http://localhost:9998',
            adapter_endpoint='9998',
            capabilities={'Test'},
            auto_discover_workspace=False,  # Disabled
            auto_join=False,
            debug=False
        )
        print("  ✓ Initialization with discovery params successful")
        print(f"  - Name: {adapter.name}")
        print(f"  - Base URI: {adapter.base_uri}")
        print(f"  - Goal: {adapter.goal_artifact_uri}")
        print(f"  - Workspace: {adapter.workspace_uri}")
        print(f"  - Logger exists: {hasattr(adapter, 'logger')}")
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        return False

    print()

    # Test 3: Test discover_workspace method signature (without calling it)
    print("Test 3: Verify discover_workspace method exists")
    try:
        adapter = HypermediaMetaAdapter(
            name='TestAgent3',
            workspace_uri='http://localhost:8080/workspaces/bazaar/',
            web_id='http://localhost:9997',
            adapter_endpoint='9997',
            capabilities={'Test'},
            auto_join=False,
            debug=False
        )

        # Check method exists
        assert hasattr(adapter, 'discover_workspace')
        print("  ✓ discover_workspace method exists")

        # Check it's callable
        assert callable(adapter.discover_workspace)
        print("  ✓ discover_workspace is callable")

        # Check logger is available for the method
        assert hasattr(adapter, 'logger')
        print("  ✓ Logger is available for discover_workspace")

    except Exception as e:
        print(f"  ✗ Failed: {e}")
        return False

    print()
    print("=" * 60)
    print("All tests passed! ✓")
    print("=" * 60)
    print()
    print("NOTE: To test actual workspace discovery, run:")
    print("  1. Start environment: cd HypermediaInteractionProtocols && ./start.sh")
    print("  2. Run agent: python buyer_agent_auto_discovery.py")
    return True


if __name__ == "__main__":
    # Run all tests
    uri_cleaning_ok = test_uri_cleaning()
    initialization_ok = test_initialization()

    success = uri_cleaning_ok and initialization_ok
    exit(0 if success else 1)
