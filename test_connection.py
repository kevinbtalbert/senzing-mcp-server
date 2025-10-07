#!/usr/bin/env python3
"""Test script to verify Senzing MCP Server can connect to your Senzing instance"""

import json
import os
import sys


def test_imports():
    """Test that required modules can be imported"""
    print("Testing imports...")
    try:
        from senzing import SzError
        print("  ✓ senzing module imported")
    except ImportError as e:
        print(f"  ✗ Failed to import senzing: {e}")
        return False
    
    try:
        from senzing_core import SzAbstractFactoryCore
        print("  ✓ senzing_core module imported")
    except ImportError as e:
        print(f"  ✗ Failed to import senzing_core: {e}")
        return False
    
    return True


def test_environment():
    """Test environment variables"""
    print("\nTesting environment...")
    
    pythonpath = os.getenv("PYTHONPATH", "")
    if "/opt/senzing/er/sdk/python" in pythonpath:
        print(f"  ✓ PYTHONPATH includes Senzing SDK: {pythonpath}")
    else:
        print(f"  ⚠ PYTHONPATH may be missing Senzing SDK")
        print(f"    Current: {pythonpath}")
        print(f"    Expected to include: /opt/senzing/er/sdk/python")
    
    project_dir = os.path.expanduser(os.getenv("SENZING_PROJECT_DIR", "~/senzing"))
    print(f"  Project directory: {project_dir}")
    
    if os.path.exists(project_dir):
        print(f"  ✓ Project directory exists")
        
        # Check for key files
        config_path = os.path.join(project_dir, "etc")
        db_path = os.path.join(project_dir, "var/sqlite/G2C.db")
        
        if os.path.exists(config_path):
            print(f"  ✓ Configuration directory exists: {config_path}")
        else:
            print(f"  ✗ Configuration directory missing: {config_path}")
        
        if os.path.exists(db_path):
            size = os.path.getsize(db_path)
            print(f"  ✓ Database exists: {db_path} ({size:,} bytes)")
        else:
            print(f"  ⚠ Database not found: {db_path}")
            print(f"    Run sz_setup_config to initialize")
    else:
        print(f"  ✗ Project directory does not exist")
        print(f"    Create it with: /opt/senzing/er/bin/sz_create_project {project_dir}")
        return False
    
    return True


def test_engine():
    """Test Senzing engine initialization"""
    print("\nTesting Senzing engine...")
    
    try:
        from senzing_mcp_server.server import get_engine, get_senzing_config
        
        # Get configuration
        config = get_senzing_config()
        config_obj = json.loads(config)
        print(f"  Configuration:")
        print(f"    CONFIGPATH: {config_obj['PIPELINE']['CONFIGPATH']}")
        print(f"    SUPPORTPATH: {config_obj['PIPELINE']['SUPPORTPATH']}")
        print(f"    DATABASE: {config_obj['SQL']['CONNECTION']}")
        
        # Initialize engine
        engine = get_engine()
        print("  ✓ Engine initialized successfully")
        
        # Get stats
        stats_json = engine.get_stats()
        stats = json.loads(stats_json)
        
        # Parse workload stats
        workload = stats.get("workload", {})
        added_records = workload.get("addedRecords", 0)
        
        print(f"\n  Engine Statistics:")
        print(f"    Records added: {added_records:,}")
        
        if added_records > 0:
            print(f"  ✓ Database has data!")
        else:
            print(f"  ⚠ Database is empty - load data with sz_file_loader")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Engine initialization failed: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("Senzing MCP Server Connection Test")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("Environment", test_environment()))
    results.append(("Engine", test_engine()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {name}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n✓ All tests passed! Your MCP server is ready to use.")
        print("\nNext steps:")
        print("  1. Configure Claude Desktop (see README.md)")
        print("  2. Restart Claude Desktop")
        print("  3. Try: 'Search for entities in Senzing'")
        return 0
    else:
        print("\n✗ Some tests failed. Please review the errors above.")
        print("\nTroubleshooting:")
        print("  1. Source Senzing environment: cd ~/senzing && source setupEnv")
        print("  2. Check project exists: ls -la ~/senzing")
        print("  3. See README.md for detailed setup instructions")
        return 1


if __name__ == "__main__":
    sys.exit(main())

