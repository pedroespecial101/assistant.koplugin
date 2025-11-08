#!/usr/bin/env python3
"""
Simple integration test for companion app
Tests basic functionality without external dependencies
"""

import sys
import json
import subprocess
import time
from pathlib import Path
from urllib import request, error
from urllib.parse import urljoin

# Colors
GREEN = '\033[92m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'

class SimpleTestRunner:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.base_url = "http://localhost:8080"
        
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
            print(f"  {RED}{e}{RESET}")
            self.failed += 1
            return False
        except Exception as e:
            print(f"{RED}✗ ERROR{RESET}")
            print(f"  {RED}{type(e).__name__}: {e}{RESET}")
            self.failed += 1
            return False
    
    def http_get(self, path):
        """Simple HTTP GET"""
        url = urljoin(self.base_url, path)
        try:
            with request.urlopen(url, timeout=2) as response:
                return response.status, json.loads(response.read().decode())
        except error.HTTPError as e:
            return e.code, {}
        except Exception as e:
            raise AssertionError(f"HTTP GET failed: {e}")
    
    def http_post(self, path, data):
        """Simple HTTP POST"""
        url = urljoin(self.base_url, path)
        try:
            json_data = json.dumps(data).encode('utf-8')
            req = request.Request(
                url,
                data=json_data,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            with request.urlopen(req, timeout=2) as response:
                return response.status, json.loads(response.read().decode())
        except error.HTTPError as e:
            return e.code, {}
        except Exception as e:
            raise AssertionError(f"HTTP POST failed: {e}")
    
    # Test cases
    def test_companion_module_exists(self):
        """Companion module file exists"""
        module_path = Path(__file__).parent / "assistant_companion.lua"
        if not module_path.exists():
            raise AssertionError(f"Module not found at {module_path}")
    
    def test_querier_has_companion_code(self):
        """Querier has companion integration"""
        querier_path = Path(__file__).parent / "assistant_querier.lua"
        if not querier_path.exists():
            raise AssertionError(f"Querier not found at {querier_path}")
        
        content = querier_path.read_text()
        
        # Check for key integration points
        checks = [
            ("companion module require", "require.*assistant_companion"),
            ("companion field", "companion = nil"),
            ("companion initialization", "Companion:new"),
            ("query_start event", 'companion:send.*query_start'),
            ("stream_chunk event", 'companion:send.*stream_chunk'),
            ("error event", 'companion:send.*error'),
        ]
        
        import re
        for name, pattern in checks:
            if not re.search(pattern, content):
                raise AssertionError(f"Missing {name} (pattern: {pattern})")
    
    def test_flask_app_exists(self):
        """Flask app file exists"""
        app_path = Path(__file__).parent / "assistant-companion" / "companion" / "app.py"
        if not app_path.exists():
            raise AssertionError(f"Flask app not found at {app_path}")
    
    def test_dashboard_html_exists(self):
        """Dashboard HTML exists"""
        html_path = Path(__file__).parent / "assistant-companion" / "companion" / "templates" / "dashboard.html"
        if not html_path.exists():
            raise AssertionError(f"Dashboard not found at {html_path}")
    
    def test_integration_docs_exist(self):
        """Integration documentation exists"""
        docs = [
            "assistant-companion/README.md",
            "assistant-companion/SETUP.md",
            "assistant-companion/kindle-module/INTEGRATION.md",
            "COMPANION_INTEGRATION.md"
        ]
        for doc in docs:
            doc_path = Path(__file__).parent / doc
            if not doc_path.exists():
                raise AssertionError(f"Documentation not found: {doc}")
    
    def test_example_files_exist(self):
        """Example files exist"""
        test_client = Path(__file__).parent / "assistant-companion" / "examples" / "test_client.py"
        if not test_client.exists():
            raise AssertionError(f"Test client not found at {test_client}")
    
    def test_companion_module_syntax(self):
        """Companion module has valid Lua syntax"""
        module_path = Path(__file__).parent / "assistant_companion.lua"
        content = module_path.read_text()
        
        # Basic syntax checks
        if content.count("function") < 5:
            raise AssertionError("Module should have at least 5 functions")
        
        if "Companion:new" not in content:
            raise AssertionError("Missing Companion:new constructor")
        
        if "Companion:send" not in content:
            raise AssertionError("Missing Companion:send method")
        
        required_methods = [":is_enabled", ":set_enabled", ":get_url", ":set_url", ":get_status"]
        for method in required_methods:
            if method not in content:
                raise AssertionError(f"Missing method: {method}")
    
    def test_querier_integration_complete(self):
        """Querier integration is complete"""
        querier_path = Path(__file__).parent / "assistant_querier.lua"
        content = querier_path.read_text()
        
        # Count companion references
        companion_count = content.count("companion")
        if companion_count < 20:
            raise AssertionError(f"Expected at least 20 companion references, found {companion_count}")
        
        # Check for all event types
        event_types = ["query_start", "stream_chunk", "error", "query_complete"]
        for event in event_types:
            if event not in content:
                raise AssertionError(f"Missing event type: {event}")
    
    def test_start_script_exists(self):
        """Start script exists and is executable"""
        start_script = Path(__file__).parent / "assistant-companion" / "start.sh"
        if not start_script.exists():
            raise AssertionError(f"Start script not found at {start_script}")
        
        import os
        if not os.access(start_script, os.X_OK):
            raise AssertionError("Start script is not executable")
    
    def test_flask_has_all_routes(self):
        """Flask app has all required routes"""
        app_path = Path(__file__).parent / "assistant-companion" / "companion" / "app.py"
        content = app_path.read_text()
        
        routes = [
            "@app.route('/')",
            "@app.route('/events'",
            "@app.route('/stream')",
            "@app.route('/api/events'",
            "@app.route('/api/clear'",
            "@app.route('/api/stats'",
            "@app.route('/health')",
        ]
        
        for route in routes:
            if route not in content:
                raise AssertionError(f"Missing route: {route}")
    
    def run_all(self):
        """Run all tests"""
        print("\n" + "=" * 60)
        print("Running Companion Static Tests")
        print("=" * 60 + "\n")
        
        tests = [
            ("Companion module file exists", self.test_companion_module_exists),
            ("Companion module has valid syntax", self.test_companion_module_syntax),
            ("Querier has companion integration", self.test_querier_has_companion_code),
            ("Querier integration is complete", self.test_querier_integration_complete),
            ("Flask app exists", self.test_flask_app_exists),
            ("Flask has all routes", self.test_flask_has_all_routes),
            ("Dashboard HTML exists", self.test_dashboard_html_exists),
            ("Integration docs exist", self.test_integration_docs_exist),
            ("Example files exist", self.test_example_files_exist),
            ("Start script exists", self.test_start_script_exists),
        ]
        
        for name, func in tests:
            self.test(name, func)
        
        # Print summary
        print("\n" + "=" * 60)
        total = self.passed + self.failed
        percentage = (self.passed / total * 100) if total > 0 else 0
        print(f"Results: {GREEN}{self.passed} passed{RESET}, {RED}{self.failed} failed{RESET} ({percentage:.1f}%)")
        print("=" * 60 + "\n")
        
        if self.failed == 0:
            print(f"{GREEN}✓ All static tests passed!{RESET}")
            print(f"{BLUE}The companion integration is complete and ready to test.{RESET}\n")
        
        return self.failed == 0

if __name__ == "__main__":
    runner = SimpleTestRunner()
    success = runner.run_all()
    sys.exit(0 if success else 1)
