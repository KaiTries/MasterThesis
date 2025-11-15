# Quick Reference: System Implementation Summary

## What This System Does

This Master's Thesis implements a **fully autonomous multi-agent system** where agents can:

1. **Discover** their environment without hardcoding
   - Workspaces (through semantic crawling)
   - Artifacts (by semantic type, not URI)
   - Protocols (through semantic links)
   - Other agents (through Thing Descriptions)

2. **Reason** which roles they should take
   - Based on their **goals** (what they want to achieve)
   - Based on their **capabilities** (what they can do)
   - Automatically matching to roles with compatible semantics

3. **Negotiate** participation dynamically
   - Propose systems with themselves in one role
   - Offer other roles to compatible agents
   - Exchange system details once all roles are bound
   - Execute formally verified protocols

4. **Execute** protocols correctly
   - Following strict message ordering rules
   - Ensuring information flows correctly
   - Preventing deadlocks through formal verification

## The Three Core Innovations

### 1. Semantic Role Reasoning
Instead of hardcoding "I am the Buyer", agents reason:
- "My goal is to Buy, I can Pay → I should be the Buyer"
- Enables same agent code to work for different goals
- No role name hardcoding needed

### 2. Class-Based Artifact Discovery
Instead of hardcoding `http://example.org/artifacts/rug#123`, agents discover:
- "I need an artifact of class ex:Rug"
- Crawl workspaces to find one
- Works if artifacts move between workspaces

### 3. Dynamic Role Negotiation
Instead of centralized role assignment, agents:
- Propose systems with their role filled
- Offer other roles to capable agents
- Negotiate acceptance through metaprotocol
- Execute once all roles confirmed

## Architecture

```
HypermediaMetaAdapter
├── Role Reasoning (semantic goal/capability matching)
├── Discovery (workspace, artifacts, protocols, agents)
├── Negotiation (metaprotocol for role binding)
└── Orchestration (high-level workflows)
    └── extends MetaAdapter
        └── extends Adapter (BSPL protocol layer)
            ├── Protocol enactment
            ├── Message handling (reactions/generators)
            └── System/role management
                └── Communication layer
                    ├── Emitter (send)
                    └── Receiver (receive)
```

## Main Classes and Responsibilities

### HypermediaMetaAdapter (Orchestration)
- **File**: `agents/HypermediaMetaAdapter.py`
- **Inherits from**: MetaAdapter
- **Key methods**:
  - `discover_workspace_by_class()` - Find workspace with artifact type
  - `reason_my_role()` - Determine role from goal + capabilities
  - `discover_and_propose_system()` - High-level workflow
  - `wait_for_system_formation()` - Wait for negotiation

### HypermediaTools (Discovery & Utilities)
- **File**: `agents/HypermediaTools.py`
- **Functions**:
  - `discover_workspace_by_artifact_class()` - DFS crawling for artifact
  - `reason_role_for_goal()` - Match agent goal+capabilities to roles
  - `get_role_semantics()` - Query role metadata
  - `get_agents()` - Discover other agents in workspace
  - RDF/SPARQL operations
  - Workspace join/leave/update operations

### MetaAdapter (Role Negotiation)
- **File**: `bspl/src/bspl/adapter/meta_adapter.py`
- **Inherits from**: Adapter
- **Key methods**:
  - `propose_system()` - Create system with partial role binding
  - `offer_roles()` - Send role offers to agents
  - `role_proposal_handler()` - Handle incoming role offers
  - `accept_handler()` - Handle role acceptance
  - `share_system_details()` - Broadcast final system

### Adapter (Protocol Enactment)
- **File**: `bspl/src/bspl/adapter/core.py`
- **Key methods**:
  - `add_protocol()` - Register a protocol
  - `add_system()` - Register a system instance
  - `reaction()` - Decorator to handle incoming messages
  - `generator()` - Decorator to define outgoing messages
  - `initiate_protocol()` - Send message to start protocol

## Development Patterns

### Pattern 1: Fully Autonomous Agent (Recommended)
```python
adapter = HypermediaMetaAdapter(
    name="BuyerAgent",
    base_uri="http://localhost:8080/",
    goal_artifact_class="http://example.org/Rug",  # What type I want
    goal_type="http://purl.org/goodrelations/v1#Buy",  # What I want to do
    capabilities={"Pay"},  # What I can do
    auto_discover_workspace=True,
    auto_join=True
)

@adapter.reaction("Give")
async def handle_receive(msg):
    return msg

async def main():
    adapter.start_in_loop()
    
    # 1. Discover (automatic)
    protocol = adapter.discover_protocol_for_goal(adapter.goal_artifact_uri)
    agents = adapter.discover_agents()
    
    # 2. Reason (automatic)
    my_role = adapter.reason_my_role(protocol)  # ← Magic happens here!
    
    # 3. Negotiate
    system = await adapter.discover_and_propose_system(
        protocol.name, "System", my_role
    )
    
    # 4. Wait & Execute
    if await adapter.wait_for_system_formation(system):
        await adapter.initiate_protocol("Buy/Pay", {...})
    
    adapter.leave_workspace()
```

### Pattern 2: Manual System Creation
```python
adapter = HypermediaMetaAdapter(
    name="Agent",
    workspace_uri="http://localhost:8080/workspaces/bazaar/",
    capabilities={"Pay"}
)

adapter.join_workspace()

protocol = adapter.discover_protocol("Buy")
system_dict = {
    "protocol": protocol,
    "roles": {"Buyer": adapter.name, "Seller": None}
}

proposed = adapter.propose_system("BuySystem", system_dict)
# ... wait for other agents to accept roles ...
```

## Key Technologies

| Technology | Usage |
|------------|-------|
| **BSPL** | Protocol specification and verification |
| **RDF/Turtle** | Metadata representation |
| **SPARQL** | Querying workspaces and artifacts |
| **W3C Thing Descriptions** | Agent capability descriptions |
| **GoodRelations** | Goal types (Buy, Sell, Lease) |
| **RDFLib** | Python RDF manipulation |
| **Yggdrasil** | Hypermedia environment |
| **asyncio** | Asynchronous execution |
| **HTTP** | Network communication |

## Autonomy Progression

The project demonstrates 4 levels of autonomy:

**Level 1: Hardcoded** (No discovery)
```
Agent knows: Workspace URI, Artifact URI, Role
Agent discovers: Nothing
```

**Level 2: URI-Based Discovery**
```
Agent knows: Base URI, Artifact URI, Role
Agent discovers: Workspace location
```

**Level 3: Class-Based Discovery**
```
Agent knows: Base URI, Artifact class, Role
Agent discovers: Workspace + Artifact URI
```

**Level 4: Full Autonomy** ✅
```
Agent knows: Base URI, Artifact class, Goal, Capabilities
Agent discovers: Everything (workspace, artifact, role)
```

## Data Models

### Protocol (BSPL)
```bspl
Buy {
    roles Buyer, Seller
    parameters out buyID key, out itemID key, out item, out money
    
    Buyer -> Seller: Pay[out buyID key, out itemID key, out money]
    Seller -> Buyer: Give[in buyID key, in itemID key, in money, out item]
}
```

### Role Semantics (RDF/Turtle)
```turtle
<protocols/buy#BuyerRole>
    bspl:roleName "Buyer" ;
    bspl:hasGoal gr:Buy ;           # Goal: acquire
    bspl:requiresCapability "Pay" ;  # Required capability
    bspl:sendsMessage "Pay" ;
    bspl:receivesMessage "Give" .
```

### Artifact (RDF/Turtle)
```turtle
<artifacts/rug#artifact>
    a ex:Rug ;  # ← Semantic class for discovery
    td:title "rug" ;
    gr:ActualProductOrServiceInstance .
```

## Key Design Decisions

1. **Three-Layer Architecture**
   - Protocol layer (BSPL Adapter)
   - Hypermedia layer (HypermediaMetaAdapter)
   - Tools/utilities layer (HypermediaTools)

2. **Semantic Web Foundation**
   - All metadata in RDF/Turtle
   - SPARQL for queries
   - Standards-compliant (W3C)

3. **Goal + Capability Reasoning**
   - Not role name matching
   - Semantic alignment
   - Protocol-agnostic

4. **DFS Workspace Crawling**
   - Decentralized (no registry)
   - Hypermedia-driven
   - Adaptive to structure

5. **Thing Descriptions for Agents**
   - W3C standard format
   - Comprehensive metadata
   - Machine-readable

## Important Files

```
bspl/
├── src/bspl/
│   ├── adapter/
│   │   ├── core.py              ← Adapter base class
│   │   ├── meta_adapter.py      ← Role negotiation
│   │   └── ...
│   ├── protocol.py              ← Protocol classes
│   └── verification/            ← Protocol verification

HypermediaInteractionProtocols/agents/
├── HypermediaMetaAdapter.py     ← Main orchestration
├── HypermediaTools.py           ← Discovery utilities
│
├── buyer_agent_with_role_reasoning.py  ← Level 4 example
├── buyer_agent_auto_discovery.py       ← Level 3 example
├── buyer_agent_with_discovery.py       ← Level 2 example
├── bazaar_agent.py              ← Seller example
│
├── SEMANTIC_ROLE_REASONING.md
├── AUTONOMY_EVOLUTION.md
└── test_role_reasoning.py

HypermediaInteractionProtocols/env/
├── protocols/
│   ├── buy.bspl                 ← Protocol spec
│   └── protocol.py              ← Protocol server
└── conf/metadata/
    ├── rug.ttl                  ← Artifact metadata
    └── buy_protocol_role_semantics.ttl  ← Role semantics
```

## Research Contributions

1. **Semantic Role Reasoning** - First to combine BSPL with goal+capability reasoning
2. **Class-Based Discovery** - Artifacts found by semantic type, not URI
3. **Unified Architecture** - Three-layer design integrating protocol + discovery + reasoning
4. **Dynamic Negotiation** - Universal metaprotocol for role binding
5. **Verification + Autonomy** - Formal verification combined with autonomous execution

## Code Statistics

- BSPL Library: ~3,500 lines
- HypermediaMetaAdapter: ~556 lines
- HypermediaTools: ~1,265 lines
- Example Agents: ~200 lines
- Documentation: ~5,000+ lines

## Impact

- **~42% less code** in typical agents (vs manual approach)
- **True autonomy** - no hardcoded URIs or role names
- **Semantic discovery** - agents reason about meaning
- **Flexible & reusable** - same code works across protocols
- **Formally verified** - protocols guaranteed deadlock-free

---

For detailed information, see `CODEBASE_ANALYSIS.md` in the repository root.
