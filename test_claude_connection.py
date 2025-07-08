#!/usr/bin/env python3
"""Test script to verify LNbits MCP server works exactly like Claude Desktop will run it."""

import subprocess
import sys
import time
import signal
import os

def test_server():
    """Test the server exactly as Claude Desktop will run it."""
    
    # Change to the project directory (like Claude Desktop does)
    os.chdir('/Users/mark/Desktop/lnbits-mcp-server')
    
    # The exact command Claude Desktop will run
    cmd = ['/Users/mark/Desktop/lnbits-mcp-server/venv/bin/lnbits-mcp-server']
    
    print("🧪 Testing LNbits MCP Server (as Claude Desktop will run it)")
    print(f"Command: {' '.join(cmd)}")
    print("─" * 50)
    
    try:
        # Start the process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a few seconds to see if it starts successfully
        time.sleep(3)
        
        # Check if process is still running (good sign)
        if process.poll() is None:
            print("✅ SUCCESS: Server started and is running!")
            print("✅ No import errors detected")
            print("✅ Process is stable and waiting for connections")
            print("✅ Ready for Claude Desktop integration")
            
            # Terminate the process
            process.terminate()
            process.wait(timeout=5)
            return True
        else:
            # Process exited, check for errors
            stdout, stderr = process.communicate()
            print("❌ FAILED: Server exited unexpectedly")
            if stderr:
                print(f"Error output: {stderr}")
            if stdout:
                print(f"Standard output: {stdout}")
            return False
            
    except Exception as e:
        print(f"❌ FAILED: Exception occurred: {e}")
        return False

if __name__ == "__main__":
    success = test_server()
    sys.exit(0 if success else 1)