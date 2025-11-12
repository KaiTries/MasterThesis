# HypermediaMetaAdapter Refactoring Guide

## Overview

The `HypermediaMetaAdapter` provides a unified abstraction that combines BSPL protocol enactment with hypermedia discovery and workspace interaction. This eliminates the need to manually coordinate between `MetaAdapter` and `HypermediaTools`.

## Architecture

### Before (Original Design)

```
Agent Implementation
├── MetaAdapter (BSPL protocol enactment)
├── HypermediaTools (manual function calls)
│   ├── join_workspace()
│   ├── get_agents()
│   ├── get_protocol()
│   └── ...
└── Manual coordination code
```

**Issues:**
- Fragmented: Agent code manually coordinates hypermedia and protocol logic
- Boilerplate: Every agent repeats the same workspace join/leave/discover pattern
- Error-prone: Easy to forget steps like advertising roles or cleaning up

### After (New Design)

```
Agent Implementation
└── HypermediaMetaAdapter
    ├── BSPL Protocol Enactment (inherited from MetaAdapter)
    ├── Workspace Management (join/leave)
    ├── Discovery Methods (agents, protocols, goals)
    ├── Role Advertisement
    └── High-level Workflows
```

**Benefits:**
- ✅ **Cohesive**: All agent functionality in one object
- ✅ **Declarative**: High-level methods like `discover_and_propose_system()`
- ✅ **Less code**: Automatic workspace management
- ✅ **Safer**: Context manager support for cleanup

## Code Comparison

### Workspace Join/Leave

**Before:**
```python
from helpers import join_workspace, leave_workspace

# Manual metadata generation
metadata = get_body_metadata()

# Manual join
success, artifact_address = join_workspace(
    BAZAAR_URI,
    web_id=WEB_ID,
    agent_name=NAME,
    metadata=metadata
)

if not success:
    # Manual error handling
    leave_workspace(BAZAAR_URI, web_id=WEB_ID, agent_name=NAME)
    exit(1)

# ... do work ...

# Manual cleanup
leave_workspace(BAZAAR_URI, web_id=WEB_ID, agent_name=NAME)
```

**After:**
```python
from HypermediaMetaAdapter import HypermediaMetaAdapter

# Automatic join on creation
adapter = HypermediaMetaAdapter(
    name="BuyerAgent",
    workspace_uri=WORKSPACE_URI,
    web_id=WEB_ID,
    adapter_endpoint="8011",
    capabilities={"Pay"},
    auto_join=True  # Handles everything
)

# ... do work ...

# Simple cleanup
adapter.leave_workspace()

# Or use context manager for automatic cleanup:
with HypermediaMetaAdapter(...) as adapter:
    # ... do work ...
    pass  # Automatically leaves workspace
```

### Agent Discovery

**Before:**
```python
from helpers import get_agents

# Manual discovery
agents = get_agents(BAZAAR_URI, artifact_address)

# Manual address book updates
for agent in agents:
    adapter.upsert_agent(agent.name, agent.addresses)
```

**After:**
```python
# One line - automatic address book update
agents = adapter.discover_agents()
```

### Protocol Discovery

**Before:**
```python
from helpers import get_protocol
from semantics_helper import get_protocol_name_from_goal_two

# Multiple steps
protocol_name = get_protocol_name_from_goal_two(BAZAAR_URI, GOAL_ITEM)
if protocol_name is None:
    # Error handling
    pass

protocol = get_protocol(BAZAAR_URI, protocol_name)
adapter.add_protocol(protocol)
```

**After:**
```python
# One line - handles everything
protocol = adapter.discover_protocol_for_goal(GOAL_ITEM)
```

### System Proposal and Role Negotiation

**Before:**
```python
# Manual protocol discovery
protocol_name = get_protocol_name_from_goal_two(BAZAAR_URI, GOAL_ITEM)
protocol = get_protocol(BAZAAR_URI, protocol_name)
adapter.add_protocol(protocol)

# Manual agent discovery
agents = get_agents(BAZAAR_URI, artifact_address)
for agent in agents:
    adapter.upsert_agent(agent.name, agent.addresses)

# Manual system construction
system_dict = {
    "protocol": protocol,
    "roles": {
        "Buyer": NAME,
        "Seller": None
    }
}

proposed_system_name = adapter.propose_system("BuySystem", system_dict)
await adapter.offer_roles(system_dict, proposed_system_name, agents)

# Manual waiting with timeout logic
await asyncio.sleep(5)
if adapter.proposed_systems.get_system(proposed_system_name).is_well_formed():
    # Continue...
```

**After:**
```python
# Single high-level call
proposed_system_name = await adapter.discover_and_propose_system(
    protocol_name="Buy",
    system_name="BuySystem",
    my_role="Buyer",
    goal_item_uri=GOAL_ITEM  # Automatic protocol discovery
)

# Built-in waiting with timeout
if await adapter.wait_for_system_formation(proposed_system_name, timeout=10.0):
    # Continue...
```

### Role Advertisement

**Before:**
```python
from helpers import body_role_metadata, update_body

# Manual protocol addition
protocol = get_protocol(BAZAAR)
new_roles = adapter.add_protocol(protocol)

# Manual metadata generation
roles_rdf = body_role_metadata(artifact_address, new_roles, protocol.name)

# Manual upload
response = update_body(artifact_address, web_id=WEB_ID, agent_name=NAME, metadata=roles_rdf)
```

**After:**
```python
# Discover and add protocol
adapter.discover_protocol("Buy")

# One line to advertise all capable roles
adapter.advertise_roles()
```

## Complete Example Comparison

### Original Buyer Agent (78 lines of logic)

```python
from bspl.adapter import MetaAdapter
from helpers import *
from semantics_helper import *

# Configuration
NAME = "BuyerAgent"
WEB_ID = 'http://localhost:8011'
BAZAAR_URI = 'http://localhost:8080/workspaces/bazaar/'
GOAL_ITEM = 'http://localhost:8080/workspaces/bazaar/artifacts/rug#artifact'
SELF = [('127.0.0.1',8011)]

adapter = MetaAdapter(name=NAME, systems={}, agents={NAME: SELF}, capabilities={"Pay",})

@adapter.reaction("Give")
async def give_reaction(msg):
    adapter.info(f"Order {msg['buyID']} successful")
    return msg

async def main():
    adapter.start_in_loop()

    # Manual workspace join
    success, artifact_address = join_workspace(BAZAAR_URI, web_id=WEB_ID, agent_name=NAME, metadata=get_body_metadata())
    if not success:
        adapter.logger.error("Could not join the bazaar workspace")
        leave_workspace(BAZAAR_URI, web_id=WEB_ID, agent_name=NAME)
        exit(1)

    # Manual protocol discovery
    protocol_name = get_protocol_name_from_goal_two(BAZAAR_URI, GOAL_ITEM)
    if protocol_name is None:
        adapter.logger.error(f"No protocol found")
        leave_workspace(BAZAAR_URI, web_id=WEB_ID, agent_name=NAME)
        exit(1)

    protocol = get_protocol(BAZAAR_URI, protocol_name)
    adapter.add_protocol(protocol)

    # Manual agent discovery
    agents = get_agents(BAZAAR_URI, artifact_address)
    for agent in agents:
        adapter.upsert_agent(agent.name, agent.addresses)
    await asyncio.sleep(5)

    # Manual system proposal
    system_dict = {
        "protocol": protocol,
        "roles": {"Buyer": NAME, "Seller": None}
    }
    proposed_system_name = adapter.propose_system("BuySystem", system_dict)
    await adapter.offer_roles(system_dict, proposed_system_name, agents)

    await asyncio.sleep(5)
    if adapter.proposed_systems.get_system(proposed_system_name).is_well_formed():
        await adapter.initiate_protocol("Buy/Pay", generate_buy_params(...))

    # Manual cleanup
    leave_workspace(BAZAAR_URI, web_id=WEB_ID, agent_name=NAME)
```

### Refactored Buyer Agent (45 lines of logic)

```python
from HypermediaMetaAdapter import HypermediaMetaAdapter

# Configuration
NAME = "BuyerAgent"
WORKSPACE_URI = 'http://localhost:8080/workspaces/bazaar/'
GOAL_ITEM = 'http://localhost:8080/workspaces/bazaar/artifacts/rug#artifact'

adapter = HypermediaMetaAdapter(
    name=NAME,
    workspace_uri=WORKSPACE_URI,
    web_id='http://localhost:8011',
    adapter_endpoint="8011",
    capabilities={"Pay"},
    auto_join=True  # Automatic workspace join
)

@adapter.reaction("Give")
async def give_reaction(msg):
    adapter.info(f"Order {msg['buyID']} successful")
    return msg

async def main():
    adapter.start_in_loop()

    # High-level workflow method
    proposed_system_name = await adapter.discover_and_propose_system(
        protocol_name="Buy",
        system_name="BuySystem",
        my_role="Buyer",
        goal_item_uri=GOAL_ITEM
    )

    if not proposed_system_name:
        adapter.leave_workspace()
        return

    # Built-in waiting
    if await adapter.wait_for_system_formation(proposed_system_name, timeout=10.0):
        await adapter.initiate_protocol("Buy/Pay", generate_buy_params(...))

    adapter.leave_workspace()
```

**Reduction: ~42% less code with more functionality!**

## API Reference

### HypermediaMetaAdapter Constructor

```python
adapter = HypermediaMetaAdapter(
    name: str,              # Agent name
    workspace_uri: str,     # Workspace to join
    web_id: str,           # Web identifier
    adapter_endpoint: str,  # Port for BSPL adapter
    capabilities: set,      # Message names agent can send
    systems: dict = None,   # Initial systems (usually empty)
    agents: dict = None,    # Initial agents (usually empty)
    debug: bool = False,    # Enable debug logging
    auto_join: bool = True  # Auto-join workspace on init
)
```

### Workspace Methods

```python
# Join workspace (automatic if auto_join=True)
success, artifact_addr = adapter.join_workspace()

# Leave workspace
success = adapter.leave_workspace()
```

### Discovery Methods

```python
# Discover agents in workspace (auto-updates address book)
agents = adapter.discover_agents()

# Discover protocol by name
protocol = adapter.discover_protocol("Buy")

# Discover protocol from goal item (semantic reasoning)
protocol = adapter.discover_protocol_for_goal(goal_item_uri)

# Advertise roles after adding protocols
adapter.advertise_roles()
```

### High-Level Workflows

```python
# All-in-one: discover protocol, agents, propose system, negotiate roles
system_name = await adapter.discover_and_propose_system(
    protocol_name="Buy",
    system_name="BuySystem",
    my_role="Buyer",
    goal_item_uri=GOAL_ITEM  # Optional: for semantic discovery
)

# Wait for system to become well-formed
ready = await adapter.wait_for_system_formation(
    system_name,
    timeout=30.0,
    check_interval=0.5
)
```

### Context Manager Support

```python
# Automatic cleanup
with HypermediaMetaAdapter(...) as adapter:
    # ... do work ...
    pass  # Automatically leaves workspace

# Async version
async with HypermediaMetaAdapter(...) as adapter:
    # ... do async work ...
    pass
```

## Migration Guide

### Step 1: Update Imports

**Remove:**
```python
from bspl.adapter import MetaAdapter
from helpers import *
from semantics_helper import *
```

**Add:**
```python
from HypermediaMetaAdapter import HypermediaMetaAdapter
```

### Step 2: Update Adapter Creation

**Before:**
```python
adapter = MetaAdapter(
    name=NAME,
    systems={},
    agents={NAME: SELF},
    capabilities={"Pay"}
)
```

**After:**
```python
adapter = HypermediaMetaAdapter(
    name=NAME,
    workspace_uri=WORKSPACE_URI,
    web_id=WEB_ID,
    adapter_endpoint="8011",
    capabilities={"Pay"},
    auto_join=True
)
```

### Step 3: Replace Manual Operations

Replace manual `join_workspace()`, `get_agents()`, `get_protocol()` calls with adapter methods:

- `join_workspace(...)` → `adapter.join_workspace()` (or automatic)
- `get_agents(...)` → `adapter.discover_agents()`
- `get_protocol(...)` → `adapter.discover_protocol(name)`
- `body_role_metadata(...)` + `update_body(...)` → `adapter.advertise_roles()`

### Step 4: Use High-Level Workflows

Replace multi-step system proposal with:

```python
await adapter.discover_and_propose_system(
    protocol_name="Buy",
    system_name="BuySystem",
    my_role="Buyer",
    goal_item_uri=GOAL_ITEM
)
```

### Step 5: Test

Run your agent and verify:
- ✅ Joins workspace correctly
- ✅ Discovers protocols and agents
- ✅ Role negotiation works
- ✅ Protocol enactment succeeds
- ✅ Leaves workspace on exit

## Best Practices

1. **Use auto_join=True** unless you need precise control over when to join
2. **Use context managers** for automatic cleanup
3. **Use high-level workflows** (`discover_and_propose_system`) when possible
4. **Call advertise_roles()** after adding protocols so others can discover your capabilities
5. **Use wait_for_system_formation()** instead of manual sleep loops
6. **Enable debug logging** during development

## Backward Compatibility

- Original `MetaAdapter` still works unchanged
- `HypermediaTools` functions still available
- Old agents (`buyer_agent.py`, `bazaar_agent.py`) continue to work
- New agents should use `HypermediaMetaAdapter`

## Files

- `HypermediaMetaAdapter.py` - The new adapter class
- `buyer_agent_refactored.py` - Example refactored buyer
- `bazaar_agent_refactored.py` - Example refactored seller
- `buyer_agent.py` - Original (still functional)
- `bazaar_agent.py` - Original (still functional)
