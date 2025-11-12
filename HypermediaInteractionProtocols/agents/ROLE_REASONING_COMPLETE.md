# Semantic Role Reasoning - Implementation Complete

## Overview

Implemented **semantic role reasoning** - agents can now automatically determine which role they should take in a protocol based on their **goals** and **capabilities**, without hardcoding role names.

**Before:**
```python
# Agent hardcodes that it should be Buyer
system_dict = {"protocol": protocol, "roles": {"Buyer": NAME, "Seller": None}}
```

**After:**
```python
# Agent reasons its role from goal + capabilities
my_role = adapter.reason_my_role(protocol)  # Returns: "Buyer"
system_dict = {"protocol": protocol, "roles": {my_role: NAME}}
```

## How It Works

### 1. Agent Specifies Goal

Agents declare their goal using GoodRelations ontology terms:

```python
adapter = HypermediaMetaAdapter(
    name="BuyerAgent",
    goal_type="http://purl.org/goodrelations/v1#Buy",  # I want to acquire/buy
    goal_artifact_class="http://example.org/Rug",
    capabilities={"Pay"}
)
```

**Goal types:**
- `gr:Buy` - Agent wants to acquire/purchase
- `gr:Sell` - Agent wants to provide/sell
- `gr:Lease` - Agent wants to lease
- (extensible with custom goals)

### 2. Protocol Provides Role Semantics

Protocols now include semantic role descriptions:

```turtle
<http://localhost:8005/protocols/buy_protocol#BuyerRole>
    a bspl:Role ;
    bspl:roleName "Buyer" ;
    bspl:hasGoal gr:Buy ;                    # This role is for buying
    bspl:requiresCapability "Pay" ;          # Requires Pay capability
    bspl:sendsMessage "Pay" ;
    bspl:receivesMessage "Give" .

<http://localhost:8005/protocols/buy_protocol#SellerRole>
    a bspl:Role ;
    bspl:roleName "Seller" ;
    bspl:hasGoal gr:Sell ;                   # This role is for selling
    bspl:requiresCapability "Give" ;         # Requires Give capability
    bspl:sendsMessage "Give" ;
    bspl:receivesMessage "Pay" .
```

### 3. Reasoning Algorithm

The adapter scores each role based on compatibility:

```
Score = (Goal Match × 10) + (Capability Match × 5) + (Additional Capabilities × 1)

Example:
Agent: goal=gr:Buy, capabilities={Pay}

Buyer role:
  - Goal matches (gr:Buy) → +10
  - Has required capability (Pay) → +5
  - Can send Pay message → +1
  - Total: 16 ✓

Seller role:
  - Goal mismatch (gr:Sell) → +0
  - Missing required capability (Give) → incompatible
  - Total: 0 ✗

Result: Buyer role (score 16)
```

### 4. Automatic Role Selection

```python
protocol = adapter.discover_protocol_for_goal(artifact_uri)
my_role = adapter.reason_my_role(protocol)
# Returns: "Buyer" (automatically determined!)
```

## Implementation Details

### Files Modified

1. **env/protocols/protocol.py**
   - Added role semantics to `bspl_rdf`
   - Includes goal, required capabilities, and message patterns for each role

2. **HypermediaTools.py** (+220 lines)
   - `get_role_semantics()` - Parse role descriptions from protocol
   - `score_role_match()` - Calculate compatibility score
   - `reason_role_for_goal()` - Select best matching role

3. **HypermediaMetaAdapter.py**
   - Added `goal_type` parameter
   - Added `auto_reason_role` parameter (default: True)
   - Added `reason_my_role()` method

### Files Created

1. **env/conf/metadata/buy_protocol_role_semantics.ttl**
   - Standalone role semantics file (reference)

2. **test_role_reasoning.py**
   - Comprehensive test suite
   - Tests buyer reasoning, seller reasoning, capability mismatch

3. **SEMANTIC_ROLE_REASONING.md**
   - Complete design documentation
   - Examples and use cases

4. **ROLE_REASONING_COMPLETE.md** (this file)
   - Implementation summary

## Usage Examples

### Example 1: Autonomous Buyer

```python
from HypermediaMetaAdapter import HypermediaMetaAdapter

adapter = HypermediaMetaAdapter(
    name="BuyerAgent",

    # Discovery
    base_uri="http://localhost:8080/",
    goal_artifact_class="http://example.org/Rug",
    auto_discover_workspace=True,

    # Role Reasoning (NEW!)
    goal_type="http://purl.org/goodrelations/v1#Buy",  # I want to buy
    capabilities={"Pay"},
    auto_reason_role=True,

    auto_join=True
)

# Agent discovers workspace + artifact
# Agent discovers protocol
protocol = adapter.discover_protocol_for_goal(adapter.goal_artifact_uri)

# Agent reasons its role automatically!
my_role = adapter.reason_my_role(protocol)
print(f"I should be: {my_role}")  # "Buyer"

# Use reasoned role in system formation
system_dict = {
    "protocol": protocol,
    "roles": {my_role: adapter.name}  # ← Automatic!
}
```

### Example 2: Flexible Agent (Can Be Buyer OR Seller)

```python
# Agent with both capabilities
adapter = HypermediaMetaAdapter(
    name="TradingAgent",
    capabilities={"Pay", "Give"},  # Can do both!
    auto_reason_role=True
)

# When wanting to acquire
adapter.goal_type = "http://purl.org/goodrelations/v1#Buy"
my_role = adapter.reason_my_role(protocol)  # → "Buyer"

# When wanting to sell
adapter.goal_type = "http://purl.org/goodrelations/v1#Sell"
my_role = adapter.reason_my_role(protocol)  # → "Seller"
```

### Example 3: Multi-Protocol Agent

```python
# Same agent can participate in different protocols
adapter = HypermediaMetaAdapter(
    goal_type="http://purl.org/goodrelations/v1#Buy",
    capabilities={"Pay"}
)

# Buy protocol → Buyer role
buy_protocol = discover_protocol("Buy")
role1 = adapter.reason_my_role(buy_protocol)  # "Buyer"

# Auction protocol → Bidder role (if it has similar semantics)
auction_protocol = discover_protocol("Auction")
role2 = adapter.reason_my_role(auction_protocol)  # "Bidder"
```

## Testing

Run the test suite:

```bash
cd agents
python test_role_reasoning.py
```

Expected output:
```
=== Role Reasoning ===
Protocol: http://localhost:8005/protocol_descriptions/buy_protocol
Agent goal: http://purl.org/goodrelations/v1#Buy
Agent capabilities: {'Pay'}

Found 2 role(s) with semantics: ['Buyer', 'Seller']

Evaluating Buyer:
  Buyer: goal matches (http://purl.org/goodrelations/v1#Buy) +10
  Buyer: has required capability (Pay) +5
  Buyer: can send Pay +1
  Buyer: total score = 16

Evaluating Seller:
  Seller: goal mismatch (want gr:Buy, role has gr:Sell)
  Seller: missing required capability (Give) - incompatible
  Seller: total score = 0

✓ Best role: Buyer (score: 16)

✓ PASS: Buyer Role Reasoning
```

## Architecture Benefits

### 1. True Autonomy
Agents don't need to know role names, only:
- What they want to do (goal)
- What they can do (capabilities)

### 2. Protocol Agnostic
Same agent code works across different protocols:
- Buy protocol → Buyer role
- Auction protocol → Bidder role
- Lease protocol → Lessee role

### 3. Goal Flexibility
Agent behavior determined by goal, not hardcoded logic:
```python
# Same agent class, different goals
buyer = Agent(goal=gr:Buy)   → Takes Buyer role
seller = Agent(goal=gr:Sell) → Takes Seller role
```

### 4. Capability Validation
Agent won't take roles it can't fulfill:
```python
agent = Agent(goal=gr:Buy, capabilities={"Give"})  # Mismatch!
role = agent.reason_my_role(protocol)  # Returns None (can't be Buyer without Pay)
```

### 5. Self-Describing Protocols
Protocols describe what each role does and requires:
- Explicit goal alignment
- Clear capability requirements
- Message sending/receiving patterns

## Integration with Previous Features

Semantic role reasoning builds on class-based discovery:

```python
# Complete autonomous agent
adapter = HypermediaMetaAdapter(
    name="FullyAutonomousAgent",

    # 1. Class-based Discovery (finds workspace + artifact)
    base_uri="http://localhost:8080/",
    goal_artifact_class="http://example.org/Rug",
    auto_discover_workspace=True,

    # 2. Role Reasoning (determines which role to take)
    goal_type="http://purl.org/goodrelations/v1#Buy",
    capabilities={"Pay"},
    auto_reason_role=True,

    auto_join=True
)

# Agent autonomously:
# ✓ Discovers workspace containing rug
# ✓ Discovers Buy protocol for rug
# ✓ Reasons it should be Buyer (goal=Buy, can Pay)
# ✓ Discovers other agents
# ✓ Forms system with reasoned role
# ✓ Executes protocol
```

## Autonomy Levels Comparison

| Level | Agent Knows | Agent Discovers | Autonomous? |
|-------|-------------|-----------------|-------------|
| **Hardcoded** | Full URI + Role name | Nothing | ⭐️ Low |
| **URI Discovery** | Base + Artifact URI + Role | Workspace | ⭐️⭐️ Medium |
| **Class Discovery** | Base + Class + Role | Workspace + Artifact | ⭐️⭐️⭐️ High |
| **+Role Reasoning** | **Base + Class + Goal** | **Workspace + Artifact + Role** | **⭐️⭐️⭐️⭐️ Very High** |

## Future Enhancements

### 1. Multi-Role Protocols
Handle protocols where one agent can take multiple roles:
```python
roles = adapter.reason_all_compatible_roles(protocol)
# Returns: ["Buyer", "Inspector"]  # Agent can do both
```

### 2. Dynamic Goal Switching
Agent adapts role based on context:
```python
if market_price < my_valuation:
    adapter.goal_type = gr:Buy
else:
    adapter.goal_type = gr:Sell
```

### 3. Negotiated Goals
Agents negotiate not just roles, but goals:
```python
# "I can buy OR sell, what do you need?"
adapter.offer_flexible_participation(protocol)
```

### 4. Learning from Experience
Track which goal/role combinations work best:
```python
# After successful transaction
adapter.record_success(goal=gr:Buy, role="Buyer", protocol="Buy")
# Use for future role selection
```

## Error Handling

### No Goal Specified
```python
adapter = HypermediaMetaAdapter(capabilities={"Pay"})
role = adapter.reason_my_role(protocol)
# Logs: "Cannot reason role: no goal_type specified"
# Returns: None
```

### Capability Mismatch
```python
adapter = HypermediaMetaAdapter(
    goal_type=gr:Buy,
    capabilities={"Give"}  # Wrong!
)
role = adapter.reason_my_role(protocol)
# Logs: "Buyer: missing required capability (Pay) - incompatible"
# Returns: None (no compatible role)
```

### No Role Semantics Available
```python
# If protocol doesn't have role semantics
role = adapter.reason_my_role(old_protocol)
# Logs: "No role semantics found for protocol"
# Returns: None
```

## Best Practices

1. **Always specify goal_type** when using role reasoning
2. **Ensure capabilities match your goal** (Buy→Pay, Sell→Give)
3. **Handle None return** from reason_my_role (fallback to manual role selection)
4. **Use meaningful goals** from established ontologies (GoodRelations, etc.)
5. **Document custom goals** if extending beyond gr:Buy/gr:Sell

## Status

✅ **Complete and Tested**

- ✅ Role semantics in protocol metadata
- ✅ Reasoning algorithm implemented
- ✅ Integrated into HypermediaMetaAdapter
- ✅ Test suite passing
- ✅ Documentation complete

## Next Steps for Users

1. **Define your agent's goal:**
   ```python
   goal_type="http://purl.org/goodrelations/v1#Buy"
   ```

2. **Ensure capabilities match:**
   ```python
   capabilities={"Pay"}  # Buyer capability
   ```

3. **Let the agent reason:**
   ```python
   my_role = adapter.reason_my_role(protocol)
   ```

4. **Use reasoned role in system:**
   ```python
   system_dict = {"protocol": protocol, "roles": {my_role: adapter.name}}
   ```

---

**Date:** 2025-11-12
**Feature:** Semantic Role Reasoning
**Status:** Production Ready ✅

Agents are now truly autonomous - they discover workspaces by class, discover protocols, and reason about their roles based on goals and capabilities!
