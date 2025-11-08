#!/usr/bin/env python3
"""
Integration test for companion app
Tests the full flow: Kindle module → Flask server → Browser
"""

import sys
import time
import json
import requests
import subprocess
import signal
from pathlib import Path

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

class TestRunner:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.server_process = None
        self.base_url = "http://localhost:8080"
        
    def start_server(self):
        """Start the Flask companion server"""
        print(f"{BLUE}Starting companion server...{RESET}")
        
        companion_dir = Path(__file__).parent / "assistant-companion"
        app_path = companion_dir / "companion" / "app.py"
        
        if not app_path.exists():
            print(f"{RED}Error: Companion app not found at {app_path}{RESET}")
            return False
        
        try:
            self.server_process = subprocess.Popen(
                [sys.executable, str(app_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(companion_dir)
            )
            
            # Wait for server to start
            for i in range(10):
                try:
                    response = requests.get(f"{self.base_url}/health", timeout=1)
                    if response.status_code == 200:
                        print(f"{GREEN}✓ Server started successfully{RESET}")
                        return True
                except requests.exceptions.RequestException:
                    time.sleep(0.5)
            
            print(f"{RED}✗ Server failed to start{RESET}")
            return False
            
        except Exception as e:
            print(f"{RED}Error starting server: {e}{RESET}")
            return False
    
    def stop_server(self):
        """Stop the Flask server"""
        if self.server_process:
            print(f"{BLUE}Stopping companion server...{RESET}")
            self.server_process.send_signal(signal.SIGTERM)
            self.server_process.wait(timeout=5)
            print(f"{GREEN}✓ Server stopped{RESET}")
    
    def test(self, name, func):
        """Run a single test"""
        print(f"{name:.<50} ", end='', flush=True)
        try:
            func()
            print(f"{GREEN}✓ PASS{RESET}")
            self.passed += 1
            return True
        except AssertionError as e:
            print(f"{RED}✗ FAIL{RESET}")
            print(f"  {RED}Error: {e}{RESET}")
            self.failed += 1
            return False
        except Exception as e:
            print(f"{RED}✗ ERROR{RESET}")
            print(f"  {RED}Exception: {e}{RESET}")
            self.failed += 1
            return False
    
    def assert_eq(self, actual, expected, msg=""):
        """Assert equality"""
        if actual != expected:
            raise AssertionError(f"{msg}: expected {expected}, got {actual}")
    
    def assert_true(self, value, msg=""):
        """Assert true"""
        if not value:
            raise AssertionError(f"{msg}: expected True, got {value}")
    
    def assert_in(self, needle, haystack, msg=""):
        """Assert item in collection"""
        if needle not in haystack:
            raise AssertionError(f"{msg}: {needle} not in {haystack}")
    
    # Test cases
    
    def test_health_endpoint(self):
        """Test /health endpoint"""
        response = requests.get(f"{self.base_url}/health", timeout=2)
        self.assert_eq(response.status_code, 200, "Health check should return 200")
        data = response.json()
        self.assert_in('status', data, "Health response should have status")
        self.assert_eq(data['status'], 'ok', "Status should be ok")
    
    def test_send_event(self):
        """Test sending an event"""
        event = {
            "event": "test_event",
            "timestamp": int(time.time()),
            "data": {"message": "test"}
        }
        response = requests.post(
            f"{self.base_url}/events",
            json=event,
            timeout=2
        )
        self.assert_eq(response.status_code, 200, "Event post should return 200")
        data = response.json()
        self.assert_eq(data['status'], 'ok', "Response should have ok status")
    
    def test_send_query_start(self):
        """Test sending query_start event"""
        event = {
            "event": "query_start",
            "timestamp": int(time.time()),
            "data": {
                "provider": "openai",
                "model": "gpt-4",
                "title": "Test Query",
                "history": [
                    {"role": "user", "content": "Hello"}
                ]
            }
        }
        response = requests.post(
            f"{self.base_url}/events",
            json=event,
            timeout=2
        )
        self.assert_eq(response.status_code, 200, "Query start should be accepted")
    
    def test_send_stream_chunk(self):
        """Test sending stream_chunk event"""
        event = {
            "event": "stream_chunk",
            "timestamp": int(time.time()),
            "data": {
                "content": "This is a streaming response..."
            }
        }
        response = requests.post(
            f"{self.base_url}/events",
            json=event,
            timeout=2
        )
        self.assert_eq(response.status_code, 200, "Stream chunk should be accepted")
    
    def test_send_error(self):
        """Test sending error event"""
        event = {
            "event": "error",
            "timestamp": int(time.time()),
            "data": {
                "message": "Test error message",
                "provider": "openai"
            }
        }
        response = requests.post(
            f"{self.base_url}/events",
            json=event,
            timeout=2
        )
        self.assert_eq(response.status_code, 200, "Error event should be accepted")
    
    def test_send_query_complete(self):
        """Test sending query_complete event"""
        event = {
            "event": "query_complete",
            "timestamp": int(time.time()),
            "data": {
                "response_length": 1234
            }
        }
        response = requests.post(
            f"{self.base_url}/events",
            json=event,
            timeout=2
        )
        self.assert_eq(response.status_code, 200, "Query complete should be accepted")
    
    def test_get_events(self):
        """Test retrieving events"""
        response = requests.get(f"{self.base_url}/api/events", timeout=2)
        self.assert_eq(response.status_code, 200, "Get events should return 200")
        data = response.json()
        self.assert_in('events', data, "Response should have events array")
        self.assert_true(len(data['events']) > 0, "Should have some events")
    
    def test_get_stats(self):
        """Test statistics endpoint"""
        response = requests.get(f"{self.base_url}/api/stats", timeout=2)
        self.assert_eq(response.status_code, 200, "Stats should return 200")
        data = response.json()
        self.assert_in('total_events', data, "Stats should have total_events")
        self.assert_in('event_types', data, "Stats should have event_types")
    
    def test_clear_events(self):
        """Test clearing events"""
        response = requests.post(f"{self.base_url}/api/clear", timeout=2)
        self.assert_eq(response.status_code, 200, "Clear should return 200")
        
        # Verify events were cleared
        response = requests.get(f"{self.base_url}/api/events", timeout=2)
        data = response.json()
        self.assert_eq(len(data['events']), 0, "Events should be empty after clear")
    
    def test_full_query_flow(self):
        """Test a complete query flow"""
        # Clear first
        requests.post(f"{self.base_url}/api/clear", timeout=2)
        
        # Send query_start
        requests.post(f"{self.base_url}/events", json={
            "event": "query_start",
            "timestamp": int(time.time()),
            "data": {"provider": "test", "model": "test-model"}
        }, timeout=2)
        
        # Send multiple chunks
        for i in range(5):
            requests.post(f"{self.base_url}/events", json={
                "event": "stream_chunk",
                "timestamp": int(time.time()),
                "data": {"content": f"Chunk {i}..."}
            }, timeout=2)
            time.sleep(0.1)
        
        # Send completion
        requests.post(f"{self.base_url}/events", json={
            "event": "query_complete",
            "timestamp": int(time.time()),
            "data": {"response_length": 50}
        }, timeout=2)
        
        # Verify events
        response = requests.get(f"{self.base_url}/api/events", timeout=2)
        data = response.json()
        self.assert_eq(data['total'], 7, "Should have 7 events (1 start + 5 chunks + 1 complete)")
    
    def run_all(self):
        """Run all tests"""
        print("\n" + "=" * 60)
        print("Running Companion Integration Tests")
        print("=" * 60 + "\n")
        
        # Start server
        if not self.start_server():
            print(f"\n{RED}Failed to start server, aborting tests{RESET}\n")
            return False
        
        time.sleep(1)  # Give server time to fully initialize
        
        # Run tests
        tests = [
            ("Health endpoint works", self.test_health_endpoint),
            ("Can send basic event", self.test_send_event),
            ("Can send query_start event", self.test_send_query_start),
            ("Can send stream_chunk event", self.test_send_stream_chunk),
            ("Can send error event", self.test_send_error),
            ("Can send query_complete event", self.test_send_query_complete),
            ("Can retrieve events", self.test_get_events),
            ("Can get statistics", self.test_get_stats),
            ("Can clear events", self.test_clear_events),
            ("Full query flow works", self.test_full_query_flow),
        ]
        
        for name, func in tests:
            self.test(name, func)
        
        # Stop server
        self.stop_server()
        
        # Print summary
        print("\n" + "=" * 60)
        total = self.passed + self.failed
        percentage = (self.passed / total * 100) if total > 0 else 0
        print(f"Results: {GREEN}{self.passed} passed{RESET}, {RED}{self.failed} failed{RESET} ({percentage:.1f}%)")
        print("=" * 60 + "\n")
        
        return self.failed == 0

if __name__ == "__main__":
    runner = TestRunner()
    success = runner.run_all()
    sys.exit(0 if success else 1)
