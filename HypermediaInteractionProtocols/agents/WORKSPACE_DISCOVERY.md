# Workspace Discovery - True Hypermedia-Driven Agents

## Overview

The workspace discovery feature enables agents to autonomously find the correct workspace for their goal through hypermedia crawling. Instead of being given the exact workspace URI, agents start with just a **base URL** and **goal artifact URI**, then discover the workspace hierarchy through hypermedia traversal.

This implements the **true spirit of hypermedia**: agents navigate by following links, not by knowing URLs in advance.

## Problem Statement

**Before:** Agents needed to know the exact workspace URI
```python
# Agent must know the full path
WORKSPACE_URI = 'http://localhost:8080/workspaces/bazaar/'
```

**Issue:** This breaks the hypermedia principle - agents shouldn't need hardcoded paths!

**After:** Agents discover workspaces autonomously
```python
# Agent only knows the entry point
BASE_URI = 'http://localhost:8080/'
GOAL_ARTIFACT = 'http://localhost:8080/workspaces/bazaar/artifacts/rug#artifact'

# Agent crawls and discovers: http://localhost:8080/workspaces/bazaar/
```

## How It Works

### 1. Workspace Crawling Algorithm

The discovery uses a depth-first search through the workspace hierarchy:

```
1. Start at base URI (e.g., http://localhost:8080/)
2. Query for sub-workspaces using SPARQL
3. For each workspace:
   a. Check if goal artifact is in this workspace
   b. If found → return workspace URI
   c. If not found → recursively search sub-workspaces
4. Continue until artifact found or max depth reached
```

### 2. RDF Queries

The implementation uses two main queries:

**Find sub-workspaces:**
```sparql
PREFIX hmas: <https://purl.org/hmas/>

SELECT ?workspace WHERE {
  ?workspace a hmas:Workspace .
}
```

**Find artifacts in workspace:**
```sparql
PREFIX hmas: <https://purl.org/hmas/>

SELECT ?artifact WHERE {
  ?artifact a hmas:Artifact .
}
```

### 3. Depth Limiting

To prevent infinite loops in cyclic workspace hierarchies, discovery is limited to a maximum depth (default: 5 levels).

## Usage Examples

### Example 1: Manual Discovery

Full control over each step:

```python
from HypermediaMetaAdapter import HypermediaMetaAdapter

adapter = HypermediaMetaAdapter(
    name="BuyerAgent",
    base_uri="http://localhost:8080/",
    goal_artifact_uri="http://localhost:8080/workspaces/bazaar/artifacts/rug#artifact",
    web_id="http://localhost:8011",
    adapter_endpoint="8011",
    capabilities={"Pay"},
    auto_join=False,  # Manual control
    auto_discover_workspace=False  # Manual discovery
)

async def main():
    adapter.start_in_loop()

    # Manually discover workspace
    workspace = adapter.discover_workspace(
        "http://localhost:8080/",
        "http://localhost:8080/workspaces/bazaar/artifacts/rug#artifact"
    )

    if workspace:
        adapter.workspace_uri = workspace
        adapter.join_workspace()
        # ... continue with protocol discovery, etc.
```

### Example 2: Automatic Discovery

Simplest approach - everything handled automatically:

```python
adapter = HypermediaMetaAdapter(
    name="BuyerAgent",
    base_uri="http://localhost:8080/",
    goal_artifact_uri="http://localhost:8080/workspaces/bazaar/artifacts/rug#artifact",
    web_id="http://localhost:8011",
    adapter_endpoint="8011",
    capabilities={"Pay"},
    auto_discover_workspace=True,  # ← Automatic!
    auto_join=True                 # ← Automatic!
)

# Workspace already discovered and joined!
# Continue with protocol discovery...
```

### Example 3: Using HypermediaTools Directly

For non-adapter usage:

```python
from HypermediaTools import discover_workspace_for_goal

workspace = discover_workspace_for_goal(
    base_uri="http://localhost:8080/",
    goal_artifact_uri="http://localhost:8080/workspaces/bazaar/artifacts/rug#artifact",
    max_depth=5
)

print(f"Discovered workspace: {workspace}")
# Output: http://localhost:8080/workspaces/bazaar/
```

## Console Output

The discovery process provides detailed logging:

```
=== Starting workspace discovery ===
Base URI: http://localhost:8080/
Goal artifact: http://localhost:8080/workspaces/bazaar/artifacts/rug#artifact
Max depth: 5

Found 2 workspaces at base URI
Searching workspace: http://localhost:8080/workspaces/bazaar/
Found 5 artifacts
✓ Found goal artifact in workspace: http://localhost:8080/workspaces/bazaar/

✓ Discovery successful! Workspace: http://localhost:8080/workspaces/bazaar/
=== Workspace discovery complete ===
```

## Implementation Files

### HypermediaTools.py

Contains the core crawling functions:
- `get_workspaces_in(workspace_uri)` - Find sub-workspaces
- `get_artifacts_in(workspace_uri)` - Find artifacts in workspace
- `find_workspace_containing_artifact(...)` - Recursive search (internal)
- `discover_workspace_for_goal(...)` - Main entry point

### HypermediaMetaAdapter.py

Integrates discovery into the adapter:
- `discover_workspace(base_uri, goal_artifact_uri)` - Discovery method
- Constructor parameter: `base_uri` - Alternative to workspace_uri
- Constructor parameter: `goal_artifact_uri` - For discovery
- Constructor parameter: `auto_discover_workspace` - Automatic mode

### Example Agents

- `buyer_agent_with_discovery.py` - Manual discovery with detailed steps
- `buyer_agent_auto_discovery.py` - Automatic discovery (simplest)

## Comparison: Before vs After

### Before (Hardcoded Workspace)

```python
# ❌ Agent must know exact workspace path
WORKSPACE_URI = 'http://localhost:8080/workspaces/bazaar/'
GOAL_ITEM = 'http://localhost:8080/workspaces/bazaar/artifacts/rug#artifact'

adapter = MetaAdapter(name=NAME, ...)
join_workspace(WORKSPACE_URI, ...)  # Hardcoded!
```

**Problems:**
- Breaks hypermedia principles
- Requires prior knowledge of workspace structure
- Not adaptable to environment changes
- Can't discover nested workspaces

### After (Discovered Workspace)

```python
# ✅ Agent only knows entry point
BASE_URI = 'http://localhost:8080/'
GOAL_ITEM = 'http://localhost:8080/workspaces/bazaar/artifacts/rug#artifact'

adapter = HypermediaMetaAdapter(
    base_uri=BASE_URI,              # Start here
    goal_artifact_uri=GOAL_ITEM,    # Find this
    auto_discover_workspace=True    # Discover automatically
)
```

**Benefits:**
- ✅ True hypermedia navigation
- ✅ No hardcoded workspace paths
- ✅ Adapts to environment structure
- ✅ Discovers nested workspaces automatically
- ✅ More realistic agent autonomy

## Architecture

### Workspace Hierarchy Example

```
http://localhost:8080/
├── workspaces/
│   ├── bazaar/                     ← Target workspace
│   │   ├── artifacts/
│   │   │   ├── rug#artifact        ← Goal artifact!
│   │   │   ├── lamp#artifact
│   │   │   └── table#artifact
│   │   └── sub-workspace-a/
│   ├── marketplace/
│   │   └── artifacts/
│   └── store/
│       ├── artifacts/
│       └── sub-workspace-b/
```

**Discovery path:**
1. Start at `http://localhost:8080/`
2. Find workspaces: `bazaar/`, `marketplace/`, `store/`
3. Check `bazaar/artifacts/` → Find `rug#artifact` ✓
4. Return `http://localhost:8080/workspaces/bazaar/`

### Search Strategy

- **Depth-First Search (DFS)**: Explores each branch fully before moving to the next
- **Early termination**: Stops as soon as artifact is found
- **Depth limiting**: Prevents infinite loops (max_depth=5)
- **Artifact matching**: Supports exact match or substring match

## Performance Considerations

### Best Case
- Artifact in first workspace checked
- **Complexity**: O(1)
- **HTTP requests**: 2 (workspace list + artifact list)

### Worst Case
- Artifact in last leaf node
- **Complexity**: O(w × d) where w=workspaces per level, d=depth
- **HTTP requests**: O(w^d)

### Optimization
- Concurrent workspace checks (future enhancement)
- Workspace caching (future enhancement)
- Smart ordering based on heuristics (future enhancement)

## Edge Cases Handled

1. **Artifact not found**: Returns `None`, agent can handle gracefully
2. **Max depth exceeded**: Stops search, returns `None`
3. **HTTP errors**: Caught and logged, continues with next workspace
4. **Circular workspace references**: Limited by max_depth
5. **Multiple matching artifacts**: Returns first found workspace

## Future Enhancements

### 1. Parallel Search
```python
# Search multiple workspaces concurrently
async def discover_workspace_parallel(...):
    tasks = [search_workspace(ws) for ws in workspaces]
    results = await asyncio.gather(*tasks)
    return first_non_none(results)
```

### 2. Semantic Hints
```python
# Use semantic annotations to guide search
# E.g., "marketplace" workspaces for shopping goals
def discover_workspace_with_hints(base_uri, goal, hints):
    # Prioritize workspaces matching hints
    ...
```

### 3. Caching
```python
# Cache workspace structure for faster subsequent searches
workspace_cache = {
    "http://localhost:8080/workspaces/bazaar/": {
        "artifacts": [...],
        "sub_workspaces": [...],
        "timestamp": ...
    }
}
```

### 4. Breadth-First Search
```python
# Alternative search strategy
# Better for shallow hierarchies
def discover_workspace_bfs(...):
    queue = [base_uri]
    while queue:
        workspace = queue.pop(0)
        # Check artifacts...
        # Add sub-workspaces to queue...
```

## Testing

### Manual Test

Run the discovery demo:
```bash
cd HypermediaInteractionProtocols/agents
python buyer_agent_with_discovery.py
```

Expected output shows each discovery step with indentation showing depth.

### Unit Test Example

```python
def test_workspace_discovery():
    workspace = discover_workspace_for_goal(
        "http://localhost:8080/",
        "http://localhost:8080/workspaces/bazaar/artifacts/rug#artifact"
    )
    assert workspace == "http://localhost:8080/workspaces/bazaar/"
```

## Best Practices

1. **Always set max_depth**: Prevent infinite loops
2. **Handle None results**: Discovery might fail
3. **Use auto-discovery for simplicity**: Unless you need manual control
4. **Log discovery process**: Helps debugging and understanding agent behavior
5. **Cache discovered workspaces**: If making multiple searches

## Related Documentation

- `HypermediaTools.py` - Implementation details
- `HypermediaMetaAdapter.py` - Integration with adapter
- `buyer_agent_with_discovery.py` - Complete example
- `README.md` - Overall project documentation

## Summary

Workspace discovery transforms agents from **hardcoded** to **truly autonomous**:

- **Before**: Agent has hardcoded workspace path
- **After**: Agent discovers workspace through hypermedia
- **Benefit**: True hypermedia-driven agent behavior
- **Complexity**: Minimal additional code
- **Performance**: Acceptable for typical workspace hierarchies

This feature is a key step toward fully autonomous hypermedia agents that can navigate arbitrary environments without prior knowledge of their structure! 🚀
