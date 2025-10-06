#!/usr/bin/env python3
"""
Simple test to verify the single agent demo structure
"""

def test_imports():
    """Test that all modules can be imported"""
    try:
        # Test tools imports
        from tools import ToolSpec, Tool, RAGArgs, WeatherArgs, DBArgs, SimpleRAG
        from tools import rag_tool_factory, weather_tool_factory, db_tool_factory
        print("✓ Tools module imports successful")
        
        # Test agent imports
        from agent import Registry, SingleAgent
        print("✓ Agent module imports successful")
        
        # Test main imports
        from main import reg, agent
        print("✓ Main module imports successful")
        
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def test_tool_creation():
    """Test that tools can be created"""
    try:
        from tools import rag_tool_factory, weather_tool_factory, db_tool_factory
        
        # Test RAG tool
        rag_tool = rag_tool_factory()
        print(f"✓ RAG tool created: {rag_tool.spec.name}")
        
        # Test Weather tool
        weather_tool = weather_tool_factory("https://api.open-meteo.com/v1/forecast")
        print(f"✓ Weather tool created: {weather_tool.spec.name}")
        
        # Test DB tool
        db_tool = db_tool_factory("test_data.db")
        print(f"✓ DB tool created: {db_tool.spec.name}")
        
        return True
    except Exception as e:
        print(f"✗ Tool creation error: {e}")
        return False

def test_registry():
    """Test registry functionality"""
    try:
        from agent import Registry
        from tools import rag_tool_factory
        
        registry = Registry()
        rag_tool = rag_tool_factory()
        registry.register(rag_tool)
        
        print(f"✓ Registry has {len(registry.tools)} tools")
        print(f"✓ Registered tool: {list(registry.tools.keys())}")
        
        return True
    except Exception as e:
        print(f"✗ Registry error: {e}")
        return False

if __name__ == "__main__":
    print("Testing Single Agent Demo Structure...")
    print("=" * 40)
    
    tests = [
        ("Import Test", test_imports),
        ("Tool Creation Test", test_tool_creation),
        ("Registry Test", test_registry),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        if test_func():
            passed += 1
        else:
            print(f"  {test_name} FAILED")
    
    print("\n" + "=" * 40)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! Demo structure is correct.")
    else:
        print("❌ Some tests failed. Check the errors above.")
