# Bug Fixes: Workspace Discovery Issues

## Bug #1: Initialization Order Issue

### Problem

When running `buyer_agent_auto_discovery.py`, the following error occurred:

```
AttributeError: 'HypermediaMetaAdapter' object has no attribute 'logger'
```

### Root Cause

The initialization order in `HypermediaMetaAdapter.__init__()` was incorrect:

1. Workspace discovery was attempted (`self.discover_workspace()`)
2. Discovery tried to use `self.info()` which requires `self.logger`
3. But `self.logger` wasn't created yet because `super().__init__()` hadn't been called

**Incorrect order:**
```python
def __init__(self, ...):
    # Store config
    self.workspace_uri = workspace_uri
    ...

    # ❌ Discovery before parent init
    if auto_discover_workspace:
        discovered = self.discover_workspace(...)  # Uses self.logger!

    # Parent init (creates self.logger)
    super().__init__(...)
```

### Solution

Fixed the initialization order:

1. First call `super().__init__()` to set up logger and other attributes
2. Then perform workspace discovery (can now use self.logger)
3. Finally auto-join if requested

**Correct order:**
```python
def __init__(self, ...):
    # Store config
    self.base_uri = base_uri
    ...

    # ✅ Parent init first (creates self.logger)
    super().__init__(
        name=name,
        systems=systems,
        agents=agents,
        capabilities=capabilities,
        debug=debug
    )

    # ✅ Now discovery can use self.logger
    if auto_discover_workspace and base_uri and goal_artifact_uri:
        discovered = self.discover_workspace(...)
        self.workspace_uri = discovered

    # ✅ Auto-join after discovery
    if auto_join:
        if self.workspace_uri:
            self.join_workspace()
```

### Additional Improvements

#### Better Error Handling

Added error handling in `buyer_agent_auto_discovery.py`:

```python
try:
    adapter = HypermediaMetaAdapter(
        ...,
        auto_discover_workspace=True,
        auto_join=True
    )
except ValueError as e:
    print(f"✗ Failed to discover workspace: {e}")
    print("\nMake sure the Yggdrasil environment is running:")
    print("  cd HypermediaInteractionProtocols")
    print("  ./start.sh")
    exit(1)
```

#### Validation

Added check in auto-join logic:

```python
if auto_join:
    if not self.workspace_uri:
        self.logger.error("Cannot auto-join: no workspace_uri available.")
    else:
        success, artifact_address = self.join_workspace()
        if not success:
            self.logger.error("Failed to join workspace during initialization")
```

---

## Bug #2: Fragment Identifier in Workspace URIs

### Problem

After fixing Bug #1, workspace discovery succeeded but joining the discovered workspace failed:

```
✓ Discovery successful! Workspace: http://localhost:8080/workspaces/bazaar#workspace/
Failed to join workspace
Must join workspace before discovering agents
```

The discovered URI contained a fragment identifier (`#workspace`) which prevented successful joining. In contrast, `buyer_agent_refactored.py` with a clean URI (`http://localhost:8080/workspaces/bazaar/`) worked correctly.

### Root Cause

When querying for workspaces using SPARQL, the RDF data includes fragment identifiers in workspace URIs:

```turtle
<http://localhost:8080/workspaces/bazaar#workspace> a hmas:Workspace
```

These fragment identifiers are part of the RDF URI but should not be used when making HTTP requests to join the workspace. The workspace join endpoint expects the base path without fragments.

### Solution

Created a `clean_workspace_uri()` function to normalize workspace URIs:

```python
def clean_workspace_uri(uri: str) -> str:
    """
    Clean a workspace URI by removing fragment identifiers and normalizing.

    Example:
        "http://localhost:8080/workspaces/bazaar#workspace"
        -> "http://localhost:8080/workspaces/bazaar/"

    Args:
        uri: The workspace URI to clean

    Returns:
        Cleaned URI without fragment, with trailing slash
    """
    # Remove fragment identifier
    if '#' in uri:
        uri = uri.split('#')[0]

    # Ensure trailing slash
    if not uri.endswith('/'):
        uri += '/'

    return uri
```

Applied cleaning at three points:

1. **In `get_workspaces_in()`** - Clean discovered workspace URIs before returning
2. **In `find_workspace_containing_artifact()`** - Return cleaned URI when goal is found
3. **Added to `test_workspace_discovery.py`** - Comprehensive test coverage

### Testing

Updated `test_workspace_discovery.py` with URI cleaning tests:

```bash
python test_workspace_discovery.py
```

Output:
```
============================================================
Testing Workspace URI Cleaning
============================================================

✓ http://localhost:8080/workspaces/bazaar#workspace
   -> http://localhost:8080/workspaces/bazaar/
✓ http://localhost:8080/workspaces/bazaar
   -> http://localhost:8080/workspaces/bazaar/
✓ http://localhost:8080/workspaces/bazaar/
   -> http://localhost:8080/workspaces/bazaar/
✓ http://localhost:8080/workspaces/bazaar#workspace/
   -> http://localhost:8080/workspaces/bazaar/

✓ All URI cleaning tests passed

============================================================
Testing HypermediaMetaAdapter Initialization
============================================================

Test 1: Basic initialization (no discovery)
  ✓ Basic initialization successful
  - Logger exists: True

Test 2: Initialization with discovery parameters (disabled)
  ✓ Initialization with discovery params successful
  - Logger exists: True

Test 3: Verify discover_workspace method exists
  ✓ discover_workspace method exists
  ✓ discover_workspace is callable
  ✓ Logger is available for discover_workspace

============================================================
All tests passed! ✓
============================================================
```

## How to Use Now

### Option 1: With Environment Running

```bash
# Terminal 1: Start environment
cd HypermediaInteractionProtocols
./start.sh

# Terminal 2: Run agent with workspace discovery
cd agents
python buyer_agent_auto_discovery.py
```

Expected output:
```
=== Starting workspace discovery ===
Base URI: http://localhost:8080/
...
✓ Discovery successful! Workspace: http://localhost:8080/workspaces/bazaar/
✓ Workspace discovered and joined: http://localhost:8080/workspaces/bazaar/
```

### Option 2: Without Environment (Will Fail Gracefully)

```bash
python buyer_agent_auto_discovery.py
```

Expected output:
```
✗ Failed to discover workspace: ...
Make sure the Yggdrasil environment is running:
  cd HypermediaInteractionProtocols
  ./start.sh
```

## Files Modified

1. **HypermediaMetaAdapter.py**
   - Fixed initialization order (Bug #1)
   - Added workspace_uri validation in auto-join
   - Better error messages

2. **HypermediaTools.py**
   - Added `clean_workspace_uri()` function (Bug #2)
   - Modified `get_workspaces_in()` to return cleaned URIs
   - Modified `find_workspace_containing_artifact()` to return cleaned URIs

3. **buyer_agent_auto_discovery.py**
   - Added try-catch for initialization errors
   - Better error messages for users

4. **buyer_agent_with_discovery.py**
   - Added better exception handling

## Files Created

1. **test_workspace_discovery.py**
   - Tests URI cleaning functionality (Bug #2)
   - Tests initialization patterns (Bug #1)
   - Verifies all fixes work correctly
   - Can run without Yggdrasil environment

2. **BUGFIX_INITIALIZATION_ORDER.md** (this file)
   - Documents both bugs and their fixes

## Status

✅ **Bug #1 Fixed** - Initialization order corrected
✅ **Bug #2 Fixed** - Fragment identifiers cleaned from workspace URIs
✅ **Tested** - All tests pass (URI cleaning + initialization)
✅ **Error Handling** - Improved user experience
✅ **Documented** - Both fixes documented for future reference

## Related Issues and Prevention

### Bug #1: Initialization Order
This bug would occur in any scenario where:
- `auto_discover_workspace=True`
- Discovery is attempted before parent initialization
- Discovery code uses logger or other parent-initialized attributes

**Prevention:** Always initialize parent class (`super().__init__()`) before using any methods that depend on parent-initialized attributes.

### Bug #2: Fragment Identifiers
This bug would occur when:
- SPARQL queries return URIs with fragment identifiers
- Fragment URIs are used directly for HTTP requests
- The HTTP endpoint expects clean paths without fragments

**Prevention:** Always clean URIs obtained from RDF/SPARQL before using them for HTTP requests. Fragment identifiers are semantic in RDF but not valid in HTTP paths.
