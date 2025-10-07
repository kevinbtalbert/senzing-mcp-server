# Senzing MCP Server for Cloudera Agent Studio

A Model Context Protocol (MCP) server that provides Cloudera Agent Studio with access to Senzing Entity Resolution capabilities using the **Senzing v4 SDK**.

## Overview

This MCP server enables Cloudera Agent Studio to perform entity resolution operations:

- **Entity Resolution**: Add records and automatically resolve them against existing entities
- **Entity Search**: Find entities by attributes (name, address, phone, etc.)
- **Relationship Discovery**: Find paths and networks between entities
- **Explainability**: Understand why entities are resolved together
- **Statistics & Monitoring**: View repository statistics and performance metrics

Designed for use with [CAI-Senzing-Custom-Runtime](https://github.com/kevinbtalbert/CAI-Senzing-Custom-Runtime) in Cloudera ML workspaces.

## Architecture

The MCP server uses an **embedded architecture** - the Senzing SDK runs directly inside the MCP server's Python process as a native library (no separate server required).

```
┌─────────────────────────────────────────────────────────────┐
│              Cloudera Agent Studio Workflow                  │
│              (Running in Cloudera ML)                        │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            │ MCP Protocol (stdio/JSON-RPC)
                            │ via mcpadapt
                            │
┌───────────────────────────▼─────────────────────────────────┐
│         senzing-mcp-server (Python Process)                  │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  MCP Server Layer                                   │   │
│  │  - Tool handlers (add_record, search_entities, etc)│   │
│  │  - Request/response marshaling                      │   │
│  └─────────────────────┬───────────────────────────────┘   │
│                        │                                     │
│  ┌─────────────────────▼───────────────────────────────┐   │
│  │  Senzing SDK v4 (Embedded Library)                  │   │
│  │  - SzAbstractFactoryCore (Python bindings)          │   │
│  │  - SzEngine (entity resolution)                     │   │
│  │  - Native C++ libraries (.so files)                 │   │
│  └─────────────────────┬───────────────────────────────┘   │
│                        │ Direct file I/O                     │
└────────────────────────┼─────────────────────────────────────┘
                         │
                         ▼
          ┌──────────────────────────────────┐
          │  SQLite Database                 │
          │  ~/senzing/var/sqlite/G2C.db     │
          │  (Persistent Storage)            │
          └──────────────────────────────────┘
```

**Key Points**:
- 🔧 **Embedded SDK**: No separate Senzing server process
- ⚡ **In-Process**: All operations are direct function calls
- 🔒 **Direct Access**: Database accessed via file I/O
- 🚀 **Fast**: No network overhead, minimal latency

## Prerequisites

Before using this MCP server in Agent Studio, you must:

1. **Have CAI-Senzing-Custom-Runtime deployed** in your Cloudera ML workspace
2. **Create a persistent Senzing project** at `~/senzing`
3. **Load data** into your Senzing database

See the [CAI-Senzing-Custom-Runtime setup guide](https://github.com/kevinbtalbert/CAI-Senzing-Custom-Runtime#getting-started-with-sample-data) for complete instructions.

## Quick Setup

### 1. Verify Senzing is Ready

In your Cloudera ML terminal:

```bash
# Check that project exists
ls -la ~/senzing/var/sqlite/G2C.db
# Should show your database file (e.g., 1.1M)

# Test that Senzing SDK is accessible
cd ~/senzing && source setupEnv
python3 -c "from senzing_core import SzAbstractFactoryCore; print('✓ Senzing SDK available')"
```

### 2. Configure Agent Studio

Add this MCP server configuration to your Agent Studio workflow:

```json
{
  "mcpServers": {
    "senzing": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/kevinbtalbert/senzing-mcp-server@main",
        "senzing-mcp"
      ],
      "env": {
        "SENZING_PROJECT_DIR": "/home/cdsw/senzing",
        "PYTHONPATH": "/opt/senzing/er/sdk/python",
        "LD_LIBRARY_PATH": "/home/cdsw/senzing/lib:/opt/senzing/er/lib"
      }
    }
  }
}
```

### 3. Test the Configuration

Before running in Agent Studio, test manually:

```bash
cd ~/senzing && source setupEnv
export SENZING_PROJECT_DIR=~/senzing
uvx --from git+https://github.com/kevinbtalbert/senzing-mcp-server@main senzing-mcp
```

The server should start and wait for input. Press `Ctrl+C` to stop.

## Available Tools

Once configured, your Agent Studio workflows can use these Senzing tools:

### `add_record`
Add a record for entity resolution.

**Example**: "Add a customer record for Jane Smith, DOB 1985-03-15, living at 123 Main St"

### `get_entity`
Get complete details about a resolved entity by entity ID.

**Example**: "Get entity 55"

### `search_entities`
Search for entities by attributes.

**Example**: "Search for entities named Robert Smith born in 1978"

### `find_path`
Find relationship paths between two entities.

**Example**: "Find the path between entity 55 and entity 91"

### `find_network`
Discover networks of related entities.

**Example**: "Find the network around entity 55 within 2 degrees"

### `get_record`
Retrieve a specific record by data source and record ID.

**Example**: "Get record 1070 from CUSTOMERS"

### `delete_record`
Delete a record from Senzing.

**Example**: "Delete record NEW_001 from CUSTOMERS"

### `why_entities`
Explain why two entities are resolved together (or not).

**Example**: "Why are entity 55 and 91 related?"

### `get_stats`
Get repository statistics.

**Example**: "Show me Senzing statistics"

## Entity Attributes

When adding records, use Senzing's standardized attribute names:

| Category | Attributes |
|----------|------------|
| **Names** | `NAME_FULL`, `NAME_FIRST`, `NAME_LAST`, `NAME_MIDDLE` |
| **Dates** | `DATE_OF_BIRTH` |
| **Addresses** | `ADDR_FULL`, `ADDR_LINE1`, `ADDR_CITY`, `ADDR_STATE`, `ADDR_POSTAL_CODE` |
| **Contact** | `PHONE_NUMBER`, `EMAIL_ADDRESS` |
| **IDs** | `SSN_NUMBER`, `NATIONAL_ID`, `PASSPORT_NUMBER`, `DRIVERS_LICENSE_NUMBER` |

See the [Senzing Entity Specification](https://senzing.com/docs/entity-spec/) for complete details.

## Troubleshooting

### Timeout Error: "Couldn't connect to the MCP server after 60 seconds"

This usually means the Senzing SDK can't be imported. Follow these steps:

#### 1. Verify Environment

```bash
cd ~/senzing && source setupEnv
echo $PYTHONPATH
# Should include: /opt/senzing/er/sdk/python

python3 -c "from senzing_core import SzAbstractFactoryCore; from senzing import SzError; print('✓ OK')"
# Should print: ✓ OK
```

If the import fails, check:
- Senzing is installed: `ls /opt/senzing/er/sdk/python/senzing_core/`
- setupEnv exists: `ls ~/senzing/setupEnv`
- Database exists: `ls ~/senzing/var/sqlite/G2C.db`

#### 2. Test Manual Server Start

```bash
cd ~/senzing && source setupEnv
export SENZING_PROJECT_DIR=~/senzing
export PYTHONPATH=/opt/senzing/er/sdk/python
export LD_LIBRARY_PATH=/home/cdsw/senzing/lib:/opt/senzing/er/lib
python3 -m senzing_mcp_server.server
```

If this fails, fix the error before using with Agent Studio.

#### 3. Check Database Permissions

```bash
ls -la ~/senzing/var/sqlite/G2C.db
# Should be readable: -rw-r--r--

# Fix if needed:
chmod 644 ~/senzing/var/sqlite/G2C.db
```

#### 4. Verify Agent Studio Configuration

Double-check your MCP configuration includes all required environment variables:
- `SENZING_PROJECT_DIR`: `/home/cdsw/senzing`
- `PYTHONPATH`: `/opt/senzing/er/sdk/python`
- `LD_LIBRARY_PATH`: `/home/cdsw/senzing/lib:/opt/senzing/er/lib`

### Common Errors

**"Data source code [CUSTOMERS] does not exist"**
- You need to configure data sources before loading data
- See: [CAI-Senzing-Custom-Runtime setup guide](https://github.com/kevinbtalbert/CAI-Senzing-Custom-Runtime#step-2-configure-data-sources)

**"Unknown resolved entity value 'X'"**
- Entity ID doesn't exist in your database
- Use `sz_explorer` to find valid entity IDs
- Load more data if database is empty

**"engine object has been destroyed"**
- The SDK factory went out of scope (shouldn't happen with current code)
- Report as a bug if you see this

### Database Locked

If you see "database is locked":

```bash
# Stop any running Senzing processes
pkill -f senzing

# Remove lock files if present
rm -f ~/senzing/var/sqlite/*.lock

# Restart Agent Studio workflow
```

## Testing Your Setup

### Diagnostic Script

Download and run the diagnostic script:

```bash
cd ~/senzing && source setupEnv
wget https://raw.githubusercontent.com/kevinbtalbert/senzing-mcp-server/main/debug_mcp_startup.sh
chmod +x debug_mcp_startup.sh
./debug_mcp_startup.sh
```

This will check:
- ✓ Senzing project exists
- ✓ Database is accessible
- ✓ PYTHONPATH is configured
- ✓ Python can import Senzing modules
- ✓ MCP server can initialize

### Test in Agent Studio

Create a simple workflow with a task that uses Senzing:

```
Task: "Search for entities named Robert Smith in Senzing"
```

If configured correctly, the agent will:
1. Connect to the MCP server
2. Call `search_entities` with appropriate parameters
3. Return matching entities

## Performance Notes

### SQLite Limitations

The setup uses SQLite for evaluation/development:
- ✅ Simple, no setup required
- ✅ File-based, easy persistence
- ⚠️ Single-writer (concurrency limited)
- ⚠️ Not suitable for production

For production workloads, migrate to PostgreSQL or MySQL for:
- Better concurrency
- Improved performance (sub-millisecond per record)
- Scalability to millions of records

### Expected Performance

With SQLite:
- ~50ms per record insert
- Search queries: <100ms for small datasets
- Path finding: <500ms for most queries

With PostgreSQL:
- <1ms per record insert
- Search queries: <50ms
- Path finding: <200ms

## Resources

- **[CAI-Senzing-Custom-Runtime](https://github.com/kevinbtalbert/CAI-Senzing-Custom-Runtime)** - Docker runtime setup guide
- [Senzing Documentation](https://senzing.com/docs/)
- [Senzing Python SDK v4 Reference](https://senzing.com/docs/python/)
- [Senzing Entity Specification](https://senzing.com/docs/entity-spec/)
- [Model Context Protocol](https://modelcontextprotocol.io/)

## Support

If you encounter issues:

1. Run the diagnostic script (see [Testing Your Setup](#testing-your-setup))
2. Check [Troubleshooting](#troubleshooting) section
3. Review [CAI-Senzing-Custom-Runtime setup](https://github.com/kevinbtalbert/CAI-Senzing-Custom-Runtime#troubleshooting)
4. Open an issue on GitHub with diagnostic output

## Version

Current version: **0.2.0** (Senzing SDK v4)

See [CHANGELOG.md](CHANGELOG.md) for version history and migration guide.

## License

Apache License 2.0

## Author

Kevin Talbert (ktalbert@cloudera.com)
