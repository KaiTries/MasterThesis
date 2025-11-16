# Interaction Protocol and Hypermedia based Multi-Agent Systems

This project presents a novel approach to building **fully autonomous multi-agent systems** that combine **BSPL (Blindingly Simple Protocol Language) interaction protocols** with **semantic hypermedia-driven discovery** and **autonomous role reasoning**. The system enables agents to autonomously discover their environment, reason about which roles to take, and collaborate through formally specified protocols—all without requiring centralized coordination or hardcoded knowledge.

## Table of Contents

- [Overview](#overview)
- [Key Concepts](#key-concepts)
- [Architecture](#architecture)
- [Autonomy Levels](#autonomy-levels)
- [Getting Started](#getting-started)
- [Building Fully Autonomous Agents](#building-fully-autonomous-agents)
- [Demo Scenario](#demo-scenario)
- [Project Structure](#project-structure)
- [Documentation](#documentation)

## Overview

Traditional multi-agent systems often rely on hardcoded agent configurations or centralized orchestration. This project introduces a **fully decentralized, autonomous approach** where:

- **Agents discover workspaces** by semantically crawling from a base URL - no hardcoded paths
- **Agents discover artifacts** by their semantic class (e.g., `ex:Rug`) - no exact URIs needed
- **Agents discover protocols** through hypermedia traversal from goal artifacts
- **Agents reason about roles** based on their goals and capabilities - no hardcoded role names
- **Dynamic role negotiation** allows agents to form systems at runtime through a universal metaprotocol
- **Protocol compliance** is ensured through BSPL formal specifications
- **Hypermedia affordances** guide all agent interactions

### What Makes This Unique

**True Autonomy Through Semantic Reasoning:**
- Agents only need to know: (1) where to start, (2) what type of thing they want, (3) what they want to do with it, (4) what they can do
- Everything else—workspace location, exact artifact URI, protocol, which role to take—is discovered and reasoned autonomously

The system is particularly suited for scenarios requiring flexible, decentralized coordination between autonomous agents, such as e-commerce transactions, supply chain coordination, or any multi-party business process.

## Key Concepts

### BSPL (Blindingly Simple Protocol Language)

BSPL is a formal language for specifying interaction protocols. A protocol defines:
- **Roles**: Participants in the interaction (e.g., Buyer, Seller)
- **Parameters**: Information exchanged, with adornments (in/out/nil) and optionally marked as keys
- **Messages**: Communications between roles with specific parameter flows

**Example - Buy Protocol:**
```bspl
Buy {
  roles Buyer, Seller
  parameters out buyID key, out itemID key, out item, out money

  Buyer -> Seller: Pay[out buyID key, out itemID key, out money]
  Seller -> Buyer: Give[in buyID key, in itemID key, in money, out item]
}
```

BSPL ensures protocols are **enactable**, **dead-lock free**, and **information-safe** through formal verification.

### HypermediaMetaAdapter

The `HypermediaMetaAdapter` is a unified abstraction that combines BSPL protocol enactment with autonomous hypermedia discovery and semantic reasoning:

**Core Capabilities:**
1. **Class-Based Workspace Discovery** - Find workspaces containing artifacts by semantic class
2. **Semantic Role Reasoning** - Automatically determine which role to take based on goals and capabilities
3. **Dynamic Protocol Management** - Add new protocols at runtime
4. **Dynamic System Formation** - Create protocol enactments with agents discovered at runtime
5. **Role Negotiation** - Built-in metaprotocol for proposing and accepting roles
6. **Capability-Based Matching** - Validate role compatibility with agent capabilities

### Semantic Role Reasoning

**The Innovation:** Agents reason about which role to take based on semantic metadata, eliminating hardcoded role names.

**How It Works:**
```python
# Agent only knows its goal and capabilities
adapter = HypermediaMetaAdapter(
    goal_type="http://purl.org/goodrelations/v1#seeks",  # I want to acquire
    capabilities={"Pay"}  # I can pay
)

# Agent reasons its role automatically
my_role = adapter.reason_my_role(protocol)  # Returns: "Buyer"
```

**Role Semantics** (in protocol metadata):
```turtle
<BuyerRole>
    bspl:hasGoal gr:seeks ;              # This role is for acquiring
    bspl:requiresCapability "Pay" ;    # Capabilities can be directly reasoned from protocol, but this makes it easier for agents

<SellerRole>
    bspl:hasGoal gr:Sell ;             # This role is for providing
    bspl:requiresCapability "Give" ;   # Requires Give capability
```

**Benefits:**
- ✅ No hardcoded role names
- ✅ Same agent code works for different goals (buy vs sell)
- ✅ Protocol-agnostic (works across different protocols)
- ✅ Self-validating (won't take incompatible roles)

### Class-Based Artifact Discovery

**The Innovation:** Agents discover artifacts by their semantic type, not exact URIs.

**Traditional Approach (Brittle):**
```python
# Agent needs exact path - breaks if artifact moves
artifact = "http://localhost:8080/workspaces/bazaar/artifacts/rug#artifact"
```

**Semantic Approach (Autonomous):**
```python
# Agent only knows the type - finds any matching artifact
goal_artifact_class = "http://example.org/Rug"
```

**Discovery Process:**
1. Start at base URI (e.g., `http://localhost:8080/`)
2. Crawl through workspaces using hypermedia links
3. Query each workspace for artifacts of the semantic class
4. Return workspace + artifact when found

**Benefits:**
- ✅ No hardcoded URIs or paths
- ✅ Works if artifacts move between workspaces
- ✅ Finds any artifact matching the semantic type
- ✅ True hypermedia-driven navigation (HATEOAS)

### Role Negotiation Metaprotocol

A universally known metaprotocol enables agents to dynamically bind roles for any protocol:

```mermaid
sequenceDiagram
    autonumber
    participant I as Initiator (MetaAdapter)
    participant C as Candidate (MetaAdapter)

    Note over I: Create system for desired protocol<br/>only own role is filled
    Note over I: Initiate role negotiation with candidates

    I->>C: OfferRole
    Note over C: Upon reception, build metaprotocol system<br/>Reasoning based on goal + capabilities

    alt Candidate accepts
        C-->>I: Accept
        I->>C: SystemDetails
        Note over I,C: Sent once all roles are filled<br/>All agents add system to their adapter
    else Candidate rejects
        C-->>I: Reject
        Note over I: Optionally re-offer to another candidate
    end
```

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                 Agent Application                   │
├─────────────────────────────────────────────────────┤
│         HypermediaMetaAdapter Layer                 │
│  • Semantic Role Reasoning (NEW!)                   │
│  • Class-Based Discovery (NEW!)                     │
│  • Workspace Discovery                              │
│  • Role Negotiation                                 │
│  • Dynamic System Management                        │
├─────────────────────────────────────────────────────┤
│              Base Adapter Layer                     │
│  • Protocol Enactment                               │
│  • Message Handling (Reactors/Generators)           │
│  • History & Integrity Management                   │
├─────────────────────────────────────────────────────┤
│           Communication Layer                       │
│  • Emitter (Send Messages)                          │
│  • Receiver (Receive Messages)                      │
└─────────────────────────────────────────────────────┘
         ↕                        ↕
  [Other Agents]          [Hypermedia Environment]
```

## Autonomy Levels

The system demonstrates **progressive autonomy** through four levels:

| Level | Agent Knows | Agent Discovers | Autonomy |
|-------|-------------|-----------------|----------|
| **1. Hardcoded** | Workspace path + Artifact URI + Role name | Nothing | ⭐️ |
| **2. URI Discovery** | Base + Artifact URI + Role name | Workspace location | ⭐️⭐️ |
| **3. Class Discovery** | Base + Artifact class + Role name | Workspace + Artifact URI | ⭐️⭐️⭐️ |
| **4. Full Autonomy** | **Base + Artifact class + Goal** | **Workspace + Artifact + Role** | **⭐️⭐️⭐️⭐️⭐️** |

**Level 4** represents full autonomy - the agent only needs high-level goals and capabilities, discovering everything else through semantic reasoning.

See [AUTONOMY_EVOLUTION.md](HypermediaInteractionProtocols/agents/AUTONOMY_EVOLUTION.md) for detailed progression.

## Getting Started

### Prerequisites

- Python 3.8+
- Java (for Yggdrasil environment)
- Gradle (for building Yggdrasil)

### Installation

1. Install base dependencies

```bash
pip install -r requirements.txt
```

2. Build and add the environment provider (Yggdrasil)

```bash
cd yggdrasil
./gradlew
cd ..
mv yggdrasil/build/libs/yggdrasil-0.0.0-SNAPSHOT-all.jar HypermediaInteractionProtocols/env
```

3. Install custom BSPL version with MetaAdapter

```bash
cd bspl
pip install -e .
```

## Building Fully Autonomous Agents

### The Recommended Approach: Full Autonomy

Create agents that discover and reason about everything autonomously:

```python
from HypermediaMetaAdapter import HypermediaMetaAdapter
import asyncio

# Agent configuration - only high-level goals!
adapter = HypermediaMetaAdapter(
    name="BuyerAgent",

    # Discovery: Find workspace + artifact by semantic class
    base_uri="http://localhost:8080/",           # Just the entry point
    goal_artifact_class="http://example.org/Rug", # Semantic type (not exact URI!)
    auto_discover_workspace=True,

    # Role Reasoning: Determine role from goal + capabilities
    goal_type="http://purl.org/goodrelations/v1#Buy",  # What I want to do
    capabilities={"Pay"},                              # What I can do
    auto_reason_role=True,                             # Reason my role!

    web_id="http://localhost:8011",
    adapter_endpoint="8011",
    auto_join=True
)

# Define message handler
@adapter.reaction("Give")
async def handle_give(msg):
    adapter.info(f"✓ Received item: {msg['item']}")
    return msg

# Autonomous workflow
async def main():
    adapter.start_in_loop()

    # Discover protocol from discovered artifact
    protocol = adapter.discover_protocol_for_goal(adapter.goal_artifact_uri)

    # Reason which role to take (not hardcoded!)
    my_role = adapter.reason_my_role(protocol)  # Returns: "Buyer"

    # Propose system with reasoned role
    system_name = await adapter.discover_and_propose_system(
        protocol_name=protocol.name,
        system_name="BuySystem",
        my_role=my_role  # ← Reasoned, not hardcoded!
    )

    # Wait for system formation and execute
    if await adapter.wait_for_system_formation(system_name, timeout=10.0):
        await adapter.initiate_protocol("Buy/Pay", {
            "system": system_name,
            "buyID": "order_123",
            "itemID": "rug",
            "money": 100
        })

    adapter.leave_workspace()

asyncio.run(main())
```

### What the Agent Discovers Autonomously

1. ✅ **Workspace location** - Crawls from base URI to find workspace containing rug
2. ✅ **Artifact URI** - Queries workspaces for artifacts of class `ex:Rug`
3. ✅ **Protocol** - Discovers Buy protocol linked from the rug artifact
4. ✅ **Role to take** - Reasons it should be "Buyer" (goal=Buy, capability=Pay)
5. ✅ **Other agents** - Discovers seller agent in workspace
6. ✅ **System formation** - Negotiates roles and forms enactable system

### Key Benefits

- 🎯 **~42% less code** compared to manual approach
- 🤖 **True autonomy** - no hardcoded URIs or role names
- 🔍 **Semantic discovery** - finds resources by meaning, not path
- 🧠 **Intelligent reasoning** - determines appropriate roles automatically
- 🔄 **Flexible & reusable** - same code works for different goals
- ✨ **Production-ready** - comprehensive error handling and logging

### Example Agents

See these complete examples:

- **`buyer_agent_with_role_reasoning.py`** - Full autonomy (Level 4) ⭐ **RECOMMENDED**
- **`buyer_agent_auto_discovery.py`** - Class-based discovery (Level 3)
- **`buyer_agent_with_discovery.py`** - URI-based discovery (Level 2)
- **`buyer_agent_refactored.py`** - Hardcoded (Level 1)

## Demo Scenario

### Motivating Scenario

> An AI agent needs to purchase an item (a rug) in a decentralized marketplace. The agent starts with minimal knowledge:
> - An entry point URL (`http://localhost:8080/`)
> - The semantic type of item wanted (`ex:Rug`)
> - Its goal (`gr:Buy` - to acquire/purchase)
> - Its capabilities (`Pay` - can send payment)
>
> From just this information, the agent autonomously:
> 1. Discovers which workspace contains rugs
> 2. Finds the specific rug artifact
> 3. Discovers the Buy protocol
> 4. Reasons it should take the Buyer role
> 5. Finds and negotiates with a seller
> 6. Completes the purchase

This demonstrates **true autonomous behavior** - the agent navigates and reasons using only semantic information.

### How to Run the Demo

1. Start the environment and bazaar agent:

```bash
cd HypermediaInteractionProtocols
./start.sh
```

This starts:
- **Yggdrasil** (hypermedia environment on port 8080)
- **Protocol Server** (serves protocol metadata on port 8005)
- **Bazaar Agent** (seller agent on port 8010)

2. Open a new terminal and start the fully autonomous buyer agent:

```bash
cd HypermediaInteractionProtocols/agents
python buyer_agent_with_role_reasoning.py
```

### What Happens in the Demo

**Discovery Phase:**
1. **Workspace Discovery**: Agent crawls from `http://localhost:8080/` to find workspace containing `ex:Rug`
2. **Artifact Discovery**: Agent queries workspace and finds the rug artifact URI
3. **Protocol Discovery**: Agent discovers Buy protocol linked from the rug
4. **Agent Discovery**: Agent finds bazaar_agent (seller) in workspace

**Reasoning Phase:**
5. **Role Reasoning**: Agent reasons it should be "Buyer" based on goal (`gr:Buy`) and capability (`Pay`)
6. **Role Validation**: Agent validates it has required capabilities for Buyer role

**Collaboration Phase:**
7. **System Proposal**: Agent proposes Buy system with itself as Buyer
8. **Role Negotiation**: Agent offers Seller role to bazaar_agent via metaprotocol
9. **Role Acceptance**: Bazaar agent accepts (has `Give` capability for Seller role)
10. **System Formation**: Both agents receive system details and finalize binding

**Execution Phase:**
11. **Protocol Enactment**: Buyer initiates by sending Pay message
12. **Transaction Completion**: Seller responds with Give message
13. **Cleanup**: Buyer leaves workspace

**Console Output** shows:
- Workspace discovery progress (crawling, querying)
- Artifact discovery (finding rug by semantic class)
- Role reasoning steps (goal matching, capability validation)
- Role negotiation messages
- Protocol messages (Pay/Give)
- Transaction completion

### Key Features Demonstrated

#### Semantic Role Reasoning

Agents determine which role to take based on:
- **Goal alignment**: Role's purpose matches agent's goal
- **Capability matching**: Agent has required capabilities
- **Automatic validation**: Incompatible roles rejected

No hardcoded role names needed!

#### Class-Based Discovery

Agents find artifacts by semantic type:
- **Type-based search**: Query by `ex:Rug`, not exact URI
- **Workspace crawling**: Autonomous navigation through hierarchy
- **Hypermedia-driven**: Pure HATEOAS navigation

No hardcoded paths needed!

#### Dynamic Role Binding

The metaprotocol enables flexible collaboration:
- **Decentralized**: No central authority assigns roles
- **Goal-driven**: Agents accept roles that match their goals
- **Capability-validated**: Roles rejected if capabilities missing
- **Protocol-agnostic**: Works with any BSPL protocol

#### Protocol Compliance

BSPL ensures correct execution:
- **Message ordering**: Only enabled messages can be sent
- **Parameter flow**: Information flows correctly
- **Integrity checking**: Invalid messages rejected
- **Deadlock freedom**: Protocols verified to be enactable

## Project Structure

```
MasterThesis/
├── README.md                      # This file
├── requirements.txt
│
├── bspl/                          # BSPL core library
│   ├── src/bspl/
│   │   ├── adapter/
│   │   │   ├── core.py            # Base Adapter
│   │   │   ├── meta_adapter.py    # MetaAdapter with role negotiation
│   │   │   └── ...
│   │   ├── protocol.py            # Protocol classes
│   │   └── verification/          # Protocol verification
│   └── samples/                   # Sample BSPL protocols
│
├── HypermediaInteractionProtocols/ # Implementation
│   ├── agents/
│   │   ├── HypermediaMetaAdapter.py           # Unified adapter ⭐
│   │   ├── HypermediaTools.py                 # Discovery & reasoning utilities
│   │   │
│   │   ├── buyer_agent_with_role_reasoning.py # Level 4: Full autonomy ⭐
│   │   ├── buyer_agent_auto_discovery.py      # Level 3: Class discovery
│   │   ├── buyer_agent_with_discovery.py      # Level 2: URI discovery
│   │   ├── buyer_agent_refactored.py          # Level 1: Hardcoded
│   │   │
│   │   ├── bazaar_agent.py                    # Seller agent
│   │   │
│   │   ├── test_role_reasoning.py             # Role reasoning tests
│   │   ├── test_workspace_discovery.py        # Discovery tests
│   │   │
│   │   └── [Documentation files - see below]
│   │
│   ├── env/
│   │   ├── protocols/
│   │   │   ├── buy.bspl                       # Buy protocol spec
│   │   │   └── protocol.py                    # Protocol server (with role semantics)
│   │   ├── conf/metadata/                     # Semantic metadata
│   │   │   ├── rug.ttl                        # Rug artifact (with ex:Rug class)
│   │   │   └── ...
│   │   └── yggdrasil-*.jar                    # Hypermedia environment
│   │
│   └── start.sh                               # Startup script
│
└── yggdrasil/                     # Hypermedia environment source
```

## Documentation

### Guides

- **[AUTONOMY_EVOLUTION.md](HypermediaInteractionProtocols/agents/AUTONOMY_EVOLUTION.md)** - Progression from hardcoded to fully autonomous
- **[CLASS_BASED_DISCOVERY.md](HypermediaInteractionProtocols/agents/CLASS_BASED_DISCOVERY.md)** - Semantic artifact discovery guide
- **[ROLE_REASONING_COMPLETE.md](HypermediaInteractionProtocols/agents/ROLE_REASONING_COMPLETE.md)** - Semantic role reasoning implementation
- **[WORKSPACE_DISCOVERY.md](HypermediaInteractionProtocols/agents/WORKSPACE_DISCOVERY.md)** - Autonomous workspace crawling

### Implementation Details

- **[CLASS_BASED_DISCOVERY_SUMMARY.md](HypermediaInteractionProtocols/agents/CLASS_BASED_DISCOVERY_SUMMARY.md)** - Quick reference for class-based discovery
- **[SEMANTIC_ROLE_REASONING.md](HypermediaInteractionProtocols/agents/SEMANTIC_ROLE_REASONING.md)** - Design and algorithm details
- **[IMPLEMENTATION_COMPLETE.md](HypermediaInteractionProtocols/agents/IMPLEMENTATION_COMPLETE.md)** - Class-based discovery implementation
- **[TROUBLESHOOTING.md](HypermediaInteractionProtocols/agents/TROUBLESHOOTING.md)** - Common issues and solutions

### Legacy/Reference

- **[REFACTORING_GUIDE.md](HypermediaInteractionProtocols/agents/REFACTORING_GUIDE.md)** - Migration from MetaAdapter to HypermediaMetaAdapter
- **[BUGFIX_INITIALIZATION_ORDER.md](HypermediaInteractionProtocols/agents/BUGFIX_INITIALIZATION_ORDER.md)** - Bug fixes during development

## Key Innovations

### 1. Semantic Role Reasoning
Agents reason about which role to take based on:
- **Goals** (what they want to achieve: buy, sell, lease)
- **Capabilities** (what they can do: pay, give, deliver)
- **Protocol semantics** (role descriptions with goals and requirements)

**Impact**: Eliminates hardcoded role names, enables protocol-agnostic agents

### 2. Class-Based Artifact Discovery
Agents find artifacts by semantic type, not exact URIs:
- Query workspaces for artifacts of specific RDF classes
- Autonomous crawling through workspace hierarchies
- Pure hypermedia navigation (HATEOAS)

**Impact**: Eliminates hardcoded paths, enables true autonomous navigation

### 3. Unified Autonomous Architecture
HypermediaMetaAdapter provides single coherent abstraction:
- Discovery (workspaces, artifacts, protocols, agents)
- Reasoning (role selection, capability validation)
- Coordination (role negotiation, system formation)
- Execution (protocol enactment, message handling)

**Impact**: ~42% less code, cleaner architecture, easier to use

## Research Contributions

This project demonstrates:

1. **Autonomous Agent Behavior** - Agents navigate and reason using only semantic information
2. **Semantic Web Integration** - Practical use of RDF, SPARQL, and semantic ontologies for agent coordination
3. **Protocol Compliance** - Formal verification combined with autonomous discovery
4. **Decentralized Coordination** - No central authority, pure peer-to-peer negotiation
5. **Progressive Autonomy** - Clear path from hardcoded to fully autonomous agents

## Further Reading

- **BSPL Specification**: See `bspl/` for detailed protocol language documentation
- **Metaprotocol**: Role negotiation protocol defined in `bspl/src/bspl/adapter/meta_adapter.py`
- **Sample Protocols**: Browse `bspl/samples/` for more BSPL protocol examples
- **W3C Thing Descriptions**: [WoT TD Specification](https://www.w3.org/TR/wot-thing-description/)
- **GoodRelations Ontology**: [GoodRelations](http://purl.org/goodrelations/v1)

## License

This project is part of a Master's Thesis research on autonomous multi-agent systems.

---

**Agents that discover, reason, and collaborate autonomously through semantic hypermedia.** 🤖✨
