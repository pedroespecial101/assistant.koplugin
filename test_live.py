#!/usr/bin/env python3
"""
Live test of the companion server
Starts the server and runs real HTTP requests against it
"""

import sys
import time
import json
import subprocess
import signal
from pathlib import Path
from urllib import request, error

GREEN = '\033[92m'
RED = '\033[91m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def start_server():
    """Start the companion server"""
    print(f"{BLUE}Starting companion server...{RESET}")
    
    companion_dir = Path(__file__).parent / "assistant-companion"
    app_path = companion_dir / "companion" / "app.py"
    
    proc = subprocess.Popen(
        [sys.executable, str(app_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(companion_dir),
        text=True
    )
    
    # Wait for server to start
    for i in range(20):
        try:
            req = request.Request("http://localhost:8080/health")
            with request.urlopen(req, timeout=1) as response:
                if response.status == 200:
                    print(f"{GREEN}✓ Server started (took {i * 0.5:.1f}s){RESET}")
                    return proc
        except:
            time.sleep(0.5)
    
    print(f"{RED}✗ Server failed to start{RESET}")
    proc.kill()
    return None

def test_endpoint(name, method, path, data=None):
    """Test a single endpoint"""
    print(f"  {name:.<45} ", end='', flush=True)
    try:
        url = f"http://localhost:8080{path}"
        
        if method == "GET":
            req = request.Request(url)
        else:  # POST
            json_data = json.dumps(data).encode('utf-8') if data else b'{}'
            req = request.Request(
                url,
                data=json_data,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
        
        with request.urlopen(req, timeout=2) as response:
            status = response.status
            body = json.loads(response.read().decode())
            
            if status == 200:
                print(f"{GREEN}✓{RESET}")
                return True
            else:
                print(f"{RED}✗ ({status}){RESET}")
                return False
                
    except Exception as e:
        print(f"{RED}✗ {type(e).__name__}{RESET}")
        return False

def run_tests(proc):
    """Run all live tests"""
    print(f"\n{BLUE}Running live HTTP tests...{RESET}\n")
    
    passed = 0
    total = 0
    
    # Test health endpoint
    if test_endpoint("GET /health", "GET", "/health"):
        passed += 1
    total += 1
    
    # Test sending query_start
    if test_endpoint("POST query_start event", "POST", "/events", {
        "event": "query_start",
        "timestamp": int(time.time()),
        "data": {
            "provider": "openai",
            "model": "gpt-4",
            "title": "Test Query"
        }
    }):
        passed += 1
    total += 1
    
    # Test sending stream_chunk
    if test_endpoint("POST stream_chunk event", "POST", "/events", {
        "event": "stream_chunk",
        "timestamp": int(time.time()),
        "data": {"content": "Test chunk"}
    }):
        passed += 1
    total += 1
    
    # Test sending error
    if test_endpoint("POST error event", "POST", "/events", {
        "event": "error",
        "timestamp": int(time.time()),
        "data": {"message": "Test error"}
    }):
        passed += 1
    total += 1
    
    # Test sending query_complete
    if test_endpoint("POST query_complete event", "POST", "/events", {
        "event": "query_complete",
        "timestamp": int(time.time()),
        "data": {"response_length": 100}
    }):
        passed += 1
    total += 1
    
    # Test getting events
    if test_endpoint("GET /api/events", "GET", "/api/events"):
        passed += 1
    total += 1
    
    # Test getting stats
    if test_endpoint("GET /api/stats", "GET", "/api/stats"):
        passed += 1
    total += 1
    
    # Test clearing events
    if test_endpoint("POST /api/clear", "POST", "/api/clear"):
        passed += 1
    total += 1
    
    return passed, total

def main():
    print("\n" + "=" * 60)
    print("Live Companion Server Test")
    print("=" * 60 + "\n")
    
    # Start server
    proc = start_server()
    if not proc:
        print(f"\n{RED}Failed to start server{RESET}\n")
        return False
    
    try:
        time.sleep(0.5)  # Let server fully initialize
        
        # Run tests
        passed, total = run_tests(proc)
        
        # Summary
        print("\n" + "=" * 60)
        percentage = (passed / total * 100) if total > 0 else 0
        print(f"Results: {GREEN}{passed}/{total} passed{RESET} ({percentage:.1f}%)")
        print("=" * 60 + "\n")
        
        if passed == total:
            print(f"{GREEN}✓ All live tests passed!{RESET}")
            print(f"{BLUE}The companion server is working correctly.{RESET}")
            print(f"{BLUE}Open http://localhost:8080 in your browser to see the dashboard.{RESET}\n")
        else:
            print(f"{YELLOW}⚠ Some tests failed{RESET}\n")
        
        # Keep server running for manual inspection
        print(f"{BLUE}Server is still running...{RESET}")
        print(f"  Dashboard: {YELLOW}http://localhost:8080{RESET}")
        print(f"  Press Ctrl+C to stop\n")
        
        try:
            proc.wait()
        except KeyboardInterrupt:
            print(f"\n{BLUE}Stopping server...{RESET}")
        
        return passed == total
        
    finally:
        # Clean up
        proc.send_signal(signal.SIGTERM)
        try:
            proc.wait(timeout=5)
        except:
            proc.kill()
        print(f"{GREEN}✓ Server stopped{RESET}\n")

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Interrupted by user{RESET}\n")
        sys.exit(130)
