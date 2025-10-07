"""Senzing MCP Server - Main server implementation"""

import asyncio
import json
import os
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Senzing SDK v4 imports (loaded from system installation)
from senzing import SzError
from senzing_core import SzAbstractFactoryCore

# Initialize MCP server
app = Server("senzing-mcp-server")

# Global Senzing instances
_sz_factory = None
_sz_engine = None


def get_senzing_config():
    """Build Senzing configuration from environment"""
    project_dir = os.path.expanduser(
        os.getenv("SENZING_PROJECT_DIR", "~/senzing")
    )
    
    return json.dumps({
        "PIPELINE": {
            "CONFIGPATH": f"{project_dir}/etc",
            "SUPPORTPATH": f"{project_dir}/data",
            "RESOURCEPATH": f"{project_dir}/resources"
        },
        "SQL": {
            "CONNECTION": f"sqlite3://na:na@{project_dir}/var/sqlite/G2C.db"
        }
    })


def get_engine():
    """Lazy initialization of Senzing engine using v4 API"""
    global _sz_factory, _sz_engine
    
    if _sz_engine is None:
        config = get_senzing_config()
        # Initialize factory and engine
        # IMPORTANT: Keep factory alive as long as engine is used
        _sz_factory = SzAbstractFactoryCore("senzing-mcp-server", config)
        _sz_engine = _sz_factory.create_engine()
    
    return _sz_engine


# Define available tools
TOOLS = [
    Tool(
        name="add_record",
        description="Add a record to Senzing for entity resolution. Records are automatically resolved against existing entities.",
        inputSchema={
            "type": "object",
            "properties": {
                "data_source": {
                    "type": "string",
                    "description": "Data source code (e.g., 'CUSTOMERS', 'REFERENCE', 'WATCHLIST')"
                },
                "record_id": {
                    "type": "string",
                    "description": "Unique record identifier within the data source"
                },
                "record_data": {
                    "type": "object",
                    "description": "JSON record data with entity attributes (e.g., NAME_FULL, DATE_OF_BIRTH, ADDR_FULL, PHONE_NUMBER)",
                    "properties": {
                        "NAME_FULL": {"type": "string", "description": "Full name"},
                        "NAME_FIRST": {"type": "string", "description": "First name"},
                        "NAME_LAST": {"type": "string", "description": "Last name"},
                        "DATE_OF_BIRTH": {"type": "string", "description": "Date of birth"},
                        "ADDR_FULL": {"type": "string", "description": "Full address"},
                        "ADDR_LINE1": {"type": "string", "description": "Address line 1"},
                        "ADDR_CITY": {"type": "string", "description": "City"},
                        "ADDR_STATE": {"type": "string", "description": "State/Province"},
                        "ADDR_POSTAL_CODE": {"type": "string", "description": "Postal/ZIP code"},
                        "PHONE_NUMBER": {"type": "string", "description": "Phone number"},
                        "EMAIL_ADDRESS": {"type": "string", "description": "Email address"},
                        "SSN_NUMBER": {"type": "string", "description": "Social Security Number"},
                        "NATIONAL_ID": {"type": "string", "description": "National ID number"}
                    }
                }
            },
            "required": ["data_source", "record_id", "record_data"]
        }
    ),
    Tool(
        name="get_entity",
        description="Get complete entity details by entity ID, including all resolved records and relationships.",
        inputSchema={
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "integer",
                    "description": "Senzing entity ID"
                },
                "include_features": {
                    "type": "boolean",
                    "description": "Include feature details (default: true)",
                    "default": True
                }
            },
            "required": ["entity_id"]
        }
    ),
    Tool(
        name="search_entities",
        description="Search for entities by attributes. Returns matching entities ranked by relevance.",
        inputSchema={
            "type": "object",
            "properties": {
                "search_attributes": {
                    "type": "object",
                    "description": "Search attributes (e.g., NAME_FULL, DATE_OF_BIRTH, ADDR_FULL, PHONE_NUMBER)",
                    "properties": {
                        "NAME_FULL": {"type": "string"},
                        "NAME_FIRST": {"type": "string"},
                        "NAME_LAST": {"type": "string"},
                        "DATE_OF_BIRTH": {"type": "string"},
                        "ADDR_FULL": {"type": "string"},
                        "PHONE_NUMBER": {"type": "string"},
                        "EMAIL_ADDRESS": {"type": "string"},
                        "SSN_NUMBER": {"type": "string"}
                    }
                }
            },
            "required": ["search_attributes"]
        }
    ),
    Tool(
        name="find_path",
        description="Find the relationship path between two entities. Useful for discovering connections.",
        inputSchema={
            "type": "object",
            "properties": {
                "start_entity_id": {
                    "type": "integer",
                    "description": "Starting entity ID"
                },
                "end_entity_id": {
                    "type": "integer",
                    "description": "Ending entity ID"
                },
                "max_degrees": {
                    "type": "integer",
                    "description": "Maximum degrees of separation (default: 3, max: 10)",
                    "default": 3,
                    "minimum": 1,
                    "maximum": 10
                }
            },
            "required": ["start_entity_id", "end_entity_id"]
        }
    ),
    Tool(
        name="find_network",
        description="Find a network of related entities around the specified entity IDs.",
        inputSchema={
            "type": "object",
            "properties": {
                "entity_ids": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "List of entity IDs to find network around",
                    "minItems": 1
                },
                "max_degrees": {
                    "type": "integer",
                    "description": "Maximum degrees of separation (default: 2, max: 5)",
                    "default": 2,
                    "minimum": 1,
                    "maximum": 5
                },
                "max_entities": {
                    "type": "integer",
                    "description": "Maximum number of entities to return (default: 100)",
                    "default": 100
                }
            },
            "required": ["entity_ids"]
        }
    ),
    Tool(
        name="get_record",
        description="Get a specific record by data source and record ID.",
        inputSchema={
            "type": "object",
            "properties": {
                "data_source": {
                    "type": "string",
                    "description": "Data source code"
                },
                "record_id": {
                    "type": "string",
                    "description": "Record identifier"
                }
            },
            "required": ["data_source", "record_id"]
        }
    ),
    Tool(
        name="delete_record",
        description="Delete a record from Senzing. Entity resolution will be recalculated.",
        inputSchema={
            "type": "object",
            "properties": {
                "data_source": {
                    "type": "string",
                    "description": "Data source code"
                },
                "record_id": {
                    "type": "string",
                    "description": "Record identifier"
                }
            },
            "required": ["data_source", "record_id"]
        }
    ),
    Tool(
        name="why_entities",
        description="Explain why two entities are or are not resolved together. Provides detailed scoring and feature analysis.",
        inputSchema={
            "type": "object",
            "properties": {
                "entity_id_1": {
                    "type": "integer",
                    "description": "First entity ID"
                },
                "entity_id_2": {
                    "type": "integer",
                    "description": "Second entity ID"
                }
            },
            "required": ["entity_id_1", "entity_id_2"]
        }
    ),
    Tool(
        name="get_stats",
        description="Get Senzing repository statistics including record counts, entity counts, and data source breakdowns.",
        inputSchema={
            "type": "object",
            "properties": {}
        }
    )
]


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available Senzing tools"""
    return TOOLS


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls to Senzing SDK"""
    
    try:
        engine = get_engine()
        
        if name == "add_record":
            data_source = arguments["data_source"]
            record_id = arguments["record_id"]
            record_data = json.dumps(arguments["record_data"])
            
            engine.add_record(data_source, record_id, record_data)
            return [TextContent(
                type="text",
                text=f"✓ Record {record_id} added successfully to {data_source}"
            )]
        
        elif name == "get_entity":
            entity_id = arguments["entity_id"]
            result = engine.get_entity_by_entity_id(entity_id)
            
            return [TextContent(
                type="text",
                text=result
            )]
        
        elif name == "search_entities":
            search_attrs = json.dumps(arguments["search_attributes"])
            result = engine.search_by_attributes(search_attrs)
            
            return [TextContent(
                type="text",
                text=result
            )]
        
        elif name == "find_path":
            start_id = arguments["start_entity_id"]
            end_id = arguments["end_entity_id"]
            max_degrees = arguments.get("max_degrees", 3)
            
            result = engine.find_path_by_entity_id(start_id, end_id, max_degrees)
            
            return [TextContent(
                type="text",
                text=result
            )]
        
        elif name == "find_network":
            entity_ids = json.dumps(arguments["entity_ids"])
            max_degrees = arguments.get("max_degrees", 2)
            max_entities = arguments.get("max_entities", 100)
            
            result = engine.find_network_by_entity_id(entity_ids, max_degrees, max_entities)
            
            return [TextContent(
                type="text",
                text=result
            )]
        
        elif name == "get_record":
            data_source = arguments["data_source"]
            record_id = arguments["record_id"]
            
            result = engine.get_record(data_source, record_id)
            
            return [TextContent(
                type="text",
                text=result
            )]
        
        elif name == "delete_record":
            data_source = arguments["data_source"]
            record_id = arguments["record_id"]
            
            engine.delete_record(data_source, record_id)
            
            return [TextContent(
                type="text",
                text=f"✓ Record {record_id} deleted from {data_source}"
            )]
        
        elif name == "why_entities":
            entity_id_1 = arguments["entity_id_1"]
            entity_id_2 = arguments["entity_id_2"]
            
            result = engine.why_entities(entity_id_1, entity_id_2)
            
            return [TextContent(
                type="text",
                text=result
            )]
        
        elif name == "get_stats":
            result = engine.get_stats()
            
            return [TextContent(
                type="text",
                text=result
            )]
        
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"❌ Error: {str(e)}"
        )]


async def run():
    """Run the MCP server"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


def main():
    """Main entry point"""
    # Ensure Senzing environment is set up
    if not os.getenv("SENZING_PROJECT_DIR"):
        os.environ["SENZING_PROJECT_DIR"] = "~/senzing"
    
    # Verify Senzing is available
    try:
        from senzing_core import SzAbstractFactoryCore
        from senzing import SzError
    except ImportError as e:
        print(f"Error: Senzing SDK not found. Please ensure:")
        print("  1. Senzing SDK is installed")
        print("  2. PYTHONPATH includes Senzing Python SDK path")
        print("  3. Senzing environment is sourced (source ~/senzing/setupEnv)")
        print(f"  Current PYTHONPATH: {os.getenv('PYTHONPATH', 'Not set')}")
        print(f"  Project directory: {os.getenv('SENZING_PROJECT_DIR', 'Not set')}")
        raise e
    
    asyncio.run(run())


if __name__ == "__main__":
    main()

