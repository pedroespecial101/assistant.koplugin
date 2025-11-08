# Quick Reference Card

## Starting the Companion App

```bash
cd assistant-companion
./start.sh
```

Open browser: http://localhost:8080

## Testing Without Kindle

```bash
python3 examples/test_client.py
```

## Kindle Setup

1. Menu → Settings → AI Assistant Settings
2. Scroll to "Companion App (Dev Mode)"
3. Toggle ON
4. Test Connection

## Common Commands

### Check Mac IP
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

### Stop Server
```bash
# Press Ctrl+C in terminal
# Or:
lsof -ti:8080 | xargs kill -9
```

### View Logs
```bash
# Kindle (via SSH):
tail -f /mnt/us/koreader/crash.log | grep Companion

# Mac: Check Flask console
```

### Clear Events
- Click 🗑️ Clear button in dashboard
- Or: `curl -X POST http://localhost:8080/api/clear`

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Dashboard UI |
| `/events` | POST | Receive Kindle events |
| `/stream` | GET | SSE stream for browser |
| `/api/events` | GET | Get all events as JSON |
| `/api/clear` | POST | Clear all events |
| `/api/stats` | GET | Get statistics |
| `/health` | GET | Health check |

## Event Types

| Event | When | Data |
|-------|------|------|
| `query_start` | AI query begins | provider, model, history |
| `stream_chunk` | Response streaming | content, reasoning |
| `query_complete` | Query done | tokens, duration |
| `error` | Error occurs | message |
| `heartbeat` | Connection test | status |

## Dashboard Tabs

- **📊 Live Output** - See AI responses in real-time
- **🔍 Prompts** - View full message histories
- **📝 Raw Events** - JSON dump of all events
- **📈 Stats** - Metrics and breakdowns

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Can't connect | Check IP with `ifconfig`, update endpoint |
| Port in use | Change port in `app.py` or kill process |
| No events | Verify companion enabled on Kindle |
| Server crash | Check Python/Flask errors in terminal |
| Kindle freeze | Disable companion mode immediately |

## Keyboard Shortcuts

In dashboard:
- **Tab** - Switch between tabs
- **Ctrl+R** - Refresh page (keeps connection)
- **F12** - Open browser console for debugging

## File Locations

```
Kindle:
  /mnt/us/koreader/plugins/assistant.koplugin/assistant_companion.lua
  /mnt/us/koreader/crash.log

Mac:
  ~/Projects/assistant.koplugin/assistant-companion/
```

## Quick Integration

```bash
# 1. Copy module to plugin
cp kindle-module/assistant_companion.lua ../

# 2. Follow INTEGRATION.md
# 3. Restart KOReader
# 4. Enable in settings
```

## Default Configuration

```
Kindle → Mac: http://192.168.1.102:8080
Mac Listen: 0.0.0.0:8080
Buffer Size: 100 events
Timeout: 2 seconds
Error Cooldown: 30 seconds
```

## Safety

✅ **Safe:**
- Use on home WiFi
- Development/testing only
- Disable when not debugging

❌ **NOT Safe:**
- Production use
- Public networks
- Contains book text

## Performance

- Disabled: 0ms overhead
- Enabled: ~1-2ms per event
- Non-blocking HTTP calls
- Auto-buffering if unreachable

## Quick Commands Cheat Sheet

```bash
# Start companion
./start.sh

# Test it
python3 examples/test_client.py

# Check health
curl http://localhost:8080/health

# Get stats
curl http://localhost:8080/api/stats

# Clear events
curl -X POST http://localhost:8080/api/clear

# Send test event
curl -X POST http://localhost:8080/events \
  -H "Content-Type: application/json" \
  -d '{"event":"test","timestamp":1234567890,"data":{}}'
```

## Need Help?

1. Check SETUP.md for detailed guide
2. Check INTEGRATION.md for Kindle integration
3. Check PROJECT.md for architecture
4. Review Flask console for errors
5. Review KOReader crash.log

---

**Pro Tips:**

- Keep dashboard open while testing
- Use test_client.py for UI development
- Check "Raw Events" tab for debugging
- Monitor "Stats" for usage patterns
- Use heartbeat to verify connectivity
