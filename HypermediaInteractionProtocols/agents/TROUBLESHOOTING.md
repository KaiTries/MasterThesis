# Troubleshooting Guide

## Class-Based Discovery Issues

### Problem: "Found 0 artifact(s) of class"

**Symptoms:**
```
Searching workspace: http://localhost:8080/workspaces/bazaar/
Found 0 artifact(s) of class
```

**Possible Causes:**

#### 1. Environment Not Restarted After Metadata Changes

Metadata files are loaded when Yggdrasil starts. If you modify metadata files (like adding `ex:Rug` class), the environment must be restarted.

**Solution:**
```bash
# Stop the environment (Ctrl+C or press any key if using start.sh)
# Then restart:
cd HypermediaInteractionProtocols
./start.sh
```

#### 2. Incorrect RDF Class URI

Make sure the class URI in your agent matches the metadata file exactly.

**Metadata file (`rug.ttl`):**
```turtle
@prefix ex: <http://example.org/> .

<workspaces/bazaar/artifacts/rug#artifact> a ex:Rug ;
```

**Agent code:**
```python
GOAL_ITEM_CLASS = 'http://example.org/Rug'  # Must match exactly!
```

**Common mistakes:**
- Missing `http://` prefix
- Wrong namespace (e.g., `http://example.com/` vs `http://example.org/`)
- Capitalization mismatch (e.g., `rug` vs `Rug`)

#### 3. Metadata File Not Referenced in Configuration

Check that `conf/buy_demo.json` references your metadata file:

```json
{
  "workspaces": [
    {
      "name": "bazaar",
      "artifacts": [
        {
          "name": "rug",
          "representation": "conf/metadata/rug.ttl"  // ← Must be present
        }
      ]
    }
  ]
}
```

### Debugging Steps

#### 1. Verify Metadata is Loaded

Check individual artifact endpoint:

```bash
curl http://localhost:8080/workspaces/bazaar/artifacts/rug
```

Should show:
```turtle
<workspaces/bazaar/artifacts/rug#artifact> a ex:Rug ;
```

#### 2. Check Collection Endpoint

The collection endpoint may not show custom types:

```bash
curl http://localhost:8080/workspaces/bazaar/artifacts/
```

May only show:
```turtle
<workspaces/bazaar/artifacts/rug#artifact> a hmas:Artifact .
```

This is expected! The discovery function queries individual artifacts for full types.

#### 3. Run Debug Script

Create a quick test:

```python
import requests
from rdflib import Graph

artifact_uri = "http://localhost:8080/workspaces/bazaar/artifacts/rug"
response = requests.get(artifact_uri)
graph = Graph()
graph.parse(data=response.text, format='turtle')

# Check for your class
query = """
SELECT ?s WHERE {
  ?s a <http://example.org/Rug> .
}
"""
results = list(graph.query(query))
print(f"Found {len(results)} artifacts of class ex:Rug")
```

## Other Common Issues

### Issue: "Connection refused" or timeout

**Solution:**
Environment not running. Start it:
```bash
cd HypermediaInteractionProtocols
./start.sh
```

### Issue: Agent can't find other agents

**Symptoms:**
```
Discovered 0 agent(s)
Must join workspace before discovering agents
```

**Solutions:**
1. Make sure seller agent is running (e.g., `bazaar_agent.py`)
2. Verify workspace was joined successfully
3. Check that both agents have compatible roles for the protocol

### Issue: "System not well-formed"

**Symptoms:**
```
✗ System not well-formed, cannot initiate protocol
```

**Solution:**
The protocol requires specific roles that aren't filled. Check:
1. Protocol requires which roles? (e.g., Buy protocol needs Buyer and Seller)
2. Do discovered agents have compatible roles?
3. Did all role proposals get accepted?

### Issue: Protocol not discovered

**Symptoms:**
```
✗ Could not discover protocol for goal item
```

**Solutions:**
1. Check that workspace metadata includes protocol link:
   ```turtle
   bspl:protocol <http://localhost:8005/protocols/buy_protocol> .
   ```
2. Verify protocol server is running (started by `start.sh`)
3. Check that protocol offers the goal artifact:
   ```turtle
   gr:includesObject [
     gr:typeOfGood <bazaar/artifacts/rug#artifact>;
   ];
   ```

## Performance Considerations

### Class-Based Discovery is Slow

Class-based discovery queries each individual artifact to check its types. For workspaces with many artifacts, this can be slow.

**Optimization options:**

1. **Use URI-based discovery** if you know the artifact URI:
   ```python
   adapter = HypermediaMetaAdapter(
       goal_artifact_uri="http://...rug#artifact",  # Faster
       # Instead of goal_artifact_class
   )
   ```

2. **Filter by workspace** if you know the workspace:
   ```python
   adapter = HypermediaMetaAdapter(
       workspace_uri="http://localhost:8080/workspaces/bazaar/",
       goal_artifact_class="http://example.org/Rug",
       auto_discover_workspace=False  # Skip workspace search
   )
   ```

3. **Cache artifact types** (future enhancement)

## Getting Help

### Check Logs

Enable debug mode for detailed logs:
```python
adapter = HypermediaMetaAdapter(
    ...,
    debug=True  # ← Verbose logging
)
```

### Verify Environment Health

```bash
# Check if Yggdrasil is running
curl http://localhost:8080/

# Check workspaces
curl http://localhost:8080/workspaces/

# Check protocol server
curl http://localhost:8005/protocols/buy_protocol
```

### Test Without Discovery

Use hardcoded values to isolate the issue:

```python
# Minimal test - no discovery
adapter = HypermediaMetaAdapter(
    name="TestAgent",
    workspace_uri="http://localhost:8080/workspaces/bazaar/",
    web_id="http://localhost:9999",
    adapter_endpoint="9999",
    capabilities={"Pay"},
    auto_join=True,
    auto_discover_workspace=False  # Disabled
)
```

If this works, the issue is with discovery. If not, it's with the environment setup.

## Common Workflow Issues

### Changes Not Taking Effect

**After modifying:**
- Metadata files → Restart environment (`./start.sh`)
- Agent code → Just re-run agent
- Adapter code → Re-run agent
- Configuration (`.json`) → Restart environment

### Multiple Agents Interfering

If running multiple test agents that don't clean up:

```bash
# Check for stray processes
ps aux | grep python

# Kill if needed
pkill -f buyer_agent
pkill -f bazaar_agent
```

### Port Already in Use

```
Error: Address already in use (port 8011)
```

**Solution:**
```bash
# Find process using port
lsof -ti:8011

# Kill it
kill $(lsof -ti:8011)
```

## Best Practices

1. **Always restart environment** after metadata changes
2. **Use debug mode** when developing
3. **Test with simple cases** first (hardcoded URIs)
4. **Add class-based discovery** once basic flow works
5. **Check individual artifact endpoints** to verify metadata
6. **Use meaningful class URIs** (e.g., `http://example.org/Rug` not `ex:thing1`)
7. **Document your ontology** (which classes exist, what they mean)

## Reference

### Key Endpoints

- Base: `http://localhost:8080/`
- Workspaces: `http://localhost:8080/workspaces/`
- Artifacts: `http://localhost:8080/workspaces/{workspace}/artifacts/`
- Individual artifact: `http://localhost:8080/workspaces/{workspace}/artifacts/{artifact}`
- Protocol server: `http://localhost:8005/protocols/`

### Key Files

- Environment config: `env/conf/buy_demo.json`
- Metadata: `env/conf/metadata/*.ttl`
- Start script: `start.sh`
- Agents: `agents/*.py`
- Tools: `agents/HypermediaTools.py`
- Adapter: `agents/HypermediaMetaAdapter.py`

### Discovery Order

For a fully autonomous agent:
1. Discover workspace (by class or URI)
2. Join workspace
3. Discover protocol (from goal artifact)
4. Discover other agents
5. Propose system and negotiate roles
6. Wait for system formation
7. Execute protocol
8. Leave workspace
