# SETUP GUIDE

## Quick Start (5 minutes)

### 1. Start the Companion App

```bash
cd assistant-companion
./start.sh
```

Or manually:

```bash
cd assistant-companion
pip3 install -r requirements.txt
python3 companion/app.py
```

You should see:
```
🚀 KOReader AI Assistant Companion App
📱 Kindle should send events to: http://192.168.1.102:8080
🌐 Open dashboard at: http://localhost:8080
```

### 2. Open the Dashboard

Open your browser to: **http://localhost:8080**

You should see the companion dashboard with 4 tabs:
- 📊 Live Output
- 🔍 Prompts  
- 📝 Raw Events
- 📈 Stats

### 3. Test Without Kindle

In a new terminal:

```bash
cd assistant-companion
python3 examples/test_client.py
```

This simulates Kindle events. Watch them appear in your browser!

### 4. Integrate with Kindle

Follow the instructions in `kindle-module/INTEGRATION.md` to:
1. Copy `assistant_companion.lua` to your plugin
2. Modify `assistant_querier.lua` 
3. Add settings to `assistant_settings.lua`

### 5. Enable on Kindle

1. Open KOReader on your Kindle
2. Open a book
3. Tap Menu → Settings → AI Assistant Settings
4. Scroll to "Companion App (Dev Mode)"
5. Toggle "Enable Companion App" ON
6. Tap "Test Connection"

You should see: "✓ Test event sent!"

### 6. Try It Out

1. Highlight text in your book
2. Use any AI Assistant feature
3. Watch the magic happen in your browser! 🎉

## Troubleshooting

### Can't connect to companion

**Check your Mac's IP:**
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

If it's not `192.168.1.102`, update:
- In Kindle settings: Configure Endpoint
- In `companion/app.py` startup message

**Check firewall:**
```bash
# macOS - allow port 8080
# System Settings → Network → Firewall → Options
# Or temporarily disable firewall for testing
```

**Test from Kindle:**
```bash
# SSH into Kindle, then:
ping 192.168.1.102
curl http://192.168.1.102:8080/health
```

### Server won't start

**Port already in use:**
```bash
lsof -ti:8080 | xargs kill -9
```

Or change the port in `companion/app.py`:
```python
app.run(host='0.0.0.0', port=9090)  # Use different port
```

### Events not showing up

1. **Check companion is enabled on Kindle**
   - Settings → AI Assistant → Companion App → Enabled?

2. **Check Flask console for requests**
   - Should see: `[INFO] [query_start] Received from Kindle`

3. **Check KOReader logs**
   ```bash
   # On Kindle via SSH:
   tail -f /mnt/us/koreader/crash.log | grep Companion
   ```

4. **Test with heartbeat**
   - Kindle: Settings → Companion App → Test Connection

### Browser shows "No events yet"

- Wait for an AI query (highlight text → use assistant)
- Or run `python3 examples/test_client.py` to generate test data
- Check browser console (F12) for JavaScript errors

## Advanced Configuration

### Change Network Interface

Edit `companion/app.py`:

```python
# Listen only on localhost (more secure)
app.run(host='127.0.0.1', port=8080)

# Or specific interface
app.run(host='192.168.1.102', port=8080)
```

### Enable Debug Mode

```python
app.run(host='0.0.0.0', port=8080, debug=True)
```

### Customize Buffer Size

Edit `kindle-module/assistant_companion.lua`:

```lua
max_buffer_size = 200,  -- Increase from 100
```

### Log to File

Add to `companion/app.py`:

```python
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('companion.log'),
        logging.StreamHandler()
    ]
)
```

## Architecture Summary

```
┌──────────────┐
│   Kindle     │
│  KOReader    │
└──────┬───────┘
       │ HTTP POST /events
       │ (Fire-and-forget)
       │
       ▼
┌──────────────┐
│  Mac/Flask   │
│  :8080       │
└──────┬───────┘
       │ Server-Sent Events /stream
       │ (Real-time push)
       │
       ▼
┌──────────────┐
│   Browser    │
│  Dashboard   │
└──────────────┘
```

## Next Steps

1. ✅ **You're done!** Try highlighting text and using AI features
2. **Customize**: Add more event types in `assistant_companion.lua`
3. **Extend**: Add persistence, token tracking, etc.
4. **Share**: Help improve the companion app

## Common Use Cases

### Debug AI Prompts
- Go to "Prompts" tab
- See exactly what's being sent to the AI
- Verify system prompts and message history

### Monitor Performance
- "Stats" tab shows query counts
- See which providers/models are used most
- Identify errors and patterns

### Save Conversations
- Right-click → "Save as..." on Raw Events tab
- Or add export feature to Flask app

### Development
- Test new prompts without checking logs
- See streaming behavior in real-time
- Debug API integration issues

## Support

For issues:
1. Check KOReader logs: `/mnt/us/koreader/crash.log`
2. Check Flask console output
3. Run `python3 examples/test_client.py` to isolate issues
4. Review `kindle-module/INTEGRATION.md`

Enjoy your new AI development superpowers! 🚀
