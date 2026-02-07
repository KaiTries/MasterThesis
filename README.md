# Interaction Protocol and Hypermedia based Multi-Agent Systems


https://github.com/user-attachments/assets/82f1db71-30f4-477a-a9ab-52ccd14b78b5


This project presents a novel approach to building **fully autonomous multi-agent systems** that combine **BSPL (Blindingly Simple Protocol Language) interaction protocols** with **semantic hypermedia-driven discovery** and **autonomous role reasoning**. The system enables agents to autonomously discover their environment, reason about which roles to take, and collaborate through formally specified protocols—all without requiring centralized coordination or hardcoded knowledge.

- [Getting Started](#getting-started)
- [Demo Scenario](#demo-scenario)

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

2. Install custom BSPL version with MetaAdapter

```bash
cd bspl
pip install -e .
```
### Example Agents

See these complete examples:

- **`buyer_agent.py`** - Fully autonomous buyer 
- **`bazaar_agent.py`** - Seller agent for the bazaar workspace (Buy protocol)
- **`supermarket_agent.py`** - Seller agent for the supermarket workspace (BuyTwo protocol)

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
