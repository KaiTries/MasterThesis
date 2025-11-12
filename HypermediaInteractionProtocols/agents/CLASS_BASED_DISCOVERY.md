# Class-Based Artifact Discovery

## Overview

Class-based discovery is the **most autonomous form** of hypermedia-driven agent discovery. Instead of hardcoding exact artifact URIs, agents only need to know:
1. A base URI to start from (e.g., `http://localhost:8080/`)
2. The **semantic class** of what they're looking for (e.g., `ex:Rug`)

Everything else—workspace location, exact artifact URI, protocols, other agents—is discovered through hypermedia traversal and semantic queries.

## Why Class-Based Discovery?

### Traditional Approach (Hardcoded URI)
```python
# Agent needs to know the exact path
GOAL_ITEM = 'http://localhost:8080/workspaces/bazaar/artifacts/rug#artifact'
```
**Problems:**
- Brittle: Breaks if artifact moves to different workspace
- Not scalable: Requires prior knowledge of workspace structure
- Defeats hypermedia principles: Agent should navigate, not know paths

### URI-Based Discovery (Better)
```python
# Agent knows the URI but discovers which workspace contains it
BASE_URL = 'http://localhost:8080/'
GOAL_ITEM = 'http://localhost:8080/workspaces/bazaar/artifacts/rug#artifact'
```
**Better:** Discovers workspace dynamically
**But:** Still needs to know the complete artifact URI

### Class-Based Discovery (Most Autonomous!)
```python
# Agent only knows the semantic type
BASE_URL = 'http://localhost:8080/'
GOAL_ITEM_CLASS = 'http://example.org/Rug'  # Just the class!
```
**Benefits:**
- ✅ True autonomy: Agent navigates by semantics
- ✅ Flexible: Works even if artifact moves
- ✅ Realistic: Models real-world scenarios (e.g., "find me a coffee shop")
- ✅ Hypermedia-native: Follows HATEOAS principles completely

## How It Works

### 1. Semantic Metadata

First, artifacts are typed with RDF classes in their metadata:

```turtle
# env/conf/metadata/rug.ttl
@prefix ex: <http://example.org/> .

<workspaces/bazaar/artifacts/rug#artifact>
    a td:Thing,
      hmas:Artifact,
      gr:ActualProductOrServiceInstance,
      ex:Rug .  # ← Semantic class!
```

### 2. Discovery Algorithm

The agent performs a depth-first search through the workspace hierarchy:

```
1. Start at base URI (http://localhost:8080/)
2. Query: "What workspaces exist here?"
3. For each workspace:
   a. Query: "What artifacts of class ex:Rug exist?"
   b. If found: Return (workspace_uri, artifact_uri)
   c. If not: Recursively search sub-workspaces
4. Continue until artifact found or max depth reached
```

### 3. Implementation

**In HypermediaTools.py:**

Three new functions power class-based discovery:

```python
def get_artifacts_by_class(workspace_uri: str, artifact_class: str) -> list[str]:
    """
    Query workspace for artifacts of a specific RDF class.

    Implementation note: The /artifacts/ collection endpoint doesn't include
    full type information, so this function:
    1. Gets all artifacts from the collection
    2. Fetches each individual artifact to check its full types
    3. Returns only those matching the requested class
    """

def find_workspace_containing_artifact_class(
    base_uri: str,
    artifact_class: str,
    max_depth: int = 5
) -> tuple[Optional[str], Optional[str]]:
    """Recursively search workspaces for artifact of given class."""

def discover_workspace_by_artifact_class(
    base_uri: str,
    artifact_class: str
) -> tuple[Optional[str], Optional[str]]:
    """Main entry point - returns (workspace_uri, artifact_uri)."""
```

**In HypermediaMetaAdapter:**

Added support for automatic class-based discovery:

```python
def __init__(
    self,
    name: str,
    base_uri: str = None,
    goal_artifact_class: str = None,  # ← New parameter!
    auto_discover_workspace: bool = False,
    ...
):
    # If class-based discovery enabled
    if auto_discover_workspace and goal_artifact_class:
        workspace, artifact = self.discover_workspace_by_class(
            base_uri,
            goal_artifact_class
        )
        self.workspace_uri = workspace
        self.goal_artifact_uri = artifact  # Discovered!
```

## Usage Examples

### Automatic Class-Based Discovery

The simplest approach - everything happens automatically:

```python
from HypermediaMetaAdapter import HypermediaMetaAdapter

adapter = HypermediaMetaAdapter(
    name="BuyerAgent",
    base_uri="http://localhost:8080/",           # Start here
    goal_artifact_class="http://example.org/Rug", # Find this class
    web_id="http://localhost:8011",
    adapter_endpoint="8011",
    capabilities={"Pay"},
    auto_discover_workspace=True,  # ← Automatic!
    auto_join=True                 # ← Join automatically too!
)

# At this point:
# - Workspace discovered and joined
# - Artifact URI discovered
print(f"Workspace: {adapter.workspace_uri}")
print(f"Artifact: {adapter.goal_artifact_uri}")
```

### Manual Class-Based Discovery

For more control or educational purposes:

```python
adapter = HypermediaMetaAdapter(
    name="BuyerAgent",
    base_uri="http://localhost:8080/",
    goal_artifact_class="http://example.org/Rug",
    web_id="http://localhost:8011",
    adapter_endpoint="8011",
    capabilities={"Pay"},
    auto_discover_workspace=False,  # Manual
    auto_join=False
)

# Manually trigger discovery
workspace, artifact = adapter.discover_workspace_by_class(
    "http://localhost:8080/",
    "http://example.org/Rug"
)

if workspace:
    adapter.workspace_uri = workspace
    adapter.goal_artifact_uri = artifact
    adapter.join_workspace()
```

## Example Agent

See `buyer_agent_auto_discovery.py` for a complete example:

```python
# Configuration - only semantics!
BASE_URL = 'http://localhost:8080/'
GOAL_ITEM_CLASS = 'http://example.org/Rug'

# Automatic discovery
adapter = HypermediaMetaAdapter(
    name="BuyerAgent",
    base_uri=BASE_URL,
    goal_artifact_class=GOAL_ITEM_CLASS,  # Only knows the class!
    web_id=f'http://localhost:{ADAPTER_PORT}',
    adapter_endpoint=str(ADAPTER_PORT),
    capabilities={"Pay"},
    auto_discover_workspace=True,
    auto_join=True
)

# Agent discovered everything!
# - Workspace: http://localhost:8080/workspaces/bazaar/
# - Artifact: http://localhost:8080/workspaces/bazaar/artifacts/rug#artifact

# Now proceed with protocol discovery and execution
protocol = adapter.discover_protocol_for_goal(adapter.goal_artifact_uri)
# ... rest of agent logic
```

## Discovery Output

When running the agent, you'll see detailed discovery logs:

```
=== Starting class-based workspace discovery ===
Base URI: http://localhost:8080/
Artifact class: http://example.org/Rug
Max depth: 5

Found 1 workspaces at base URI
Searching workspace: http://localhost:8080/workspaces/bazaar/
Found 1 artifact(s) of class
✓ Found artifact of class in workspace: http://localhost:8080/workspaces/bazaar/

✓ Discovery successful!
  Workspace: http://localhost:8080/workspaces/bazaar/
  Artifact: http://localhost:8080/workspaces/bazaar/artifacts/rug#artifact
=== Class-based discovery complete ===
```

## Testing

Run the test suite to verify class-based discovery:

```bash
cd agents
python test_workspace_discovery.py
```

Expected output:
```
Test 3: Initialization with class-based discovery params (disabled)
  ✓ Initialization with class-based discovery params successful
  - Goal class: http://example.org/Rug

Test 4: Verify discovery methods exist
  ✓ discover_workspace_by_class method exists
  ✓ discover_workspace_by_class is callable
```

## Running the Agents

### With Yggdrasil Environment

```bash
# Terminal 1: Start environment
cd HypermediaInteractionProtocols
./start.sh

# Terminal 2: Run class-based buyer agent
cd agents
python buyer_agent_auto_discovery.py

# Terminal 3: Run seller agent
python bazaar_agent.py
```

### Without Environment

The initialization will fail gracefully with a helpful message:

```
✗ Failed to discover workspace: Could not discover workspace for artifact class: http://example.org/Rug

Make sure the Yggdrasil environment is running:
  cd HypermediaInteractionProtocols
  ./start.sh
```

## Comparison of Discovery Modes

| Mode | Agent Knows | Discovers | Autonomy |
|------|------------|-----------|----------|
| **Hardcoded** | Full workspace + artifact URI | Nothing | ⭐️ Low |
| **URI-based** | Base URI + artifact URI | Workspace location | ⭐️⭐️ Medium |
| **Class-based** | Base URI + artifact class | Workspace + artifact URI | ⭐️⭐️⭐️ High |

## Key Files Modified

1. **env/conf/metadata/rug.ttl**
   - Added `ex:Rug` class to artifact

2. **HypermediaTools.py**
   - Added `get_artifacts_by_class()`
   - Added `find_workspace_containing_artifact_class()`
   - Added `discover_workspace_by_artifact_class()`

3. **HypermediaMetaAdapter.py**
   - Added `goal_artifact_class` parameter
   - Added `discover_workspace_by_class()` method
   - Updated `__init__()` to support class-based discovery

4. **buyer_agent_auto_discovery.py**
   - Updated to use class-based discovery

5. **buyer_agent_with_discovery.py**
   - Updated to demonstrate manual class-based discovery

6. **test_workspace_discovery.py**
   - Added tests for class-based discovery

## Architecture Benefits

### Separation of Concerns
- **Semantic Layer**: RDF metadata describes what things are
- **Discovery Layer**: Agents navigate by semantic queries
- **Protocol Layer**: BSPL handles interaction protocols

### Flexibility
- Artifacts can move between workspaces without breaking agents
- New artifact types can be added without code changes
- Multiple artifacts of same class can coexist

### Realism
Models real-world scenarios:
- "Find me a coffee shop nearby" (class: CoffeeShop)
- "Find an available printer" (class: Printer)
- "Find a rug to buy" (class: Rug)

## Future Extensions

### Multiple Results
```python
# Find ALL rugs, not just the first
workspaces_and_artifacts = discover_all_artifacts_by_class(
    "http://localhost:8080/",
    "http://example.org/Rug"
)
# Returns list of (workspace, artifact) tuples
```

### Property-Based Discovery
```python
# Find rugs with specific properties
discover_artifacts_by_class_and_properties(
    base_uri="http://localhost:8080/",
    artifact_class="http://example.org/Rug",
    properties={
        "gr:hasPriceSpecification": {"gr:hasCurrencyValue": {"max": 100}}
    }
)
```

### Proximity-Based Discovery
```python
# Find nearest artifact of class (using spatial metadata)
discover_nearest_artifact(
    base_uri="http://localhost:8080/",
    artifact_class="http://example.org/CoffeeShop",
    location={"lat": 46.5, "lon": 6.5}
)
```

## References

- **HATEOAS Principle**: https://en.wikipedia.org/wiki/HATEOAS
- **RDF**: https://www.w3.org/RDF/
- **SPARQL**: https://www.w3.org/TR/sparql11-query/
- **GoodRelations Ontology**: http://purl.org/goodrelations/v1
- **W3C Thing Description**: https://www.w3.org/TR/wot-thing-description/

## Summary

Class-based discovery represents the pinnacle of autonomous agent behavior:
- ✅ Agents navigate by **semantics**, not hardcoded paths
- ✅ True **hypermedia-driven** discovery
- ✅ **Flexible** and **scalable** architecture
- ✅ Models **realistic** scenarios

This implementation demonstrates how semantic web technologies (RDF, SPARQL) combine with hypermedia principles (HATEOAS) to enable truly autonomous multi-agent systems.
