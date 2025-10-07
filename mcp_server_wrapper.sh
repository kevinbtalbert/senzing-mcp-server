#!/bin/bash
# Wrapper script to ensure Senzing environment is properly configured
# before starting the MCP server for Agent Studio

set -e  # Exit on error

# Default project directory
PROJECT_DIR="${SENZING_PROJECT_DIR:-$HOME/senzing}"
export SENZING_PROJECT_DIR="$PROJECT_DIR"

# Ensure Senzing SDK is in PYTHONPATH
SENZING_SDK_PATH="/opt/senzing/er/sdk/python"
if [ -d "$SENZING_SDK_PATH" ]; then
    if [[ ":$PYTHONPATH:" != *":$SENZING_SDK_PATH:"* ]]; then
        export PYTHONPATH="$SENZING_SDK_PATH${PYTHONPATH:+:$PYTHONPATH}"
    fi
fi

# Source setupEnv if it exists and we're in an interactive shell
if [ -f "$PROJECT_DIR/setupEnv" ]; then
    # Extract and export key environment variables from setupEnv
    # without actually sourcing it (which can cause issues in non-interactive shells)
    
    # Add Senzing tools to PATH
    if [ -d "$PROJECT_DIR/bin" ]; then
        export PATH="$PROJECT_DIR/bin:$PATH"
    fi
    
    # Set LD_LIBRARY_PATH for Senzing native libraries
    if [ -d "$PROJECT_DIR/lib" ]; then
        export LD_LIBRARY_PATH="$PROJECT_DIR/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
    fi
    if [ -d "/opt/senzing/er/lib" ]; then
        export LD_LIBRARY_PATH="/opt/senzing/er/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
    fi
fi

# Verify project exists
if [ ! -d "$PROJECT_DIR" ]; then
    echo "ERROR: Senzing project directory not found: $PROJECT_DIR" >&2
    echo "Create it with: /opt/senzing/er/bin/sz_create_project $PROJECT_DIR" >&2
    exit 1
fi

# Verify database exists
if [ ! -f "$PROJECT_DIR/var/sqlite/G2C.db" ]; then
    echo "ERROR: Senzing database not found: $PROJECT_DIR/var/sqlite/G2C.db" >&2
    echo "Initialize it with: cd $PROJECT_DIR && source setupEnv && ./bin/sz_setup_config" >&2
    exit 1
fi

# Log environment for debugging
echo "Starting Senzing MCP Server..." >&2
echo "  Project: $SENZING_PROJECT_DIR" >&2
echo "  Database: $(du -h $PROJECT_DIR/var/sqlite/G2C.db 2>/dev/null | cut -f1)" >&2

# Start the MCP server
exec python3 -m senzing_mcp_server.server "$@"

