#!/usr/bin/env python3
"""
Test client that simulates Kindle events
Use this to test the companion app UI without needing a Kindle
"""

import requests
import time
import json
import random

BASE_URL = "http://localhost:8080"

def send_event(event_type, data):
    """Send an event to the companion app"""
    event = {
        "event": event_type,
        "timestamp": int(time.time()),
        "data": data
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/events",
            json=event,
            timeout=2
        )
        if response.status_code == 200:
            print(f"✓ Sent {event_type}")
            return True
        else:
            print(f"✗ Failed to send {event_type}: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error sending {event_type}: {e}")
        return False


def simulate_query():
    """Simulate a complete query with streaming"""
    
    providers = ["openai", "anthropic", "ollama"]
    models = ["gpt-4", "claude-3-opus", "llama2"]
    
    provider = random.choice(providers)
    model = random.choice(models)
    
    # Send query start
    print("\n--- Starting new query ---")
    send_event("query_start", {
        "provider": provider,
        "model": model,
        "title": "AI Assistant Query",
        "history": [
            {
                "role": "system",
                "content": "You are a helpful AI assistant integrated into an e-reader."
            },
            {
                "role": "user",
                "content": "Explain the concept of quantum entanglement in simple terms."
            }
        ]
    })
    
    time.sleep(0.5)
    
    # Simulate streaming response
    response_parts = [
        "Quantum entanglement is ",
        "a fascinating phenomenon ",
        "where two particles become ",
        "connected in such a way ",
        "that the state of one ",
        "instantly affects the state ",
        "of the other, ",
        "no matter how far apart they are.\n\n",
        "Think of it like ",
        "a pair of magic dice: ",
        "when you roll one, ",
        "the other automatically shows ",
        "a related number, ",
        "even if it's on the other side ",
        "of the universe!"
    ]
    
    for part in response_parts:
        send_event("stream_chunk", {
            "content": part
        })
        time.sleep(random.uniform(0.1, 0.3))
    
    # Send completion
    send_event("query_complete", {
        "response_length": sum(len(p) for p in response_parts),
        "duration": random.randint(2000, 5000),
        "tokens": {
            "prompt": random.randint(50, 150),
            "completion": random.randint(100, 300)
        }
    })
    
    print("--- Query complete ---\n")


def simulate_error():
    """Simulate an error"""
    print("\n--- Simulating error ---")
    send_event("error", {
        "message": "API rate limit exceeded. Please try again in 30 seconds.",
        "provider": "openai"
    })
    print("--- Error sent ---\n")


def send_heartbeat():
    """Send a heartbeat"""
    send_event("heartbeat", {
        "status": "alive"
    })


def main():
    """Main test loop"""
    print("=" * 60)
    print("KOReader AI Companion - Test Client")
    print("=" * 60)
    print(f"\nTarget: {BASE_URL}")
    print("\nThis will simulate Kindle events for testing the UI")
    print("Press Ctrl+C to stop\n")
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        if response.status_code == 200:
            print("✓ Companion server is running\n")
        else:
            print("✗ Companion server returned error\n")
            return
    except Exception as e:
        print(f"✗ Cannot connect to companion server: {e}")
        print(f"  Make sure it's running: python3 companion/app.py\n")
        return
    
    print("Starting simulation...\n")
    
    try:
        iteration = 1
        while True:
            print(f"=== Iteration {iteration} ===")
            
            # Send a query
            simulate_query()
            time.sleep(2)
            
            # Occasionally simulate an error
            if random.random() < 0.2:
                simulate_error()
                time.sleep(2)
            
            # Send heartbeat
            send_heartbeat()
            
            iteration += 1
            time.sleep(3)
            
    except KeyboardInterrupt:
        print("\n\nStopping simulation...")
        print("Events remain in companion app until cleared")


if __name__ == "__main__":
    main()
