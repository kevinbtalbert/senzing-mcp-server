# Senzing MCP Server

A Model Context Protocol (MCP) server that provides AI assistants with access to Senzing Entity Resolution capabilities using the **Senzing v4 SDK**.

## Overview

This MCP server exposes Senzing's powerful entity resolution engine through the Model Context Protocol, enabling AI assistants like Claude to perform:

- **Entity Resolution**: Add records and automatically resolve them against existing entities
- **Entity Search**: Find entities by attributes (name, address, phone, etc.)
- **Relationship Discovery**: Find paths and networks between entities
- **Explainability**: Understand why entities are resolved together
- **Statistics & Monitoring**: View repository statistics and performance metrics

Works seamlessly with the [CAI-Senzing-Custom-Runtime](https://github.com/kevinbtalbert/CAI-Senzing-Custom-Runtime) Docker environment for Cloudera ML workspaces.

## Architecture

### Embedded SDK Design

The MCP server uses an **embedded architecture** - there is **no separate Senzing server process**. Instead, the Senzing SDK runs directly inside the MCP server's Python process as a native library.

```
┌─────────────────────────────────────────────────────────────┐
│                    Claude Desktop                            │
│                  (MCP Client - Local)                        │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            │ MCP Protocol (stdio/JSON-RPC)
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
│                        │ Direct file I/O / SQL               │
└────────────────────────┼─────────────────────────────────────┘
                         │
                         ▼
          ┌──────────────────────────────────┐
          │  Database (Persistent Storage)   │
          │                                   │
          │  SQLite:                          │
          │    ~/senzing/var/sqlite/G2C.db   │
          │                                   │
          │  Or PostgreSQL/MySQL for prod    │
          └──────────────────────────────────┘
```

### How It Works

1. **MCP Client (Claude Desktop)** sends natural language requests via stdio
2. **MCP Server** translates requests into Senzing SDK function calls
3. **Senzing SDK** (embedded library) processes entity resolution in-process
4. **Database** is accessed directly via file I/O (SQLite) or SQL connection (PostgreSQL/MySQL)
5. **Results** flow back through MCP protocol to Claude

### Key Characteristics

- **No Network Overhead**: All Senzing operations are in-process function calls
- **No Daemon Required**: Senzing doesn't run as a background service
- **Direct Database Access**: SQLite file or SQL database accessed directly
- **Single Process**: MCP server and Senzing SDK run in the same Python process
- **Fast Response Times**: No HTTP/RPC overhead, minimal latency

### Deployment Models

#### Local Development (Current Setup)
```
Claude Desktop (Mac) → MCP Server (Cloudera ML) → Senzing SDK → SQLite
```
- MCP server runs in Cloudera ML workspace
- Accesses persistent SQLite database at `~/senzing/var/sqlite/G2C.db`
- Single user, development/evaluation use case

#### Production (Future Enhancement)
```
Multiple Clients → Load Balancer → Multiple MCP Servers → PostgreSQL/MySQL
```
- Replace SQLite with PostgreSQL or MySQL
- Run multiple MCP server instances for horizontal scaling
- Shared database enables concurrent access
- Better performance for high-volume workloads

### Security Considerations

Since the MCP server has **direct database access**:
- ✅ No exposed network ports (uses stdio for MCP)
- ✅ Authentication handled by MCP client
- ✅ Database access controlled by file permissions (SQLite) or SQL credentials
- ⚠️ Grant least-privilege access to the Senzing project directory
- ⚠️ For production, use database-level access controls and encryption

## Prerequisites

- **Senzing SDK v4**: Must be installed and configured
  - For installation instructions, see the [Senzing Quickstart Guide](https://senzing.com/docs/quickstart/quickstart_api/)
  - **Or use the [CAI-Senzing-Custom-Runtime](https://github.com/kevinbtalbert/CAI-Senzing-Custom-Runtime)** - Docker runtime with Senzing pre-installed
  - Senzing project must be initialized in a persistent location (e.g., `~/senzing`)
- **Python 3.10+**
- **MCP Client**: Claude Desktop, or any MCP-compatible client

## Quick Start with CAI-Senzing-Custom-Runtime

The fastest way to get started is to use the pre-built Docker runtime. The MCP server will connect directly to your Senzing SDK installation (see [Architecture](#architecture) for details).

1. **Follow the [CAI-Senzing-Custom-Runtime setup guide](https://github.com/kevinbtalbert/CAI-Senzing-Custom-Runtime#getting-started-with-sample-data)** to:
   - Create your persistent Senzing project at `~/senzing`
   - Load sample data (truth set)
   - Verify everything works with `sz_explorer`

2. **Configure Claude Desktop** (see Configuration section below) to connect to your Senzing project

3. **Start using Senzing in Claude!** Try queries like:
   - "Search for entities named Robert Smith"
   - "Get entity 1"
   - "Find the path between entity 1 and entity 100"

> **Note**: The MCP server uses an embedded architecture - it loads the Senzing SDK directly as a library and accesses your database. No separate server process is required.

## Installation

### Option 1: Install from GitHub (Recommended)

```bash
pip install git+https://github.com/kevinbtalbert/senzing-mcp-server@main
```

### Option 2: Install from source

```bash
git clone https://github.com/kevinbtalbert/senzing-mcp-server.git
cd senzing-mcp-server
pip install -e .
```

### Option 3: Use with uvx (No installation needed)

```bash
uvx --from git+https://github.com/kevinbtalbert/senzing-mcp-server@main run-server
```

## Configuration

### Claude Desktop Configuration

Add this to your Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`  
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

#### For Cloudera ML / Docker Runtime Users

If you're using the [CAI-Senzing-Custom-Runtime](https://github.com/kevinbtalbert/CAI-Senzing-Custom-Runtime):

```json
{
  "mcpServers": {
    "senzing": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/kevinbtalbert/senzing-mcp-server@main",
        "run-server"
      ],
      "env": {
        "MCP_TRANSPORT": "stdio",
        "SENZING_PROJECT_DIR": "/home/cdsw/senzing",
        "PYTHONPATH": "/opt/senzing/er/sdk/python"
      }
    }
  }
}
```

#### For Local Senzing Installation

If you have Senzing installed locally:

```json
{
  "mcpServers": {
    "senzing": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/kevinbtalbert/senzing-mcp-server@main",
        "run-server"
      ],
      "env": {
        "MCP_TRANSPORT": "stdio",
        "SENZING_PROJECT_DIR": "~/senzing",
        "PYTHONPATH": "/opt/senzing/er/sdk/python"
      }
    }
  }
}
```

### Environment Variables

- `SENZING_PROJECT_DIR`: Path to your Senzing project (default: `~/senzing`)
  - For Cloudera ML: `/home/cdsw/senzing`
  - For local: `~/senzing` or any persistent directory
- `PYTHONPATH`: Must include path to Senzing Python SDK (typically `/opt/senzing/er/sdk/python`)

## Available Tools

### `add_record`
Add a record to Senzing for entity resolution.

**Example**:
```
Add a customer record:
- Data source: CUSTOMERS
- Record ID: 1001
- Name: John Smith
- DOB: 1985-03-15
- Address: 123 Main St, Boston MA 02101
- Phone: 617-555-0100
```

### `get_entity`
Get complete details about a resolved entity.

**Example**:
```
Get entity 42
```

### `search_entities`
Search for entities by attributes.

**Example**:
```
Search for entities with:
- Name: Jane Doe
- City: San Francisco
```

### `find_path`
Find relationship paths between two entities.

**Example**:
```
Find the path between entity 100 and entity 250
```

### `find_network`
Discover networks of related entities.

**Example**:
```
Find the network around entities 42, 84, and 126 within 2 degrees
```

### `get_record`
Retrieve a specific record.

**Example**:
```
Get record 1001 from CUSTOMERS
```

### `delete_record`
Delete a record from Senzing.

**Example**:
```
Delete record 1001 from CUSTOMERS
```

### `why_entities`
Explain why two entities are resolved together (or not).

**Example**:
```
Why are entity 42 and entity 84 resolved together?
```

### `get_stats`
Get repository statistics.

**Example**:
```
Show me Senzing statistics
```

> **Note**: Data source configuration (adding/listing data sources) should be done using command-line tools like `sz_configtool` in your Senzing project. See the [CAI-Senzing-Custom-Runtime README](https://github.com/kevinbtalbert/CAI-Senzing-Custom-Runtime#getting-started-with-sample-data) for details.

## Entity Specification

When adding records, use Senzing's standardized attribute names:

### Name Attributes
- `NAME_FULL`: Full name
- `NAME_FIRST`: First/given name
- `NAME_LAST`: Last/family name
- `NAME_MIDDLE`: Middle name

### Date Attributes
- `DATE_OF_BIRTH`: Date of birth

### Address Attributes
- `ADDR_FULL`: Complete address
- `ADDR_LINE1`: Street address
- `ADDR_CITY`: City
- `ADDR_STATE`: State/Province
- `ADDR_POSTAL_CODE`: Postal/ZIP code
- `ADDR_COUNTRY`: Country

### Contact Attributes
- `PHONE_NUMBER`: Phone number
- `EMAIL_ADDRESS`: Email address

### Identifier Attributes
- `SSN_NUMBER`: Social Security Number
- `NATIONAL_ID`: National ID number
- `PASSPORT_NUMBER`: Passport number
- `DRIVERS_LICENSE_NUMBER`: Driver's license

For complete specification, see [Senzing Entity Specification](https://senzing.com/docs/entity-spec/).

## Usage Examples

Once configured in Claude Desktop, you can interact naturally:

**Example 1: Adding Records**
> "Add a customer record for Jane Smith, born 1990-05-20, living at 456 Oak Ave, Chicago IL 60601, phone 312-555-0200"

**Example 2: Searching**
> "Search for anyone named Robert Johnson in California"

**Example 3: Finding Connections**
> "Is there any connection between entity 42 and entity 100?"

**Example 4: Analysis**
> "Show me statistics about the data in Senzing"

## Development

### Running Tests

```bash
pip install pytest
pytest tests/
```

### Project Structure

```
senzing-mcp-server/
├── pyproject.toml
├── README.md
└── src/
    └── senzing_mcp_server/
        ├── __init__.py
        └── server.py
```

## Troubleshooting

### "Senzing SDK not found"

Ensure:
1. Senzing SDK v4 is installed: `/opt/senzing/er/bin/sz_create_project`
2. `PYTHONPATH` includes Senzing SDK: `/opt/senzing/er/sdk/python`
3. Senzing project is initialized in a persistent directory
4. If using Cloudera ML, source the environment: `source ~/senzing/setupEnv`

**Quick test:**
```bash
python3 -c "from senzing_core import SzAbstractFactoryCore; from senzing import SzError; print('✓ Senzing v4 SDK available')"
```

### "Module not found" or Import Errors

- Make sure you've sourced the Senzing environment before starting Claude Desktop
- In Cloudera ML: `cd ~/senzing && source setupEnv`
- Check PYTHONPATH: `echo $PYTHONPATH` should include `/opt/senzing/er/sdk/python`

### Connection Issues

- Verify Claude Desktop configuration file syntax (JSON must be valid)
- Check that all environment variables are set correctly
- Ensure `SENZING_PROJECT_DIR` points to an existing, initialized project
- Restart Claude Desktop after configuration changes

### Database/Data Issues

- Verify data is loaded: `ls -lh ~/senzing/var/sqlite/G2C.db`
- Check data sources are configured: `sz_configtool` (in Senzing environment)
- View loaded data: `sz_explorer` (in Senzing environment)

## Using with Cloudera ML Workspaces

If you're running this in a Cloudera ML workspace with the CAI-Senzing-Custom-Runtime:

### Setup in Cloudera ML

1. **Create your persistent project** (if not already done):
   ```bash
   /opt/senzing/er/bin/sz_create_project ~/senzing
   cd ~/senzing && source setupEnv && ./bin/sz_setup_config
   ```

2. **Load sample data** (see [runtime README](https://github.com/kevinbtalbert/CAI-Senzing-Custom-Runtime#getting-started-with-sample-data))

### How It Works

The MCP server architecture enables seamless integration between Claude Desktop (running on your Mac) and Senzing (running in your Cloudera ML workspace):

```
┌──────────────────┐           ┌─────────────────────────────────┐
│ Claude Desktop   │  stdio    │  Cloudera ML Workspace          │
│ (Your Mac)       │◄─────────►│                                  │
│                  │  via uvx  │  ┌────────────────────────────┐ │
│ - Natural        │           │  │ senzing-mcp-server         │ │
│   language       │           │  │ (Python process)           │ │
│   queries        │           │  │                            │ │
│                  │           │  │ ┌────────────────────────┐ │ │
│                  │           │  │ │ Senzing SDK v4         │ │ │
│                  │           │  │ │ (Embedded library)     │ │ │
│                  │           │  │ └──────────┬─────────────┘ │ │
│                  │           │  └────────────┼───────────────┘ │
│                  │           │               │                 │
│                  │           │               ▼                 │
│                  │           │  ┌──────────────────────────┐  │
│                  │           │  │ ~/senzing/var/sqlite/    │  │
│                  │           │  │ G2C.db (Persistent)      │  │
│                  │           │  └──────────────────────────┘  │
└──────────────────┘           └─────────────────────────────────┘
```

**Key Points**:
- MCP server runs **inside your Cloudera ML workspace** (not on your Mac)
- Claude Desktop launches it via `uvx` and communicates over stdio
- Senzing SDK is **embedded** in the MCP server process
- Database is accessed **directly** within the workspace
- No network ports exposed, no separate servers needed

### Claude Desktop Configuration

3. **Configure Claude Desktop** with `SENZING_PROJECT_DIR="/home/cdsw/senzing"`

4. **Access from Claude Desktop** - The MCP server will connect to your Cloudera ML workspace's Senzing instance via the embedded SDK

## Testing Your Setup

Verify the MCP server can connect to your Senzing instance:

### Using the Test Script (Recommended)

```bash
# Source the Senzing environment
cd ~/senzing && source setupEnv

# Run the comprehensive test
python3 test_connection.py
```

This will check:
- ✓ Required Python modules can be imported
- ✓ Environment variables are set correctly
- ✓ Senzing project exists and is configured
- ✓ Engine can initialize and connect to the database
- ✓ Data is loaded (if applicable)

### Quick Manual Test

```bash
# Source the Senzing environment
cd ~/senzing && source setupEnv

# Test the server
python3 -c "
from senzing_mcp_server.server import get_engine
engine = get_engine()
stats = engine.get_stats()
print('✓ MCP Server connected successfully!')
print(stats)
"
```

## Resources

- **[CAI-Senzing-Custom-Runtime](https://github.com/kevinbtalbert/CAI-Senzing-Custom-Runtime)** - Docker runtime with Senzing pre-installed
- [Senzing Documentation](https://senzing.com/docs/)
- [Senzing Quickstart Guide](https://senzing.com/docs/quickstart/quickstart_api/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Senzing Entity Specification](https://senzing.com/docs/entity-spec/)
- [Senzing Python SDK v4 Reference](https://senzing.com/docs/python/)

## License

Apache License 2.0

## Author

Kevin Talbert (ktalbert@cloudera.com)
