import langgraph
import sys

print(f"Python version: {sys.version}")
print(f"Langgraph module location: {langgraph.__file__}")
print(f"Langgraph version: {langgraph.__version__ if hasattr(langgraph, '__version__') else 'Version not found'}")

try:
    import langgraph.prebuilt
    print(f"langgraph.prebuilt location: {langgraph.prebuilt.__file__}")
    print("\n--- Contents of langgraph.prebuilt ---")
    print(dir(langgraph.prebuilt))
    print("--------------------------------------\n")

    # Test the problematic import directly
    try:
        from langgraph.prebuilt.agent_executor.core import create_agent_executor
        print("SUCCESSFULLY imported create_agent_executor from langgraph.prebuilt.agent_executor.core")
    except ImportError as e1:
        print(f"FAILED to import from langgraph.prebuilt.agent_executor.core: {e1}")
        try:
            from langgraph.prebuilt import create_agent_executor
            print("SUCCESSFULLY imported create_agent_executor from langgraph.prebuilt")
        except ImportError as e2:
            print(f"FAILED to import from langgraph.prebuilt: {e2}")

except ImportError as e:
    print(f"Could not import langgraph.prebuilt: {e}")
except AttributeError as e:
    print(f"Attribute error, possibly related to langgraph.prebuilt structure: {e}")