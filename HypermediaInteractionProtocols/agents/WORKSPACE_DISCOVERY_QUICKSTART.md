# Workspace Discovery - Quick Start

## What Is It?

Agents can now **automatically find workspaces** by crawling from a base URL, instead of needing hardcoded workspace paths. This implements true hypermedia-driven navigation!

## Quick Comparison

### ❌ Old Way (Hardcoded)
```python
WORKSPACE = 'http://localhost:8080/workspaces/bazaar/'  # Must know exact path!
```

### ✅ New Way (Discovered)
```python
BASE_URL = 'http://localhost:8080/'  # Just the entry point
GOAL = 'http://localhost:8080/workspaces/bazaar/artifacts/rug#artifact'
# Agent crawls to find the workspace automatically!
```

## Three Ways to Use It

### 1. Automatic (Easiest) 🚀

Everything happens automatically:

```python
from HypermediaMetaAdapter import HypermediaMetaAdapter

adapter = HypermediaMetaAdapter(
    name="MyAgent",
    base_uri="http://localhost:8080/",
    goal_artifact_uri="http://localhost:8080/workspaces/bazaar/artifacts/rug#artifact",
    web_id="http://localhost:8011",
    adapter_endpoint="8011",
    capabilities={"Pay"},
    auto_discover_workspace=True,  # ← Automatic discovery!
    auto_join=True                 # ← Automatic join!
)

# That's it! Workspace discovered and joined.
# Continue with protocol discovery...
```

**Use when:** You want the simplest, most straightforward code.

### 2. Manual (More Control) ⚙️

Step-by-step control:

```python
adapter = HypermediaMetaAdapter(
    name="MyAgent",
    base_uri="http://localhost:8080/",
    goal_artifact_uri="http://localhost:8080/workspaces/bazaar/artifacts/rug#artifact",
    web_id="http://localhost:8011",
    adapter_endpoint="8011",
    capabilities={"Pay"},
    auto_discover_workspace=False,  # Manual
    auto_join=False                 # Manual
)

adapter.start_in_loop()

# Step 1: Discover workspace
workspace = adapter.discover_workspace(
    "http://localhost:8080/",
    "http://localhost:8080/workspaces/bazaar/artifacts/rug#artifact"
)

# Step 2: Join discovered workspace
if workspace:
    adapter.workspace_uri = workspace
    adapter.join_workspace()
    # Continue...
```

**Use when:** You need logging, error handling, or custom logic between steps.

### 3. Direct Tools (Without Adapter) 🔧

Use discovery functions directly:

```python
from HypermediaTools import discover_workspace_for_goal

workspace = discover_workspace_for_goal(
    base_uri="http://localhost:8080/",
    goal_artifact_uri="http://localhost:8080/workspaces/bazaar/artifacts/rug#artifact",
    max_depth=5
)

print(f"Found workspace: {workspace}")
# Output: http://localhost:8080/workspaces/bazaar/
```

**Use when:** You're not using HypermediaMetaAdapter or need standalone discovery.

## Complete Example

See `buyer_agent_auto_discovery.py` for a full working example:

```python
from HypermediaMetaAdapter import HypermediaMetaAdapter
import asyncio

# Configuration
adapter = HypermediaMetaAdapter(
    name="BuyerAgent",
    base_uri="http://localhost:8080/",
    goal_artifact_uri="http://localhost:8080/workspaces/bazaar/artifacts/rug#artifact",
    web_id="http://localhost:8011",
    adapter_endpoint="8011",
    capabilities={"Pay"},
    auto_discover_workspace=True,
    auto_join=True
)

@adapter.reaction("Give")
async def give_reaction(msg):
    adapter.info(f"Received: {msg['item']}")
    return msg

async def main():
    adapter.start_in_loop()

    # Discover protocol and agents
    protocol = adapter.discover_protocol_for_goal(adapter.goal_artifact_uri)
    system_name = await adapter.discover_and_propose_system(
        protocol_name=protocol.name,
        system_name="BuySystem",
        my_role="Buyer"
    )

    # Wait and execute
    if await adapter.wait_for_system_formation(system_name):
        await adapter.initiate_protocol("Buy/Pay", {...})

    adapter.leave_workspace()

asyncio.run(main())
```

## How It Works

1. **Start at base URL** (e.g., `http://localhost:8080/`)
2. **Find workspaces** using SPARQL queries
3. **Check each workspace** for artifacts
4. **If goal found** → return workspace URI
5. **If not found** → search sub-workspaces recursively
6. **Stop at max depth** (default: 5 levels)

## Console Output

When you run discovery, you'll see:

```
=== Starting workspace discovery ===
Base URI: http://localhost:8080/
Goal artifact: .../artifacts/rug#artifact
Max depth: 5

Searching workspace: http://localhost:8080/workspaces/bazaar/
Found 5 artifacts
✓ Found goal artifact in workspace: http://localhost:8080/workspaces/bazaar/

✓ Discovery successful! Workspace: http://localhost:8080/workspaces/bazaar/
=== Workspace discovery complete ===
```

## Configuration Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `base_uri` | str | None | Starting point for discovery |
| `goal_artifact_uri` | str | None | Artifact to find |
| `auto_discover_workspace` | bool | False | Automatic discovery on init |
| `max_depth` | int | 5 | Maximum search depth |

## When To Use

### Use Workspace Discovery When:
✅ You have a **base URL** and **goal artifact**
✅ You want **true hypermedia navigation**
✅ Workspace structure might **change**
✅ You're building **autonomous agents**

### Use Direct Workspace URI When:
⚠️ Workspace location is **truly static**
⚠️ You need **maximum performance** (no discovery overhead)
⚠️ You're **testing** with fixed setup

## Troubleshooting

### Discovery Returns None

**Possible causes:**
1. Artifact doesn't exist
2. Artifact is deeper than max_depth
3. Network/HTTP errors
4. Wrong artifact URI format

**Solutions:**
```python
# Increase search depth
workspace = adapter.discover_workspace(base, goal, max_depth=10)

# Check artifact URI is correct
print(f"Looking for: {goal_artifact_uri}")

# Enable debug logging
adapter = HypermediaMetaAdapter(..., debug=True)
```

### Discovery Too Slow

**Optimize:**
```python
# Reduce max_depth if possible
workspace = adapter.discover_workspace(base, goal, max_depth=3)

# Cache discovered workspace for reuse
cached_workspace = workspace
```

### Max Depth Exceeded

**Increase limit:**
```python
workspace = adapter.discover_workspace(
    base_uri,
    goal_artifact_uri,
    max_depth=10  # Increase from default 5
)
```

## FAQ

**Q: Does discovery work with nested workspaces?**
A: Yes! It recursively searches sub-workspaces up to max_depth.

**Q: What if multiple workspaces have the same artifact?**
A: Returns the first one found (depth-first order).

**Q: Can I use both workspace_uri and base_uri?**
A: Yes, but workspace_uri takes precedence if both provided.

**Q: How many HTTP requests does discovery make?**
A: 2 per workspace searched (one for workspaces, one for artifacts).

**Q: Is it cached?**
A: Not yet, but caching is a planned enhancement.

## Examples in Repository

1. **buyer_agent_with_discovery.py** - Manual discovery with detailed steps
2. **buyer_agent_auto_discovery.py** - Automatic discovery (simplest)
3. **buyer_agent_refactored.py** - Using direct workspace_uri (old way)

## Full Documentation

For complete details, see:
- **WORKSPACE_DISCOVERY.md** - In-depth guide
- **WORKSPACE_DISCOVERY_SUMMARY.md** - Implementation summary
- **HypermediaTools.py** - Source code with docstrings

## Testing

```bash
# Terminal 1: Start environment
cd HypermediaInteractionProtocols
./start.sh

# Terminal 2: Run agent with discovery
cd agents
python buyer_agent_auto_discovery.py
```

## Summary

**Before:** Agents needed hardcoded workspace paths
**After:** Agents discover workspaces through hypermedia crawling
**Benefit:** True autonomous, hypermedia-driven agents! 🎉

**Simplest usage:**
```python
adapter = HypermediaMetaAdapter(
    base_uri="http://localhost:8080/",
    goal_artifact_uri="http://.../artifact",
    auto_discover_workspace=True,
    auto_join=True,
    ...
)
```

That's it! 🚀
