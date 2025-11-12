# Class-Based Discovery Implementation Summary

## What Was Implemented

Agents can now discover artifacts by their **semantic RDF class** instead of hardcoded URIs.

### Before (Hardcoded URI)
```python
GOAL_ITEM = 'http://localhost:8080/workspaces/bazaar/artifacts/rug#artifact'
```

### After (Semantic Class)
```python
GOAL_ITEM_CLASS = 'http://example.org/Rug'  # Just the class!
```

## Changes Made

### 1. Metadata Enhancement
**File:** `env/conf/metadata/rug.ttl`
- Added `ex:Rug` class to rug artifact
- Now artifacts have semantic types that agents can query

```turtle
@prefix ex: <http://example.org/> .

<workspaces/bazaar/artifacts/rug#artifact>
    a ex:Rug .  # ← Semantic classification
```

### 2. Discovery Functions
**File:** `HypermediaTools.py` (+183 lines)

Added three new functions:

**`get_artifacts_by_class(workspace_uri, artifact_class)`**
- Queries workspace for artifacts of specific RDF class
- Implementation: Fetches all artifacts from collection, then queries each individual artifact for full type information (collection endpoint doesn't include all types)
- Returns list of matching artifact URIs

**`find_workspace_containing_artifact_class(base_uri, artifact_class)`**
- Recursively crawls workspaces searching for artifacts of given class
- Returns tuple: (workspace_uri, artifact_uri)

**`discover_workspace_by_artifact_class(base_uri, artifact_class)`**
- Main entry point for class-based discovery
- Detailed logging of search process

### 3. Adapter Support
**File:** `HypermediaMetaAdapter.py`

**New Parameter:**
```python
def __init__(
    self,
    goal_artifact_class: str = None,  # ← New!
    ...
)
```

**New Method:**
```python
def discover_workspace_by_class(
    self,
    base_uri: str,
    artifact_class: str
) -> tuple[Optional[str], Optional[str]]:
    """Discover workspace containing artifact of specific class."""
```

**Enhanced Initialization:**
- Automatically discovers workspace AND artifact when `goal_artifact_class` provided
- Sets both `workspace_uri` and `goal_artifact_uri` from discovery

### 4. Updated Agents
**File:** `buyer_agent_auto_discovery.py`
- Changed from URI-based to class-based discovery
- Now only knows semantic class, not exact URI
- Discovers artifact URI automatically

**File:** `buyer_agent_with_discovery.py`
- Updated to demonstrate manual class-based discovery
- Shows step-by-step discovery process

### 5. Enhanced Testing
**File:** `test_workspace_discovery.py`
- Added Test 3: Class-based discovery parameters
- Added Test 4: Verify class-based discovery methods exist
- All tests pass ✓

### 6. Documentation
**File:** `CLASS_BASED_DISCOVERY.md` (new)
- Complete guide to class-based discovery
- Usage examples
- Architecture benefits
- Comparison of discovery modes

## How to Use

### Automatic Mode (Simplest)
```python
adapter = HypermediaMetaAdapter(
    name="BuyerAgent",
    base_uri="http://localhost:8080/",
    goal_artifact_class="http://example.org/Rug",  # Only the class!
    auto_discover_workspace=True,
    auto_join=True
)

# Workspace and artifact discovered automatically!
print(adapter.workspace_uri)     # Discovered workspace
print(adapter.goal_artifact_uri) # Discovered artifact
```

### Manual Mode (More Control)
```python
adapter = HypermediaMetaAdapter(
    name="BuyerAgent",
    base_uri="http://localhost:8080/",
    goal_artifact_class="http://example.org/Rug",
    auto_discover_workspace=False
)

# Manual discovery
workspace, artifact = adapter.discover_workspace_by_class(
    "http://localhost:8080/",
    "http://example.org/Rug"
)

adapter.workspace_uri = workspace
adapter.goal_artifact_uri = artifact
adapter.join_workspace()
```

## Testing

```bash
# Run unit tests
cd agents
python test_workspace_discovery.py

# Run with full environment
cd HypermediaInteractionProtocols
./start.sh

# In another terminal
cd agents
python buyer_agent_auto_discovery.py
```

## Discovery Algorithm

```
START: base_uri, artifact_class
│
├─ Query: "What workspaces exist at base_uri?"
│
├─ For each workspace:
│  ├─ Query: "What artifacts of class X exist here?"
│  ├─ If found: RETURN (workspace, artifact)
│  └─ Else: Recursively search sub-workspaces
│
└─ Return None if not found after max_depth
```

## Benefits

### 1. True Autonomy
Agents navigate by **semantics**, not hardcoded paths
- "Find me a rug" vs "Go to /workspaces/bazaar/artifacts/rug"

### 2. Flexibility
- Artifacts can move between workspaces
- Multiple artifacts of same class can coexist
- No brittle path dependencies

### 3. Scalability
- Add new artifact types without code changes
- Just add RDF type to metadata
- Agents automatically discover them

### 4. Hypermedia-Native
- Follows HATEOAS principles completely
- True hypermedia-driven architecture
- Semantic queries + hypermedia navigation

## Example Output

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

✓ Workspace discovered and joined: http://localhost:8080/workspaces/bazaar/
✓ Artifact discovered: http://localhost:8080/workspaces/bazaar/artifacts/rug#artifact
```

## Files Modified

1. `env/conf/metadata/rug.ttl` - Added semantic class
2. `HypermediaTools.py` - Added class-based discovery functions
3. `HypermediaMetaAdapter.py` - Added class-based discovery support
4. `buyer_agent_auto_discovery.py` - Updated to use class-based discovery
5. `buyer_agent_with_discovery.py` - Updated to demonstrate manual discovery
6. `test_workspace_discovery.py` - Added class-based tests

## Files Created

1. `CLASS_BASED_DISCOVERY.md` - Complete documentation
2. `CLASS_BASED_DISCOVERY_SUMMARY.md` - This file

## Architecture

```
┌─────────────────────────────────────────┐
│  Agent Configuration                     │
│  • Base URI: http://localhost:8080/    │
│  • Goal Class: ex:Rug                   │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  HypermediaMetaAdapter                   │
│  • discover_workspace_by_class()        │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  HypermediaTools                         │
│  • discover_workspace_by_artifact_class()│
│  • find_workspace_containing_artifact_class()│
│  • get_artifacts_by_class()             │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  SPARQL Queries on Workspace Metadata   │
│  SELECT ?artifact WHERE {               │
│    ?artifact a <ex:Rug> .               │
│  }                                      │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  Result                                  │
│  • workspace_uri                        │
│  • artifact_uri                         │
└─────────────────────────────────────────┘
```

## Comparison

| Discovery Mode | Agent Input | Discovered | Autonomy Level |
|---------------|-------------|------------|----------------|
| Hardcoded | Full URI | Nothing | ⭐️ Low |
| URI-based | Base + Artifact URI | Workspace | ⭐️⭐️ Medium |
| **Class-based** | **Base + Class** | **Workspace + Artifact** | **⭐️⭐️⭐️ High** |

## Future Extensions

### Multiple Results
Find all artifacts of a class, not just the first:
```python
results = discover_all_artifacts_by_class(base_uri, "ex:Rug")
# Returns: [(workspace1, artifact1), (workspace2, artifact2), ...]
```

### Property Constraints
Find artifacts matching class AND properties:
```python
discover_artifacts_by_class_and_properties(
    artifact_class="ex:Rug",
    properties={"gr:hasCurrencyValue": {"max": 100}}
)
```

### Spatial Discovery
Find nearest artifact of class:
```python
discover_nearest_artifact(
    artifact_class="ex:CoffeeShop",
    location={"lat": 46.5, "lon": 6.5}
)
```

## Implementation Notes

### Collection vs Individual Endpoints

An important discovery during implementation: Yggdrasil's `/artifacts/` collection endpoint returns only basic type information (`hmas:Artifact`), not the full semantic types defined in metadata files.

**Problem:**
```
GET http://localhost:8080/workspaces/bazaar/artifacts/
Returns: artifact a hmas:Artifact  (missing ex:Rug type!)
```

**Solution:**
```
1. GET /artifacts/ → Get list of all artifacts
2. For each artifact:
   GET /artifacts/{artifact} → Get full types including ex:Rug
3. Return only artifacts matching requested class
```

This means class-based discovery performs multiple HTTP requests but ensures accurate type matching.

### Testing Results

Full end-to-end test with Yggdrasil environment:

```
=== Starting class-based workspace discovery ===
Base URI: http://localhost:8080/
Artifact class: http://example.org/Rug

Found 2 workspaces at base URI
Searching workspace: http://localhost:8080/workspaces/bazaar/
Found 1 artifact(s) of class
✓ Found artifact of class in workspace: http://localhost:8080/workspaces/bazaar/

✓ Discovery successful!
  Workspace: http://localhost:8080/workspaces/bazaar/
  Artifact: http://localhost:8080/workspaces/bazaar/artifacts/rug#artifact

✓ Workspace discovered and joined
✓ Discovered protocol: Buy
✓ Discovered agent: bazaar_agent
✓ System formed successfully
✓ Two purchases completed
✓ Agent completed successfully
```

## Status

✅ **Complete** - All functionality implemented and tested

- ✅ Semantic metadata added
- ✅ Discovery functions implemented (with collection endpoint workaround)
- ✅ Adapter support added
- ✅ Agents updated
- ✅ Unit tests passing
- ✅ End-to-end tests successful
- ✅ Documentation complete

## Next Steps for Users

1. **Define your artifact classes** in metadata files (e.g., `ex:Rug`)
2. **Restart environment** after metadata changes (`./start.sh`)
3. **Configure agents** with `goal_artifact_class` instead of URIs
4. **Let agents discover** everything through semantic queries
5. **Enjoy true autonomy** and flexibility!
