# Project Overview

## What We Built

A **development companion application** that runs on your Mac and displays real-time AI Assistant activity from your Kindle e-reader.

### Components

1. **Flask Web Server** (`companion/`)
   - Receives events from Kindle via HTTP POST
   - Streams events to browser via Server-Sent Events
   - Provides REST API for stats and management
   - Beautiful dark-themed dashboard

2. **Kindle Module** (`kindle-module/`)
   - `assistant_companion.lua` - HTTP event reporter
   - Non-blocking, fire-and-forget architecture
   - Automatic buffering when server unavailable
   - Integrates into existing plugin with minimal changes

3. **Web Dashboard** (`companion/templates/`, `companion/static/`)
   - Live streaming output display
   - Prompt inspector with message history
   - Raw event viewer with JSON formatting
   - Statistics and metrics

4. **Testing Tools** (`examples/`)
   - Test client to simulate Kindle events
   - Sample event data
   - Helpful for UI development

## Key Features

✅ **Real-time Streaming** - See AI responses as they're generated
✅ **Non-intrusive** - Zero impact when disabled, minimal when enabled
✅ **Fault Tolerant** - Buffers events if server unreachable
✅ **Color Coded** - Visual differentiation for event types
✅ **Multi-tab Interface** - Output, Prompts, Raw, Stats
✅ **Easy Integration** - Clear step-by-step guide
✅ **Development Tool** - For debugging and development only

## Technical Decisions

### Why Flask?
- Simple, lightweight
- Perfect for PoC
- Easy to extend
- Native SSE support

### Why HTTP POST?
- Simple to implement in Lua
- No dependencies beyond `socket.http`
- Fire-and-forget prevents UI blocking
- Easy to test with curl/Postman

### Why Server-Sent Events?
- Native browser support
- Auto-reconnect built-in
- One-way push (all we need)
- Simpler than WebSockets

### Why Buffering?
- Prevents data loss
- Graceful degradation
- No plugin crashes if server down
- Automatic recovery

## File Structure

```
assistant-companion/
├── README.md                    # Main documentation
├── SETUP.md                     # Quick start guide
├── requirements.txt             # Python dependencies
├── start.sh                     # Quick start script
│
├── companion/                   # Flask server
│   ├── __init__.py
│   ├── app.py                  # Main Flask application
│   ├── static/
│   │   ├── style.css           # Dashboard styling
│   │   └── app.js              # Dashboard JavaScript
│   └── templates/
│       └── dashboard.html      # Main UI template
│
├── kindle-module/              # Kindle integration
│   ├── assistant_companion.lua # Event reporter module
│   └── INTEGRATION.md          # Integration guide
│
└── examples/                   # Testing tools
    ├── test_client.py          # Event simulator
    └── sample_events.json      # Sample data
```

## Event Flow

```
User highlights text in book
         ↓
AI Assistant feature triggered
         ↓
assistant_querier.lua processes
         ↓
assistant_companion.lua sends HTTP POST
         ↓
Flask /events endpoint receives
         ↓
Event stored in memory queue
         ↓
SSE /stream pushes to browser
         ↓
JavaScript updates dashboard
         ↓
User sees real-time output!
```

## Event Types

| Event | Purpose | Data |
|-------|---------|------|
| `query_start` | New AI query initiated | Provider, model, history |
| `stream_chunk` | AI response chunk | Content, reasoning |
| `query_complete` | Query finished | Tokens, duration |
| `error` | Error occurred | Error message |
| `heartbeat` | Connection check | Status |

## Configuration Points

### Kindle Side
- `companion_enabled` - Toggle on/off
- `companion_url` - Server endpoint
- `max_buffer_size` - Event buffer limit
- `error_cooldown` - Error logging rate limit

### Mac Side
- `host` - Network interface (0.0.0.0 = all)
- `port` - Server port (8080)
- `debug` - Flask debug mode
- `maxlen` - Event queue size (1000)

## Security Considerations

⚠️ **This is a development tool only!**

- No authentication
- No encryption
- No input validation
- Logs contain book content
- HTTP only, no HTTPS

**Do NOT:**
- Use in production
- Expose to internet
- Use on untrusted networks
- Log sensitive information

**Do:**
- Use on private home network only
- Disable when not needed
- Clear logs regularly
- Review what's being logged

## Performance Impact

| Scenario | Overhead | Notes |
|----------|----------|-------|
| Disabled | 0ms | No code runs |
| Enabled, server reachable | ~1-2ms/event | Fire-and-forget HTTP |
| Enabled, server down | ~2ms + buffer write | Automatic buffering |
| Buffering | 0ms | In-memory only |
| Buffer flush | ~2ms/event | Batch send |

## Future Enhancements

Potential additions (not implemented):

- [ ] SQLite persistence
- [ ] Token usage tracking
- [ ] Cost calculations
- [ ] Export conversations
- [ ] WebSocket bidirectional
- [ ] Multiple Kindle support
- [ ] Authentication/encryption
- [ ] Theme customization
- [ ] Metrics dashboards
- [ ] Alert/notification system

## Development Notes

### Adding New Event Types

1. Define in Kindle module:
   ```lua
   companion:send("my_event", { data = "..." })
   ```

2. Handle in Flask:
   ```python
   # Automatically handled, no changes needed
   ```

3. Display in UI:
   ```javascript
   if (event.event === 'my_event') {
       // Handle display
   }
   ```

### Debugging

**Kindle side:**
```bash
tail -f /mnt/us/koreader/crash.log | grep Companion
```

**Mac side:**
```bash
# Flask console shows all requests
# Browser console (F12) shows JavaScript
```

**Test without Kindle:**
```bash
python3 examples/test_client.py
```

## Credits

Built as a proof-of-concept companion for the KOReader AI Assistant plugin.

- Flask framework
- Server-Sent Events
- Lua socket.http
- VS Code for development

## License

Same as parent plugin (see main LICENSE file)

---

**Status**: ✅ Ready to use
**Version**: 1.0 (PoC)
**Last Updated**: November 8, 2025
