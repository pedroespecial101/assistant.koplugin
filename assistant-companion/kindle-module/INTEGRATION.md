# Integration Guide: Companion Module

This guide explains how to integrate the companion module into the main AI Assistant plugin.

## Files to Modify

### 1. Copy the Companion Module

```bash
cp assistant_companion.lua ../
```

### 2. Modify `assistant_querier.lua`

Add companion support to the query method.

**At the top of the file** (around line 10, after other requires):

```lua
local Companion = require("assistant_companion")
```

**In `Querier:init()`** (around line 140):

```lua
function Querier:init(settings)
    self.settings = settings
    -- ...existing code...
    
    -- Initialize companion
    self.companion = Companion:new(settings)
    
    -- ...rest of existing code...
end
```

**In `Querier:query()`** (around line 180, after validation):

```lua
function Querier:query(message_history, title)
    if not self:is_inited() then
        return nil, _("Plugin is not configured.")
    end
    
    -- NEW: Report query start to companion
    if self.companion:is_enabled() then
        self.companion:send("query_start", {
            provider = self.provider_name,
            model = self.provider_settings.model,
            title = title,
            history = message_history,
        })
    end
    
    -- ...existing query code...
```

**In the streaming loop** (around line 342, where chunks are processed):

```lua
-- Inside the while true loop, after content is extracted
if ok and event then
    local reasoning_content, content
    -- ...existing parsing code...
    
    -- NEW: Report chunk to companion
    if self.companion:is_enabled() and (content or reasoning_content) then
        self.companion:send("stream_chunk", {
            content = content,
            reasoning = reasoning_content,
        })
    end
    
    -- ...existing code to append to response_text...
end
```

**In error handling** (around line 400+, where errors are caught):

```lua
-- When an error occurs
if not ok then
    local error_msg = response_text or "Unknown error"
    
    -- NEW: Report error to companion
    if self.companion:is_enabled() then
        self.companion:send("error", {
            message = error_msg,
            provider = self.provider_name,
        })
    end
    
    return nil, error_msg
end
```

**When query completes successfully** (at the end of query method):

```lua
-- Before returning response_text
if self.companion:is_enabled() then
    self.companion:send("query_complete", {
        response_length = #response_text,
        duration = os.time() - start_time,
    })
end

return response_text
```

### 3. Modify `assistant_settings.lua`

Add companion settings to the settings menu.

**Find the settings table** (around line 50+) and add:

```lua
{
    text = _("Companion App (Dev Mode)"),
    separator = true,
    sub_item_table = {
        {
            text = _("Enable Companion App"),
            checked_func = function()
                return self.settings:readSetting("companion_enabled") == true
            end,
            callback = function()
                local current = self.settings:readSetting("companion_enabled")
                self.settings:saveSetting("companion_enabled", not current)
                
                -- Notify user
                if not current then
                    UIManager:show(InfoMessage:new{
                        text = _("Companion app enabled. Make sure the server is running on your Mac."),
                        timeout = 3,
                    })
                else
                    UIManager:show(InfoMessage:new{
                        text = _("Companion app disabled."),
                        timeout = 2,
                    })
                end
            end,
        },
        {
            text = _("Configure Endpoint"),
            keep_menu_open = true,
            callback = function()
                local InputDialog = require("ui/widget/inputdialog")
                local current_url = self.settings:readSetting("companion_url") or "http://192.168.1.102:8080"
                
                local input_dialog
                input_dialog = InputDialog:new{
                    title = _("Companion App Endpoint"),
                    input = current_url,
                    input_hint = "http://YOUR_MAC_IP:8080",
                    input_type = "text",
                    buttons = {
                        {
                            {
                                text = _("Cancel"),
                                callback = function()
                                    UIManager:close(input_dialog)
                                end,
                            },
                            {
                                text = _("Save"),
                                is_enter_default = true,
                                callback = function()
                                    local url = input_dialog:getInputText()
                                    if url and url ~= "" then
                                        self.settings:saveSetting("companion_url", url)
                                        UIManager:show(InfoMessage:new{
                                            text = _("Companion endpoint saved: ") .. url,
                                            timeout = 2,
                                        })
                                    end
                                    UIManager:close(input_dialog)
                                end,
                            },
                        },
                    },
                }
                UIManager:show(input_dialog)
                input_dialog:onShowKeyboard()
            end,
        },
        {
            text = _("Test Connection"),
            callback = function()
                local Companion = require("assistant_companion")
                local companion = Companion:new(self.settings)
                
                if not companion:is_enabled() then
                    UIManager:show(InfoMessage:new{
                        text = _("Companion app is disabled. Enable it first."),
                        timeout = 2,
                    })
                    return
                end
                
                local success = companion:send("heartbeat", {
                    test = true,
                    message = "Test from KOReader",
                })
                
                if success then
                    UIManager:show(InfoMessage:new{
                        text = _("Test event sent! Check your Mac companion app."),
                        timeout = 3,
                    })
                else
                    UIManager:show(InfoMessage:new{
                        text = _("Connection failed. Check the endpoint URL and make sure the server is running."),
                        timeout = 4,
                    })
                end
            end,
        },
        {
            text = _("About Companion App"),
            keep_menu_open = true,
            callback = function()
                UIManager:show(InfoMessage:new{
                    text = _([[Companion App is a development tool that displays AI Assistant activity on your Mac in real-time.

⚠️ Security Warning:
- No authentication
- Logs contain book content
- Use only on trusted networks
- For development/debugging only

To use:
1. Start companion server on Mac
2. Enable companion app here
3. Verify endpoint URL
4. Test connection

Events are buffered if server is unreachable.]]),
                    timeout = 0, -- Require manual dismiss
                })
            end,
        },
    },
},
```

**Add the required imports** at the top of `assistant_settings.lua`:

```lua
local InfoMessage = require("ui/widget/infomessage")
local UIManager = require("ui/uimanager")
```

## Testing the Integration

### 1. Check for Syntax Errors

On the Kindle, check `/mnt/us/koreader/crash.log` after restarting KOReader.

### 2. Enable Companion Mode

1. Open a book
2. Menu → Settings → AI Assistant Settings
3. Scroll down to "Companion App (Dev Mode)"
4. Enable it
5. Test Connection

### 3. Try a Query

1. Highlight some text
2. Use any AI Assistant feature
3. Check the companion app on your Mac

## Troubleshooting

### Plugin Won't Load

- Check Lua syntax: `luac -p assistant_companion.lua`
- Review `/mnt/us/koreader/crash.log`
- Ensure all `require()` statements are correct

### No Events Appearing

1. Check KOReader log: `tail -f /mnt/us/koreader/crash.log`
2. Look for "[Companion]" log messages
3. Verify companion is enabled in settings
4. Check Mac server is running and reachable

### Events Buffering

- Companion will buffer up to 100 events if server is unreachable
- Check network connectivity
- Verify endpoint URL is correct
- Ensure no firewall blocking port 8080

## Reverting Changes

To remove companion integration:

1. Comment out or remove the companion code sections
2. Or simply disable it in settings (no performance impact when disabled)
3. Delete `assistant_companion.lua` if desired

## Performance Notes

- When disabled: Zero overhead
- When enabled: ~1-2ms per event
- HTTP calls are fire-and-forget (non-blocking)
- Automatic error cooldown prevents log spam
- Buffer prevents memory issues

## Next Steps

Once integrated:
- Customize event data to include more metrics
- Add token usage tracking
- Implement bidirectional communication
- Add authentication for production use
