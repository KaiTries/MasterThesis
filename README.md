# Interaction Protocol and Hypermedia based Multi-Agent Systems


https://github.com/user-attachments/assets/82f1db71-30f4-477a-a9ab-52ccd14b78b5


This project presents a novel approach to building **fully autonomous multi-agent systems** that combine **BSPL (Blindingly Simple Protocol Language) interaction protocols** with **semantic hypermedia-driven discovery** and **autonomous role reasoning**. The system enables agents to autonomously discover their environment, reason about which roles to take, and collaborate through formally specified protocols—all without requiring centralized coordination or hardcoded knowledge.

## Table of Contents

- [Overview](#overview)
- [Key Concepts](#key-concepts)
- [Architecture](#architecture)
- [Getting Started](#getting-started)
- [Demo Scenario](#demo-scenario)
- [Project Structure](#project-structure)

## Overview

Traditional multi-agent systems often rely on hardcoded agent configurations or centralized orchestration. This project introduces a **fully decentralized, autonomous approach** where:

- **Agents discover workspaces** by semantically crawling from a base URL - no hardcoded paths
- **Agents discover artifacts** by their semantic class (e.g., `ex:Rug`, `ex:Grill`) - no exact URIs needed
- **Agents discover protocols** through hypermedia traversal from goal artifacts
- **Agents reason about roles** based on their goals and capabilities - no hardcoded role names
- **Agents adapt to different protocols** automatically - same code handles Buy (2 messages) and BuyTwo (4 messages with handshake)
- **Dynamic role negotiation** allows agents to form systems at runtime through a universal metaprotocol
- **Protocol compliance** is ensured through BSPL formal specifications and verification
- **Hypermedia affordances** guide all agent interactions

- Agents only need to know: (1) where to start, (2) what type of thing they want, (3) what they want to do with it, (4) what they can do
- Everything else—workspace location, exact artifact URI, protocol specification, which role to take, message sequencing—is discovered and reasoned autonomously

The system is particularly suited for scenarios requiring flexible, decentralized coordination between autonomous agents, such as e-commerce transactions, supply chain coordination, or any multi-party business process where protocols may vary across different contexts.

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

**Example - BuyTwo Protocol (with handshake):**
```bspl
BuyTwo {
  roles Buyer, Seller
  parameters out firstID key, out buyID key, out itemID key, out item, out money

  Buyer -> Seller: HandShake[out firstID key]
  Seller -> Buyer: AcceptHandShake[in firstID key, out buyID key]
  Buyer -> Seller: Pay[in firstID key, in buyID key, out itemID key, out money]
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

### Class-Based Artifact Discovery
1. Start at base URI (e.g., `http://localhost:8080/`)
2. Crawl through workspaces using hypermedia links
3. Query each workspace for artifacts of the semantic class
4. Return workspace + artifact when found

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
│  • Semantic Role Reasoning                          │
│  • Class-Based Discovery                            │
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

2. Build and add the environment provider (Yggdrasil) NOT NEEDED ANYMORE BINARY IS ADDED TO ENV

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
### Example Agents

See these complete examples:

- **`buyer_agent.py`** - Fully autonomous buyer 
- **`bazaar_agent.py`** - Seller agent for the bazaar workspace (Buy protocol)
- **`supermarket_agent.py`** - Seller agent for the supermarket workspace (BuyTwo protocol)

## Demo Scenario

### Motivating Scenario

> An AI agent needs to purchase items in a decentralized multi-marketplace environment. The agent starts with minimal knowledge:
> - An entry point URL (`http://localhost:8080/`)
> - The semantic type of item wanted (`ex:Rug` or `ex:Grill`)
> - Its goal (`gr:seeks` - to acquire/purchase)
> - Its capabilities (`Pay`, `HandShake` - can send payment and perform handshake)
>
> From just this information, the agent autonomously:
> 1. Discovers which workspace contains the desired item type
> 2. Finds the specific artifact
> 3. Discovers the appropriate protocol (Buy or BuyTwo)
> 4. Reasons it should take the Buyer role
> 5. Finds and negotiates with the appropriate seller
> 6. Adapts to different protocol requirements and completes the purchase

This demonstrates **true autonomous behavior** - the agent navigates, adapts to different protocols, and reasons using only semantic information.

### Two-Workspace Scenario

The demo environment includes two distinct marketplaces:

**Bazaar Workspace** (`ex:Rug` artifacts)
- Simple **Buy** protocol (2 messages: Pay → Give)
- Seller agent with `Give` capability

**Supermarket Workspace** (`ex:Grill` artifacts)
- Extended **BuyTwo** protocol (4 messages: HandShake → AcceptHandShake → Pay → Give)
- Seller agent with `Give` and `AcceptHandShake` capabilities

The buyer agent must discover which workspace has the desired item and adapt to that workspace's protocol **without any code changes**.

### How to Run the Demo

1. Start the environment and seller agents:

```bash
cd HypermediaInteractionProtocols
./start.sh
```

This starts:
- **Yggdrasil** (hypermedia environment on port 8080)
- **Protocol Server** (serves protocol metadata on port 8005)
- **Bazaar Agent** (seller for rugs on port 8010)
- **Supermarket Agent** (seller for grills on port 8013)

2. Open a new terminal and start the autonomous buyer agent:

```bash
cd HypermediaInteractionProtocols/agents
python buyer_agent.py
```

3. When prompted, enter the item you want to buy:
   - Type `rug` to purchase from the bazaar (uses Buy protocol)
   - Type `grill` to purchase from the supermarket (uses BuyTwo protocol)
   - Type `exit` to quit

### What Happens in the Demo

**For Rug Purchase (Bazaar/Buy Protocol):**

**Discovery Phase:**
1. **Workspace Discovery**: Agent crawls from `http://localhost:8080/` to find workspace containing `ex:Rug`
2. **Artifact Discovery**: Agent queries bazaar workspace and finds the rug artifact URI
3. **Protocol Discovery**: Agent discovers Buy protocol linked from the rug
4. **Agent Discovery**: Agent finds bazaar_agent (seller) in workspace

**Reasoning Phase:**
5. **Role Reasoning**: Agent reasons it should be "Buyer" based on goal (`gr:seeks`) and capability (`Pay`)
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

**For Grill Purchase (Supermarket/BuyTwo Protocol):**

The workflow is identical, except:
- Discovers **supermarket** workspace with `ex:Grill` artifacts
- Discovers **BuyTwo** protocol (with handshake requirement)
- Negotiates with **supermarket_agent**
- Executes **4-message protocol**: HandShake → AcceptHandShake → Pay → Give

**Console Output** shows:
- Workspace discovery progress (crawling, querying)
- Artifact discovery (finding item by semantic class)
- Role reasoning steps (goal matching, capability validation)
- Role negotiation messages
- Protocol messages (varies by protocol)
- Transaction completion

### Key Features Demonstrated

#### Semantic Role Reasoning

Agents determine which role to take based on:
- **Goal alignment**: Role's purpose matches agent's goal
- **Capability matching**: Agent has required capabilities
- **Automatic validation**: Incompatible roles rejected

#### Class-Based Discovery

Agents find artifacts by semantic type:
- **Type-based search**: Query by `ex:Rug`, not exact URI
- **Workspace crawling**: Autonomous navigation through hierarchy
- **Hypermedia-driven**: Pure HATEOAS navigation

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
├── README.md                          # This file
├── requirements.txt
│
├── bspl/                              # BSPL core library
│   ├── src/bspl/
│       ├── adapter/
│           ├── core.py                # Base Adapter
│           ├── meta_adapter.py        # MetaAdapter with role negotiation
│           └── ...
│
├── HypermediaInteractionProtocols/    # Implementation
│   ├── agents/
│   │   ├── HypermediaMetaAdapter.py   # Unified adapter framework
│   │   ├── HypermediaTools.py         # Discovery & reasoning utilities
│   │   ├── buyer_agent.py             # Autonomous buyer agent (demo)
│   │   ├── bazaar_agent.py            # Seller agent (Buy protocol)
│   │   └── supermarket_agent.py       # Seller agent (BuyTwo protocol)
│   │
│   ├── env/
│   │   ├── protocols/
│   │   │   ├── buy.bspl               # Buy protocol spec
│   │   │   ├── buy_two.bspl           # BuyTwo protocol spec (with handshake)
│   │   │   └── protocol.py            # Protocol server (serves metadata)
│   │   ├── conf/
│   │   │   ├── buy_demo.json          # Environment configuration
│   │   │   └── metadata/              # Semantic metadata (RDF/Turtle)
│   │   │       ├── rug.ttl            # Rug artifact metadata
│   │   │       ├── grill.ttl          # Grill artifact metadata
│   │   │       └── ...
│   │   └── yggdrasil-*.jar            # Hypermedia environment
│   │
│   └── start.sh                       # Demo startup script
│
└── yggdrasil/                         # Yggdrasil hypermedia platform source OLD
```

### Code Documentation

- **`HypermediaMetaAdapter.py`** - Main framework class with inline documentation
- **`HypermediaTools.py`** - Discovery and reasoning utilities with detailed docstrings
- **`buyer_agent.py`** - Complete example with extensive comments
- **`bspl/`** - BSPL library with protocol samples and verification tools

## Research Contributions

This project demonstrates:

1. **Autonomous Agent Behavior** - Agents navigate and reason using only semantic information
2. **Protocol Adaptation** - Same agent code handles different protocols discovered at runtime (Buy vs BuyTwo)
3. **Semantic Web Integration** - Practical use of RDF, SPARQL, and W3C Thing Descriptions for agent coordination
4. **Formal Protocol Verification** - BSPL verification ensures enactability and deadlock-freedom
5. **Semantic Role Reasoning** - Goal and capability-based role selection without hardcoded bindings
6. **Decentralized Coordination** - No central authority, pure peer-to-peer negotiation via metaprotocol
7. **Hypermedia-Driven Discovery** - True HATEOAS navigation for autonomous workspace and artifact discovery

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
