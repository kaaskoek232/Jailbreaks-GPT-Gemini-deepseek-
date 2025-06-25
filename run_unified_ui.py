#!/usr/bin/env python3
"""
Unified MCP Agent UI Launcher
Simple launcher script to run the unified UI with proper error handling
"""

import sys
import os
import traceback

def main():
    """Main launcher function"""
    print("🚀 Starting Unified MCP Agent System...")
    print("=" * 50)
    
    try:
        # Check if tkinter is available
        try:
            import tkinter as tk
            print("✅ Tkinter GUI framework available")
        except ImportError:
            print("❌ Tkinter not available. Please install tkinter for GUI support.")
            print("   On Ubuntu/Debian: sudo apt-get install python3-tk")
            print("   On Windows: Usually included with Python")
            print("   On macOS: Usually included with Python")
            return 1
        
        # Import the unified UI
        try:
            from unified_agent_ui import main as ui_main
            print("✅ Unified UI module loaded successfully")
        except ImportError as e:
            print(f"❌ Failed to import unified UI: {e}")
            print("   Make sure all required files are in the same directory")
            return 1
        
        # Check for required components
        required_files = [
            'agent_connection_manager.py',
            'mcp_agent_integration.py', 
            'custom_mcp_server.py'
        ]
        
        missing_files = []
        for file in required_files:
            if not os.path.exists(file):
                missing_files.append(file)
        
        if missing_files:
            print(f"⚠️  Missing required files: {', '.join(missing_files)}")
            print("   Some features may not work properly")
        else:
            print("✅ All required components found")
        
        print("\n🎯 Launching Unified MCP Agent Dashboard...")
        print("   - Dashboard: Real-time system monitoring")
        print("   - Connection: SSH/RunPod management")
        print("   - Memory: Persistent storage operations")
        print("   - Search: Multi-source search capabilities")
        print("   - Feedback: User feedback and analytics")
        print("   - Heartbeat: Layer communication monitoring")
        print("   - Logs: System activity logs")
        print("\n💓 Heartbeat system will maintain context awareness")
        print("   All layers communicate every 2 seconds")
        print("   Timeout detection at 10 seconds")
        print("   Context chain tracks system state")
        
        # Launch the UI
        ui_main()
        
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
        return 0
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        print("\nStack trace:")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main()) 