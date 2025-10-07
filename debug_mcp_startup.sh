#!/bin/bash
# Debug script for MCP server startup issues in Agent Studio

echo "======================================"
echo "MCP Server Startup Diagnostic"
echo "======================================"
echo ""

echo "1. Checking Senzing Project Directory:"
echo "   SENZING_PROJECT_DIR=${SENZING_PROJECT_DIR:-<not set>}"
PROJECT_DIR="${SENZING_PROJECT_DIR:-$HOME/senzing}"
echo "   Using: $PROJECT_DIR"

if [ -d "$PROJECT_DIR" ]; then
    echo "   ✓ Project directory exists"
    echo "   Database: $(ls -lh $PROJECT_DIR/var/sqlite/G2C.db 2>/dev/null || echo 'NOT FOUND')"
else
    echo "   ✗ Project directory does NOT exist"
    echo "   Run: /opt/senzing/er/bin/sz_create_project $PROJECT_DIR"
fi
echo ""

echo "2. Checking PYTHONPATH:"
echo "   PYTHONPATH=$PYTHONPATH"
if echo "$PYTHONPATH" | grep -q "senzing"; then
    echo "   ✓ PYTHONPATH includes Senzing SDK"
else
    echo "   ✗ PYTHONPATH does NOT include Senzing SDK"
    echo "   Source setupEnv: cd $PROJECT_DIR && source setupEnv"
fi
echo ""

echo "3. Testing Python Imports:"
python3 << 'EOF'
import sys
import os

# Add Senzing to path if not already there
senzing_sdk = "/opt/senzing/er/sdk/python"
if senzing_sdk not in sys.path and os.path.exists(senzing_sdk):
    sys.path.insert(0, senzing_sdk)

print("   Python path includes:")
for p in sys.path[:5]:
    if 'senzing' in p.lower():
        print(f"     - {p}")

try:
    from senzing_core import SzAbstractFactoryCore
    print("   ✓ Can import SzAbstractFactoryCore")
except ImportError as e:
    print(f"   ✗ Cannot import SzAbstractFactoryCore: {e}")
    sys.exit(1)

try:
    from senzing import SzError
    print("   ✓ Can import SzError")
except ImportError as e:
    print(f"   ✗ Cannot import SzError: {e}")
    sys.exit(1)

print("   ✓ All Senzing imports successful")
EOF

if [ $? -ne 0 ]; then
    echo ""
    echo "   Import failed! Make sure to source setupEnv:"
    echo "   cd $PROJECT_DIR && source setupEnv"
    exit 1
fi
echo ""

echo "4. Testing MCP Server Initialization:"
python3 << 'EOF'
import sys
import os

# Add Senzing to path
senzing_sdk = "/opt/senzing/er/sdk/python"
if senzing_sdk not in sys.path and os.path.exists(senzing_sdk):
    sys.path.insert(0, senzing_sdk)

try:
    # Set project directory
    project_dir = os.environ.get('SENZING_PROJECT_DIR', os.path.expanduser('~/senzing'))
    os.environ['SENZING_PROJECT_DIR'] = project_dir
    
    # Try to import the server module
    from senzing_mcp_server.server import get_senzing_config, get_engine
    print(f"   ✓ Can import MCP server modules")
    
    # Try to get config
    config = get_senzing_config()
    print(f"   ✓ Config generated successfully")
    print(f"   Project: {project_dir}")
    
    # Try to initialize engine
    print("   Initializing Senzing engine...")
    engine = get_engine()
    print("   ✓ Engine initialized successfully")
    
    # Get stats to verify it works
    stats = engine.get_stats()
    print("   ✓ Engine is functional")
    
except Exception as e:
    print(f"   ✗ MCP server initialization failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
EOF

if [ $? -eq 0 ]; then
    echo ""
    echo "======================================"
    echo "✓ All checks passed!"
    echo "======================================"
    echo ""
    echo "MCP server should work. If you still see timeout errors:"
    echo "1. Make sure Agent Studio's MCP config includes:"
    echo "   env:"
    echo "     SENZING_PROJECT_DIR: /home/cdsw/senzing"
    echo "     PYTHONPATH: /opt/senzing/er/sdk/python"
    echo ""
    echo "2. Try running the MCP server manually:"
    echo "   cd $PROJECT_DIR && source setupEnv"
    echo "   SENZING_PROJECT_DIR=$PROJECT_DIR python -m senzing_mcp_server.server"
else
    echo ""
    echo "======================================"
    echo "✗ Diagnostics failed"
    echo "======================================"
    echo ""
    echo "Fix the issues above before using MCP server"
fi

