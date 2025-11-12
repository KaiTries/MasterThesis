# Agent Autonomy Evolution

## From Hardcoded to Fully Autonomous

This document shows the evolution of agent autonomy through four levels, demonstrating how each enhancement reduces hardcoded knowledge and increases autonomous behavior.

---

## Level 1: Hardcoded Agent (Original)

**Agent knows:** Everything
**Agent discovers:** Nothing

### Configuration
```python
NAME = "BuyerAgent"
WORKSPACE = 'http://localhost:8080/workspaces/bazaar/'  # ← Hardcoded path
GOAL_ITEM = 'http://localhost:8080/workspaces/bazaar/artifacts/rug#artifact'  # ← Exact URI
MY_ROLE = "Buyer"  # ← Hardcoded role name
```

### Code
```python
# Hardcoded workspace
adapter = HypermediaMetaAdapter(
    name=NAME,
    workspace_uri=WORKSPACE,  # ← Knows exact path
    capabilities={"Pay"}
)

# Hardcoded role
system_dict = {
    "protocol": protocol,
    "roles": {
        "Buyer": NAME,  # ← Hardcoded role name
        "Seller": None
    }
}
```

### Problems
- ❌ Brittle: Breaks if workspace moves
- ❌ Not scalable: Need different code for each workspace
- ❌ Not autonomous: Agent is just executing a script
- ❌ No reasoning: All decisions hardcoded

**Autonomy Score: ⭐️ (1/5)**

---

## Level 2: URI-Based Workspace Discovery

**Agent knows:** Base URL + full artifact URI + role name
**Agent discovers:** Workspace location

### Configuration
```python
NAME = "BuyerAgent"
BASE_URL = 'http://localhost:8080/'  # ← Just base
GOAL_ITEM = 'http://localhost:8080/workspaces/bazaar/artifacts/rug#artifact'  # ← Still full URI
MY_ROLE = "Buyer"  # ← Still hardcoded
```

### Code
```python
adapter = HypermediaMetaAdapter(
    name=NAME,
    base_uri=BASE_URL,  # ← Discovers from here
    goal_artifact_uri=GOAL_ITEM,
    auto_discover_workspace=True,  # ← Discovers workspace!
    capabilities={"Pay"}
)

# Still hardcoded role
system_dict = {
    "protocol": protocol,
    "roles": {"Buyer": NAME}  # ← Still hardcoded
}
```

### Improvements
- ✅ Finds workspace automatically
- ✅ Works if artifact moves between workspaces
- ❌ Still needs full artifact URI
- ❌ Still hardcodes role name

**Autonomy Score: ⭐️⭐️ (2/5)**

---

## Level 3: Class-Based Discovery

**Agent knows:** Base URL + artifact semantic class + role name
**Agent discovers:** Workspace location + exact artifact URI

### Configuration
```python
NAME = "BuyerAgent"
BASE_URL = 'http://localhost:8080/'
GOAL_ITEM_CLASS = 'http://example.org/Rug'  # ← Just the class!
MY_ROLE = "Buyer"  # ← Still hardcoded
```

### Code
```python
adapter = HypermediaMetaAdapter(
    name=NAME,
    base_uri=BASE_URL,
    goal_artifact_class=GOAL_ITEM_CLASS,  # ← Only knows type!
    auto_discover_workspace=True,  # ← Discovers workspace + artifact
    capabilities={"Pay"}
)

# Workspace and artifact discovered automatically!
# But role still hardcoded
system_dict = {
    "protocol": protocol,
    "roles": {"Buyer": NAME}  # ← Still hardcoded
}
```

### Improvements
- ✅ Only needs semantic type, not exact URI
- ✅ True hypermedia navigation
- ✅ Works with multiple artifacts of same type
- ❌ Still hardcodes role name

**Autonomy Score: ⭐️⭐️⭐️ (3/5)**

---

## Level 4: Full Autonomy (Class Discovery + Role Reasoning)

**Agent knows:** Base URL + artifact class + goal + capabilities
**Agent discovers:** Workspace + artifact URI + which role to take

### Configuration
```python
NAME = "BuyerAgent"
BASE_URL = 'http://localhost:8080/'
GOAL_ITEM_CLASS = 'http://example.org/Rug'  # Semantic type
GOAL_TYPE = 'http://purl.org/goodrelations/v1#Buy'  # What I want to do
# No role name needed!
```

### Code
```python
adapter = HypermediaMetaAdapter(
    name=NAME,

    # Discovery
    base_uri=BASE_URL,
    goal_artifact_class=GOAL_ITEM_CLASS,
    auto_discover_workspace=True,

    # Role Reasoning (NEW!)
    goal_type=GOAL_TYPE,  # ← I want to acquire/buy
    capabilities={"Pay"},
    auto_reason_role=True  # ← Reasons role automatically!
)

# Workspace and artifact discovered automatically
protocol = adapter.discover_protocol_for_goal(adapter.goal_artifact_uri)

# Role reasoned automatically!
my_role = adapter.reason_my_role(protocol)  # ← Returns "Buyer"

system_dict = {
    "protocol": protocol,
    "roles": {my_role: NAME}  # ← Using reasoned role!
}
```

### Improvements
- ✅ No hardcoded URIs
- ✅ No hardcoded role names
- ✅ Reasons role from goal + capabilities
- ✅ Fully autonomous navigation and reasoning
- ✅ Same code works for different goals (buy vs sell)

**Autonomy Score: ⭐️⭐️⭐️⭐️⭐️ (5/5)**

---

## Comparison Table

| Aspect | Level 1 | Level 2 | Level 3 | Level 4 |
|--------|---------|---------|---------|---------|
| **Workspace** | Hardcoded | Discovered | Discovered | Discovered |
| **Artifact URI** | Hardcoded | Hardcoded | Discovered | Discovered |
| **Role** | Hardcoded | Hardcoded | Hardcoded | **Reasoned** |
| **Agent Knows** | Path + URI + Role | Base + URI + Role | Base + Class + Role | Base + Class + Goal |
| **Lines of Config** | 4 | 3 | 3 | 3 |
| **Flexibility** | None | Low | Medium | **High** |
| **Reusability** | None | Low | Medium | **High** |
| **Autonomy** | ⭐️ | ⭐️⭐️ | ⭐️⭐️⭐️ | ⭐️⭐️⭐️⭐️⭐️ |

---

## Code Comparison

### Agent Initialization

```python
# Level 1: Hardcoded
adapter = HypermediaMetaAdapter(
    workspace_uri='http://localhost:8080/workspaces/bazaar/',  # Hardcoded
    capabilities={"Pay"}
)

# Level 2: URI-Based Discovery
adapter = HypermediaMetaAdapter(
    base_uri='http://localhost:8080/',
    goal_artifact_uri='http://.../rug#artifact',  # Still full URI
    auto_discover_workspace=True,
    capabilities={"Pay"}
)

# Level 3: Class-Based Discovery
adapter = HypermediaMetaAdapter(
    base_uri='http://localhost:8080/',
    goal_artifact_class='http://example.org/Rug',  # Just class!
    auto_discover_workspace=True,
    capabilities={"Pay"}
)

# Level 4: Full Autonomy
adapter = HypermediaMetaAdapter(
    base_uri='http://localhost:8080/',
    goal_artifact_class='http://example.org/Rug',  # Just class!
    goal_type='http://purl.org/goodrelations/v1#Buy',  # Goal!
    auto_discover_workspace=True,
    auto_reason_role=True,  # Reasons role!
    capabilities={"Pay"}
)
```

### System Formation

```python
# Level 1-3: Hardcoded role
system_dict = {
    "protocol": protocol,
    "roles": {"Buyer": NAME}  # ← Developer decided this
}

# Level 4: Reasoned role
my_role = adapter.reason_my_role(protocol)  # ← Agent decided this!
system_dict = {
    "protocol": protocol,
    "roles": {my_role: NAME}
}
```

---

## Real-World Analogy

### Level 1: Hardcoded
*"Go to 123 Main Street, buy the red rug from Bob in the buyer role"*
- Exact address, exact item, exact person, exact role
- What if the store moves? What if Bob leaves? Script breaks.

### Level 2: URI-Based Discovery
*"Start downtown, find 123 Main Street, buy the red rug from Bob in the buyer role"*
- Can navigate to address from starting point
- Still need exact address, item, person, and role

### Level 3: Class-Based Discovery
*"Start downtown, find any rug, buy it from Bob in the buyer role"*
- Can navigate and find any matching item
- Still need to be told which role to play

### Level 4: Full Autonomy
*"Start downtown, find any rug because I want to buy something (gr:Buy) and I can pay for it"*
- Navigates autonomously
- Finds matching items by type
- **Figures out I should be a buyer based on my goal and capabilities**
- True autonomy!

---

## Benefits of Full Autonomy

### 1. Flexibility
Same agent code with different goals:
```python
# As buyer
buyer = Agent(goal_type=gr:Buy, capabilities={"Pay"})
buyer.reason_my_role(protocol)  # → "Buyer"

# As seller
seller = Agent(goal_type=gr:Sell, capabilities={"Give"})
seller.reason_my_role(protocol)  # → "Seller"
```

### 2. Protocol Agnostic
Works across different protocols:
```python
agent = Agent(goal_type=gr:Buy, capabilities={"Pay"})

# Buy protocol
agent.reason_my_role(buy_protocol)  # → "Buyer"

# Auction protocol
agent.reason_my_role(auction_protocol)  # → "Bidder"

# Lease protocol
agent.reason_my_role(lease_protocol)  # → "Lessee"
```

### 3. Self-Validation
Agent won't take incompatible roles:
```python
agent = Agent(goal_type=gr:Buy, capabilities={"Give"})  # Mismatch!
role = agent.reason_my_role(protocol)  # → None (can't be Buyer without Pay)
```

### 4. Semantic Understanding
Agent reasons based on meaning:
- **Goal** = What I want to achieve (Buy, Sell, Lease)
- **Role** = How to achieve it in this protocol (Buyer, Seller)
- **Capabilities** = What I can do (Pay, Give)

### 5. True HATEOAS
Hypermedia As The Engine Of Application State:
- Navigate by links ✓
- Discover by semantics ✓
- Reason by meaning ✓

---

## Migration Path

### Step 1: Add Class-Based Discovery
```python
# Before
workspace_uri='http://localhost:8080/workspaces/bazaar/'

# After
base_uri='http://localhost:8080/',
goal_artifact_class='http://example.org/Rug',
auto_discover_workspace=True
```

### Step 2: Add Role Reasoning
```python
# Add goal type
goal_type='http://purl.org/goodrelations/v1#Buy',
auto_reason_role=True

# Update system formation
my_role = adapter.reason_my_role(protocol)
system_dict = {"protocol": protocol, "roles": {my_role: NAME}}
```

### Step 3: Remove Hardcoded Values
```python
# Remove
WORKSPACE = 'http://...'  # Not needed
GOAL_ITEM = 'http://...'  # Not needed
MY_ROLE = "Buyer"  # Not needed

# Keep
GOAL_ITEM_CLASS = 'http://example.org/Rug'  # Semantic type
GOAL_TYPE = 'http://purl.org/goodrelations/v1#Buy'  # Goal
```

---

## Files

### Examples of Each Level

1. **Level 1:** `buyer_agent_refactored.py` (original)
2. **Level 2:** `buyer_agent_with_discovery.py` (URI-based)
3. **Level 3:** `buyer_agent_auto_discovery.py` (class-based)
4. **Level 4:** `buyer_agent_with_role_reasoning.py` (full autonomy)

### Try Them

```bash
# Start environment
cd HypermediaInteractionProtocols
./start.sh

# In another terminal
cd agents

# Level 4: Full autonomy
python buyer_agent_with_role_reasoning.py
```

---

## Summary

**Evolution:**
1. **Hardcoded** → Everything specified
2. **URI Discovery** → Find workspace from base + URI
3. **Class Discovery** → Find workspace + artifact from base + class
4. **Role Reasoning** → Find workspace + artifact + role from base + class + goal

**Result:**
- 🎯 Agents reason about their roles
- 🧭 Agents navigate by semantics
- 🤖 True autonomy achieved
- ✨ HATEOAS principles fully realized

**Agent only needs to know:**
- Where to start (base URI)
- What they want (artifact class + goal type)
- What they can do (capabilities)

**Everything else is discovered and reasoned autonomously!**

---

*This progression demonstrates the full potential of semantic hypermedia for autonomous multi-agent systems.*
