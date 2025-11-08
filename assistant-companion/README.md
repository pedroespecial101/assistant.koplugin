# KOReader AI Assistant Companion App

A development/debugging companion application that runs on your Mac and displays real-time AI Assistant activity from your Kindle.

## Features

- 📊 **Live Output Stream**: Watch LLM responses as they're generated
- 🔍 **Prompt Inspector**: See all prompts and message histories sent to AI providers
- 📝 **Event Logger**: Raw event stream with timestamps
- 🎨 **Color-coded Events**: Visual differentiation for queries, chunks, errors
- 🔌 **Non-intrusive**: Completely optional, disable anytime without affecting the plugin

## Quick Start

### 1. Install Dependencies

```bash
cd assistant-companion
pip3 install -r requirements.txt
```

### 2. Start the Companion Server

```bash
python3 companion/app.py
```

The server will start on `http://192.168.1.102:8080`

### 3. Install Kindle Module

Copy the companion module to your plugin:

```bash
# Option A: Copy to your development directory
cp kindle-module/assistant_companion.lua ../

# Option B: SFTP directly to Kindle
# (adjust path to match your Kindle setup)
```

### 4. Enable in KOReader

1. Open a book in KOReader
2. Menu → Settings → AI Assistant Settings
3. Scroll to "Companion App (Dev Mode)"
4. Toggle it ON
5. Verify endpoint shows: `http://192.168.1.102:8080`

### 5. Test It!

1. Highlight some text
2. Use any AI Assistant feature
3. Watch your Mac browser at `http://192.168.1.102:8080`

## Architecture

```
┌─────────────┐                    ┌──────────────┐
│   Kindle    │  HTTP POST events  │   Mac/Flask  │
│  (Plugin)   │ ──────────────────>│   (Companion)│
│             │                    │              │
│ assistant_  │                    │  Server-Sent │
│ companion.  │                    │  Events      │
│ lua         │                    │      ↓       │
└─────────────┘                    │  [Browser]   │
                                   └──────────────┘
```

## Event Types

| Event | Description | Data |
|-------|-------------|------|
| `query_start` | New AI query initiated | Provider, model, history |
| `stream_chunk` | LLM response chunk | Content, reasoning |
| `query_complete` | Query finished | Full response, tokens |
| `error` | Error occurred | Error message, stack |
| `heartbeat` | Connection check | Timestamp |

## Configuration

### Companion App Settings

Edit `companion/app.py`:

```python
# Change port
app.run(host='0.0.0.0', port=9090)

# Enable debug mode
app.run(debug=True)

# Change log level
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Kindle Plugin Settings

Edit in KOReader UI or modify settings directly:

```lua
-- In your plugin's settings
companion_enabled = true
companion_url = "http://192.168.1.102:8080"
companion_buffer_size = 100  -- Max buffered events
```

## Troubleshooting

### Companion app shows "No events yet"

1. Verify Kindle and Mac are on same network
2. Check Mac IP hasn't changed: `ifconfig | grep "inet "`
3. Test connectivity from Kindle: `ping 192.168.1.102`
4. Check KOReader logs: `/mnt/us/koreader/crash.log`

### Events not appearing

1. Confirm companion is enabled in KOReader settings
2. Check Flask console for incoming requests
3. Try the test client: `python3 examples/test_client.py`

### Plugin crashes or freezes

1. Disable companion mode immediately
2. Check if companion URL is reachable
3. Review `/mnt/us/koreader/crash.log` for Lua errors
4. Report issue with logs

## Development

### Adding New Event Types

1. In `assistant_companion.lua`, add event emission:
   ```lua
   companion:send("my_event", { custom = "data" })
   ```

2. In `companion/static/app.js`, handle it:
   ```javascript
   if (event.event === 'my_event') {
       // Display logic
   }
   ```

### Testing Without Kindle

Use the test client:

```bash
python3 examples/test_client.py
```

This simulates Kindle events for UI development.

## Security Notes

⚠️ **This is a development tool only!**

- No authentication or encryption
- Logs may contain sensitive text from your books
- Only use on trusted local networks
- **DO NOT expose to the internet**

## Performance Impact

- Minimal: HTTP calls are fire-and-forget
- No blocking operations in plugin
- Automatically disables if companion unreachable
- ~1-2ms overhead per chunk when enabled

## Roadmap

- [ ] Event persistence to SQLite
- [ ] Token usage tracking and costs
- [ ] Export conversation logs
- [ ] WebSocket support for bidirectional communication
- [ ] Multiple Kindle support
- [ ] Dark/light theme toggle

## License

Same as parent plugin (check main LICENSE file)

## Support

This is an experimental dev tool. For issues:
1. Check KOReader logs first
2. Try disabling and re-enabling
3. Test with `examples/test_client.py`
4. Open an issue with full logs
