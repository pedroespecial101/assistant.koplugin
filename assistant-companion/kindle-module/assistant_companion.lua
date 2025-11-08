--[[
    Companion App HTTP Reporter Module
    
    Sends AI Assistant events to a companion Mac application for real-time monitoring.
    This is a development/debugging tool and should be used with caution.
    
    Usage:
        local Companion = require("assistant_companion")
        local companion = Companion:new(settings)
        
        if companion:is_enabled() then
            companion:send("query_start", { provider = "openai", model = "gpt-4" })
        end
]]

local logger = require("logger")
local http = require("socket.http")
local ltn12 = require("ltn12")
local JSON = require("json")

local Companion = {}

function Companion:new(settings)
    local o = {
        settings = settings,
        enabled = false,
        url = nil,
        buffer = {},
        max_buffer_size = 100,
        last_error_time = 0,
        error_cooldown = 30, -- Don't spam errors more than once per 30 seconds
    }
    setmetatable(o, self)
    self.__index = self
    
    -- Initialize from settings
    o:_init_from_settings()
    
    return o
end

function Companion:_init_from_settings()
    self.enabled = self.settings:readSetting("companion_enabled") == true
    self.url = self.settings:readSetting("companion_url") or "http://192.168.1.102:8080"
    
    if self.enabled then
        logger.info("[Companion] Enabled, endpoint:", self.url)
    end
end

function Companion:is_enabled()
    return self.enabled
end

function Companion:set_enabled(enabled)
    self.enabled = enabled
    self.settings:saveSetting("companion_enabled", enabled)
    if enabled then
        logger.info("[Companion] Enabled")
        self:send("heartbeat", { status = "enabled" })
    else
        logger.info("[Companion] Disabled")
    end
end

function Companion:set_url(url)
    self.url = url
    self.settings:saveSetting("companion_url", url)
    logger.info("[Companion] URL updated:", url)
end

function Companion:get_url()
    return self.url
end

--[[
    Send an event to the companion app
    
    @param event_type: string - Type of event (query_start, stream_chunk, error, etc.)
    @param data: table - Event data payload
    @return boolean - true if sent successfully or buffered, false on error
]]
function Companion:send(event_type, data)
    if not self.enabled then
        return false
    end
    
    local event = {
        event = event_type,
        timestamp = os.time(),
        data = data or {},
    }
    
    -- Try to send
    local success = self:_http_post(event)
    
    if not success then
        -- Buffer if send failed
        self:_buffer_event(event)
    else
        -- If send succeeded, try to flush buffer
        self:_flush_buffer()
    end
    
    return success
end

--[[
    Internal HTTP POST implementation
    Non-blocking fire-and-forget style
]]
function Companion:_http_post(event)
    if not self.url then
        return false
    end
    
    local ok, json_str = pcall(JSON.encode, event)
    if not ok then
        logger.warn("[Companion] Failed to encode JSON:", json_str)
        return false
    end
    
    local sink = {}
    local url = self.url .. "/events"
    
    -- Set timeout to avoid blocking
    local old_timeout = http.TIMEOUT
    http.TIMEOUT = 2 -- 2 second timeout
    
    local _, status_code = pcall(function()
        return http.request{
            url = url,
            method = "POST",
            headers = {
                ["Content-Type"] = "application/json",
                ["Content-Length"] = tostring(#json_str),
                ["User-Agent"] = "KOReader-AI-Assistant/1.0",
            },
            source = ltn12.source.string(json_str),
            sink = ltn12.sink.table(sink),
        }
    end)
    
    -- Restore timeout
    http.TIMEOUT = old_timeout
    
    if status_code == 200 or status_code == true then
        return true
    else
        -- Only log errors if not in cooldown
        if os.time() - self.last_error_time > self.error_cooldown then
            logger.warn("[Companion] HTTP error:", status_code, "- buffering event")
            self.last_error_time = os.time()
        end
        return false
    end
end

--[[
    Buffer an event when companion is unreachable
]]
function Companion:_buffer_event(event)
    table.insert(self.buffer, event)
    
    -- Limit buffer size
    if #self.buffer > self.max_buffer_size then
        table.remove(self.buffer, 1) -- Remove oldest
        logger.dbg("[Companion] Buffer full, dropped oldest event")
    end
    
    logger.dbg("[Companion] Buffered event, buffer size:", #self.buffer)
end

--[[
    Try to flush buffered events
]]
function Companion:_flush_buffer()
    if #self.buffer == 0 then
        return
    end
    
    logger.info("[Companion] Flushing", #self.buffer, "buffered events")
    
    local sent_count = 0
    local max_flush = 10 -- Don't send too many at once
    
    while #self.buffer > 0 and sent_count < max_flush do
        local event = table.remove(self.buffer, 1)
        if self:_http_post(event) then
            sent_count = sent_count + 1
        else
            -- Put it back and stop trying
            table.insert(self.buffer, 1, event)
            break
        end
    end
    
    if sent_count > 0 then
        logger.info("[Companion] Flushed", sent_count, "events, remaining:", #self.buffer)
    end
end

--[[
    Clear the buffer
]]
function Companion:clear_buffer()
    local count = #self.buffer
    self.buffer = {}
    logger.info("[Companion] Cleared buffer, removed", count, "events")
end

--[[
    Get current status
]]
function Companion:get_status()
    return {
        enabled = self.enabled,
        url = self.url,
        buffered_events = #self.buffer,
    }
end

return Companion
