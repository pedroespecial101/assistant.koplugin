#!/usr/bin/env python3
"""
KOReader AI Assistant Companion App
Receives and displays real-time events from the Kindle plugin
"""

from flask import Flask, render_template, request, Response, jsonify
from datetime import datetime
import json
import logging
from collections import deque

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# In-memory event storage (max 1000 events)
events = deque(maxlen=1000)
connected_clients = 0


@app.route('/')
def index():
    """Serve the main dashboard"""
    return render_template('dashboard.html')


@app.route('/events', methods=['POST'])
def receive_event():
    """Receive events from Kindle plugin"""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Add server-side timestamp
        data['received_at'] = datetime.now().isoformat()
        
        # Store event
        events.append(data)
        
        # Log to console with color coding
        event_type = data.get('event', 'unknown')
        event_color = {
            'query_start': '\033[92m',      # Green
            'stream_chunk': '\033[94m',     # Blue
            'query_complete': '\033[93m',   # Yellow
            'error': '\033[91m',            # Red
            'heartbeat': '\033[90m',        # Gray
        }.get(event_type, '\033[0m')
        
        reset_color = '\033[0m'
        
        logger.info(f"{event_color}[{event_type}]{reset_color} Received from Kindle")
        
        # Log details based on event type
        if event_type == 'query_start':
            provider = data.get('data', {}).get('provider', 'unknown')
            model = data.get('data', {}).get('model', 'unknown')
            logger.info(f"  Provider: {provider}, Model: {model}")
        elif event_type == 'stream_chunk':
            content = data.get('data', {}).get('content', '')
            if content:
                preview = content[:50] + ('...' if len(content) > 50 else '')
                logger.info(f"  Content: {preview}")
        elif event_type == 'error':
            error_msg = data.get('data', {}).get('message', 'Unknown error')
            logger.error(f"  Error: {error_msg}")
        
        return jsonify({'status': 'ok', 'event_id': len(events)}), 200
        
    except Exception as e:
        logger.error(f"Error processing event: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/stream')
def stream():
    """Server-Sent Events stream for real-time updates"""
    def generate():
        global connected_clients
        connected_clients += 1
        logger.info(f"Client connected (total: {connected_clients})")
        
        # Send all existing events first
        for event in events:
            yield f"data: {json.dumps(event)}\n\n"
        
        # Keep connection alive and send new events
        last_id = len(events)
        try:
            while True:
                if len(events) > last_id:
                    for event in list(events)[last_id:]:
                        yield f"data: {json.dumps(event)}\n\n"
                    last_id = len(events)
                # Small delay to avoid busy-waiting
                import time
                time.sleep(0.1)
        except GeneratorExit:
            connected_clients -= 1
            logger.info(f"Client disconnected (remaining: {connected_clients})")
    
    return Response(generate(), mimetype='text/event-stream')


@app.route('/api/events', methods=['GET'])
def get_events():
    """Get all events as JSON (for debugging)"""
    return jsonify({
        'total': len(events),
        'events': list(events)
    })


@app.route('/api/clear', methods=['POST'])
def clear_events():
    """Clear all events"""
    events.clear()
    logger.info("Event history cleared")
    return jsonify({'status': 'cleared'})


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get statistics about events"""
    event_types = {}
    for event in events:
        event_type = event.get('event', 'unknown')
        event_types[event_type] = event_types.get(event_type, 0) + 1
    
    return jsonify({
        'total_events': len(events),
        'connected_clients': connected_clients,
        'event_types': event_types,
        'oldest_event': events[0].get('received_at') if events else None,
        'newest_event': events[-1].get('received_at') if events else None,
    })


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'events_count': len(events)
    })


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 KOReader AI Assistant Companion App")
    print("="*60)
    print(f"\n📱 Kindle should send events to: http://192.168.1.102:8080")
    print(f"🌐 Open dashboard at: http://localhost:8080")
    print(f"🌐 Or from other devices: http://192.168.1.102:8080")
    print("\nPress Ctrl+C to stop\n")
    print("="*60 + "\n")
    
    app.run(
        host='0.0.0.0',
        port=8080,
        debug=False,
        threaded=True
    )
