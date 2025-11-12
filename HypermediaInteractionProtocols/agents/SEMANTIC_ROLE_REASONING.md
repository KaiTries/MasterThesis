# Semantic Role Reasoning Design

## Problem Statement

Currently, agents are hardcoded to know which role they should play:

```python
system_dict = {
    "protocol": protocol,
    "roles": {
        "Buyer": NAME,  # ← Hardcoded!
        "Seller": None
    }
}
```

**This is not autonomous!** The agent should reason about which role to take based on:
1. Its **goal** (acquire vs provide an artifact)
2. Its **capabilities** (what messages it can send)
3. The **protocol's role semantics** (what each role does and requires)

## Desired Behavior

```python
# Agent only knows its goal and capabilities
adapter = HypermediaMetaAdapter(
    name="BuyerAgent",
    goal_type="http://purl.org/goodrelations/v1#Buy",  # I want to BUY
    goal_artifact_class="http://example.org/Rug",
    capabilities={"Pay"},
    # No role specified!
)

# Agent automatically reasons:
# - Protocol has Buyer and Seller roles
# - Buyer role has goal gr:Buy (matches my goal!)
# - Buyer role requires Pay capability (I have it!)
# - Therefore, I should take the Buyer role

my_role = adapter.reason_role_for_protocol(protocol)
# Returns: "Buyer"
```

## Semantic Model

### 1. Goal Types (GoodRelations Ontology)

Use existing GoodRelations terms:

```turtle
@prefix gr: <http://purl.org/goodrelations/v1#> .

# Agent goals
gr:Buy      # "I want to acquire this artifact"
gr:Sell     # "I want to provide this artifact"
gr:Lease    # "I want to lease this artifact"
gr:Repair   # "I want to repair this artifact"
```

### 2. Role Semantics

Extend BSPL protocol descriptions with semantic role information:

```turtle
@prefix bspl: <https://purl.org/hmas/bspl/> .
@prefix gr: <http://purl.org/goodrelations/v1#> .
@prefix ex: <http://example.org/> .

<protocols/buy_protocol#BuyerRole> a bspl:Role ;
  bspl:roleName "Buyer" ;

  # What goal does this role fulfill?
  bspl:hasGoal gr:Buy ;  # This role is for buying/acquiring

  # What capabilities are required?
  bspl:requiresCapability "Pay" ;  # Must be able to send Pay message

  # What does this role do?
  bspl:sendsMessage "Pay" ;        # Sends payment
  bspl:receivesMessage "Give" ;    # Receives item

  # Textual description for humans
  rdfs:comment "Acquires items by paying for them" .

<protocols/buy_protocol#SellerRole> a bspl:Role ;
  bspl:roleName "Seller" ;

  # What goal does this role fulfill?
  bspl:hasGoal gr:Sell ;  # This role is for selling/providing

  # What capabilities are required?
  bspl:requiresCapability "Give" ;  # Must be able to send Give message

  # What does this role do?
  bspl:sendsMessage "Give" ;        # Delivers item
  bspl:receivesMessage "Pay" ;      # Receives payment

  # Textual description
  rdfs:comment "Provides items in exchange for payment" .
```

### 3. Agent Configuration

Agent specifies its goal and capabilities:

```python
adapter = HypermediaMetaAdapter(
    name="BuyerAgent",

    # Goal: What do I want to do?
    goal_type="http://purl.org/goodrelations/v1#Buy",

    # Target: What artifact?
    goal_artifact_class="http://example.org/Rug",

    # Capabilities: What can I do?
    capabilities={"Pay"},

    # Auto-reasoning enabled
    auto_reason_role=True  # ← New!
)
```

## Reasoning Algorithm

### Step 1: Discover Protocol

```python
protocol = adapter.discover_protocol_for_goal(artifact_uri)
```

### Step 2: Get Role Semantics

Query protocol for roles with their semantics:

```sparql
PREFIX bspl: <https://purl.org/hmas/bspl/>
PREFIX gr: <http://purl.org/goodrelations/v1#>

SELECT ?roleName ?goal ?capability ?sends ?receives WHERE {
  ?role a bspl:Role ;
        bspl:roleName ?roleName ;
        bspl:hasGoal ?goal ;
        bspl:requiresCapability ?capability ;
        bspl:sendsMessage ?sends ;
        bspl:receivesMessage ?receives .
}
```

Results:
```
Buyer:  goal=gr:Buy,  capability=Pay, sends=Pay, receives=Give
Seller: goal=gr:Sell, capability=Give, sends=Give, receives=Pay
```

### Step 3: Score Each Role

For each role, calculate compatibility score:

```python
def score_role(agent, role_semantics):
    score = 0

    # Goal match (most important - weight: 10)
    if agent.goal_type == role_semantics.goal:
        score += 10

    # Capability match (important - weight: 5)
    if role_semantics.required_capability in agent.capabilities:
        score += 5

    # Additional capabilities (nice to have - weight: 1)
    for msg in role_semantics.sends_messages:
        if msg in agent.capabilities:
            score += 1

    return score
```

Example:
```
Agent: goal=gr:Buy, capabilities={Pay}

Buyer role:  goal=gr:Buy (✓+10), requires=Pay (✓+5), sends=Pay (✓+1) = 16
Seller role: goal=gr:Sell (✗+0), requires=Give (✗+0), sends=Give (✗+0) = 0

Winner: Buyer role (score: 16)
```

### Step 4: Select Best Role

```python
best_role = max(roles, key=lambda r: score_role(agent, r))
return best_role.name  # "Buyer"
```

## Implementation Plan

### 1. Extend Protocol Metadata

File: `env/conf/metadata/buy_protocol_semantics.ttl`

```turtle
@prefix bspl: <https://purl.org/hmas/bspl/> .
@prefix gr: <http://purl.org/goodrelations/v1#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

<http://localhost:8005/protocols/buy_protocol#BuyerRole>
    a bspl:Role ;
    bspl:roleName "Buyer" ;
    bspl:hasGoal gr:Buy ;
    bspl:requiresCapability "Pay" ;
    bspl:sendsMessage "Pay" ;
    bspl:receivesMessage "Give" ;
    rdfs:comment "Buyer acquires items by paying" .

<http://localhost:8005/protocols/buy_protocol#SellerRole>
    a bspl:Role ;
    bspl:roleName "Seller" ;
    bspl:hasGoal gr:Sell ;
    bspl:requiresCapability "Give" ;
    bspl:sendsMessage "Give" ;
    bspl:receivesMessage "Pay" ;
    rdfs:comment "Seller provides items for payment" .
```

### 2. Add to HypermediaTools.py

```python
def get_role_semantics(protocol_uri: str) -> dict:
    """
    Get semantic information about protocol roles.

    Returns dict like:
    {
        "Buyer": {
            "goal": "http://purl.org/goodrelations/v1#Buy",
            "required_capability": "Pay",
            "sends": ["Pay"],
            "receives": ["Give"]
        },
        "Seller": { ... }
    }
    """

def reason_role_for_goal(
    protocol_uri: str,
    agent_goal: str,
    agent_capabilities: set
) -> Optional[str]:
    """
    Reason which role the agent should take.

    Args:
        protocol_uri: URI of the protocol
        agent_goal: Agent's goal (e.g., gr:Buy)
        agent_capabilities: Agent's capabilities (e.g., {"Pay"})

    Returns:
        Role name (e.g., "Buyer") or None if no match
    """
```

### 3. Extend HypermediaMetaAdapter

```python
class HypermediaMetaAdapter(MetaAdapter):
    def __init__(
        self,
        goal_type: str = None,  # ← New: gr:Buy, gr:Sell, etc.
        auto_reason_role: bool = True,  # ← New: automatic role reasoning
        ...
    ):
        self.goal_type = goal_type
        self.auto_reason_role = auto_reason_role
        ...

    def reason_my_role(self, protocol: Protocol) -> Optional[str]:
        """
        Reason which role I should take in this protocol.

        Returns:
            Role name or None
        """
        if not self.goal_type:
            self.warning("Cannot reason role: no goal_type specified")
            return None

        role = HypermediaTools.reason_role_for_goal(
            protocol.uri,
            self.goal_type,
            self.capabilities
        )

        if role:
            self.info(f"Reasoned my role: {role} (goal={self.goal_type})")
        else:
            self.warning("Could not reason appropriate role")

        return role
```

### 4. Update Agent Workflow

```python
# Old way (hardcoded)
system_dict = {
    "protocol": protocol,
    "roles": {
        "Buyer": NAME,  # ← Hardcoded
        "Seller": None
    }
}

# New way (reasoned)
my_role = adapter.reason_my_role(protocol)
system_dict = {
    "protocol": protocol,
    "roles": {
        my_role: NAME,  # ← Automatically determined!
        # Other roles filled through negotiation
    }
}
```

## Benefits

### 1. True Autonomy
Agent doesn't need to know the role name, only its goal and capabilities

### 2. Protocol Agnostic
Same agent can participate in different protocols:
- Buy protocol → Takes Buyer role (goal=Buy)
- Auction protocol → Takes Bidder role (goal=Buy)
- Lease protocol → Takes Lessee role (goal=Lease)

### 3. Flexible Goal Switching
Same agent code can be reused:
```python
# As buyer
buyer = Agent(goal_type=gr:Buy, capabilities={"Pay"})
# → Automatically takes Buyer role

# As seller
seller = Agent(goal_type=gr:Sell, capabilities={"Give"})
# → Automatically takes Seller role
```

### 4. Capability Validation
Agent won't try to take roles it can't fulfill:
```python
agent = Agent(goal_type=gr:Buy, capabilities={"Give"})
# → Warns: "Want to buy but only can Give, cannot take Buyer role"
```

## Example Scenario

### Scenario 1: Buyer Agent

```python
adapter = HypermediaMetaAdapter(
    name="ShoppingAgent",
    goal_type="http://purl.org/goodrelations/v1#Buy",
    goal_artifact_class="http://example.org/Rug",
    capabilities={"Pay"},
    auto_reason_role=True
)

# Discovery phase
workspace, artifact = adapter.discover_workspace_by_class(...)
protocol = adapter.discover_protocol_for_goal(artifact)

# Role reasoning
my_role = adapter.reason_my_role(protocol)
print(f"I should be: {my_role}")  # "Buyer"

# System formation
system_dict = {"protocol": protocol, "roles": {my_role: adapter.name}}
adapter.propose_system("PurchaseSystem", system_dict)
```

### Scenario 2: Seller Agent

```python
adapter = HypermediaMetaAdapter(
    name="ShopAgent",
    goal_type="http://purl.org/goodrelations/v1#Sell",
    goal_artifact_class="http://example.org/Rug",
    capabilities={"Give"},
    auto_reason_role=True
)

# Same discovery process...
my_role = adapter.reason_my_role(protocol)
print(f"I should be: {my_role}")  # "Seller"
```

### Scenario 3: Multi-Protocol Agent

```python
# Agent that can both buy and sell
adapter = HypermediaMetaAdapter(
    name="TradingAgent",
    # Goal determined at runtime
    capabilities={"Pay", "Give"},  # Can do both!
    auto_reason_role=True
)

# When wanting to acquire
adapter.goal_type = gr:Buy
my_role = adapter.reason_my_role(buy_protocol)  # → "Buyer"

# When wanting to provide
adapter.goal_type = gr:Sell
my_role = adapter.reason_my_role(sell_protocol)  # → "Seller"
```

## Advanced: Multi-Criteria Reasoning

For complex scenarios, extend reasoning with additional factors:

```python
def score_role_advanced(agent, role, context):
    score = 0

    # Goal alignment (weight: 10)
    if agent.goal_type == role.goal:
        score += 10

    # Capability match (weight: 5)
    if role.required_capability in agent.capabilities:
        score += 5

    # Economic factors (weight: 3)
    if context.price <= agent.budget:
        score += 3

    # Trust/reputation (weight: 2)
    if context.counterparty_reputation > 0.8:
        score += 2

    # Temporal constraints (weight: 1)
    if context.deadline_compatible:
        score += 1

    return score
```

## Integration with Existing Features

This builds on class-based discovery:

```python
# Complete autonomous agent
adapter = HypermediaMetaAdapter(
    name="AutonomousAgent",

    # Discovery by class (implemented)
    base_uri="http://localhost:8080/",
    goal_artifact_class="http://example.org/Rug",
    auto_discover_workspace=True,

    # Role reasoning (new)
    goal_type="http://purl.org/goodrelations/v1#Buy",
    auto_reason_role=True,

    # Capabilities
    capabilities={"Pay"}
)

# Everything automatic:
# 1. Discovers workspace with rug
# 2. Discovers protocol for rug
# 3. Reasons it should be Buyer
# 4. Discovers other agents
# 5. Forms system with reasoned role
# 6. Executes protocol
```

## Summary

**Current state**: Agent hardcodes role
**Proposed state**: Agent reasons role from goal + capabilities + protocol semantics

**Key components**:
1. Semantic role descriptions in protocol metadata
2. Goal types (gr:Buy, gr:Sell, etc.)
3. Role reasoning algorithm (goal matching + capability matching)
4. Integration with HypermediaMetaAdapter

**Result**: Truly autonomous agents that adapt to different protocols and scenarios based on their goals and capabilities.
