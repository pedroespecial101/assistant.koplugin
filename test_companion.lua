#!/usr/bin/env lua
--[[
    Test suite for assistant_companion module
    Tests the companion module functionality in isolation
]]

local passed = 0
local failed = 0
local tests = {}

-- Mock logger for testing
local logger = {
    info = function(...) print("[INFO]", ...) end,
    warn = function(...) print("[WARN]", ...) end,
    dbg = function(...) print("[DEBUG]", ...) end,
    err = function(...) print("[ERROR]", ...) end,
}
_G.logger = logger

-- Mock settings for testing
local MockSettings = {}
function MockSettings:new()
    local o = {
        settings = {}
    }
    setmetatable(o, self)
    self.__index = self
    return o
end

function MockSettings:readSetting(key, default)
    return self.settings[key] or default
end

function MockSettings:saveSetting(key, value)
    self.settings[key] = value
end

-- Helper function to run a test
local function test(name, func)
    table.insert(tests, {name = name, func = func})
end

-- Helper function to assert
local function assert_eq(actual, expected, msg)
    if actual == expected then
        return true
    else
        error(string.format("%s: expected %s, got %s", msg or "Assertion failed", tostring(expected), tostring(actual)))
    end
end

local function assert_true(value, msg)
    if value then
        return true
    else
        error(msg or "Expected true, got false")
    end
end

local function assert_false(value, msg)
    if not value then
        return true
    else
        error(msg or "Expected false, got true")
    end
end

-- Test 1: Module can be loaded
test("Module loads successfully", function()
    local ok, Companion = pcall(require, "assistant_companion")
    assert_true(ok, "Module should load without errors")
    assert_true(Companion ~= nil, "Module should return a table")
end)

-- Test 2: Can create a companion instance
test("Can create companion instance", function()
    local Companion = require("assistant_companion")
    local settings = MockSettings:new()
    local companion = Companion:new(settings)
    
    assert_true(companion ~= nil, "Should create instance")
    assert_true(companion.settings ~= nil, "Should have settings")
    assert_eq(companion.enabled, false, "Should be disabled by default")
end)

-- Test 3: Enable/disable functionality
test("Enable and disable companion", function()
    local Companion = require("assistant_companion")
    local settings = MockSettings:new()
    local companion = Companion:new(settings)
    
    assert_false(companion:is_enabled(), "Should start disabled")
    
    companion:set_enabled(true)
    assert_true(companion:is_enabled(), "Should be enabled after set_enabled(true)")
    assert_eq(settings.settings.companion_enabled, true, "Should save to settings")
    
    companion:set_enabled(false)
    assert_false(companion:is_enabled(), "Should be disabled after set_enabled(false)")
end)

-- Test 4: URL configuration
test("URL configuration", function()
    local Companion = require("assistant_companion")
    local settings = MockSettings:new()
    local companion = Companion:new(settings)
    
    local default_url = companion:get_url()
    assert_eq(default_url, "http://192.168.1.102:8080", "Should have default URL")
    
    companion:set_url("http://192.168.1.100:9090")
    assert_eq(companion:get_url(), "http://192.168.1.100:9090", "Should update URL")
    assert_eq(settings.settings.companion_url, "http://192.168.1.100:9090", "Should save to settings")
end)

-- Test 5: Send when disabled (should return false)
test("Send returns false when disabled", function()
    local Companion = require("assistant_companion")
    local settings = MockSettings:new()
    local companion = Companion:new(settings)
    
    local result = companion:send("test_event", {data = "test"})
    assert_false(result, "Should return false when disabled")
end)

-- Test 6: Buffering functionality
test("Event buffering", function()
    local Companion = require("assistant_companion")
    local settings = MockSettings:new()
    local companion = Companion:new(settings)
    companion:set_enabled(true)
    
    -- Set invalid URL to force buffering
    companion:set_url("http://invalid-host-that-does-not-exist:9999")
    
    -- Send should return false (couldn't send) but event should be buffered
    companion:send("test_event", {data = "test1"})
    companion:send("test_event", {data = "test2"})
    
    local status = companion:get_status()
    assert_true(status.buffered_events > 0, "Should buffer events when send fails")
end)

-- Test 7: Clear buffer
test("Clear buffer", function()
    local Companion = require("assistant_companion")
    local settings = MockSettings:new()
    local companion = Companion:new(settings)
    companion:set_enabled(true)
    companion:set_url("http://invalid-host:9999")
    
    -- Buffer some events
    companion:send("test", {})
    companion:send("test", {})
    
    local status_before = companion:get_status()
    assert_true(status_before.buffered_events > 0, "Should have buffered events")
    
    companion:clear_buffer()
    
    local status_after = companion:get_status()
    assert_eq(status_after.buffered_events, 0, "Buffer should be empty after clear")
end)

-- Test 8: Status reporting
test("Get status", function()
    local Companion = require("assistant_companion")
    local settings = MockSettings:new()
    local companion = Companion:new(settings)
    
    companion:set_enabled(true)
    companion:set_url("http://test:8080")
    
    local status = companion:get_status()
    assert_true(status.enabled, "Status should show enabled")
    assert_eq(status.url, "http://test:8080", "Status should show URL")
    assert_eq(status.buffered_events, 0, "Status should show buffer count")
end)

-- Test 9: Settings persistence
test("Settings persistence", function()
    local Companion = require("assistant_companion")
    local settings = MockSettings:new()
    
    -- Set some settings
    settings:saveSetting("companion_enabled", true)
    settings:saveSetting("companion_url", "http://192.168.1.50:7070")
    
    -- Create new companion instance
    local companion = Companion:new(settings)
    
    assert_true(companion:is_enabled(), "Should load enabled state from settings")
    assert_eq(companion:get_url(), "http://192.168.1.50:7070", "Should load URL from settings")
end)

-- Test 10: Buffer size limit
test("Buffer size limit", function()
    local Companion = require("assistant_companion")
    local settings = MockSettings:new()
    local companion = Companion:new(settings)
    companion:set_enabled(true)
    companion:set_url("http://invalid:9999")
    
    -- Try to overflow buffer (max is 100)
    for i = 1, 150 do
        companion:send("test", {count = i})
    end
    
    local status = companion:get_status()
    assert_true(status.buffered_events <= 100, "Buffer should not exceed max size")
end)

-- Run all tests
print("\n" .. string.rep("=", 60))
print("Running Companion Module Tests")
print(string.rep("=", 60) .. "\n")

for _, test_case in ipairs(tests) do
    io.write(string.format("%-50s ", test_case.name .. " ..."))
    io.flush()
    
    local ok, err = pcall(test_case.func)
    if ok then
        print("✓ PASS")
        passed = passed + 1
    else
        print("✗ FAIL")
        print("  Error: " .. tostring(err))
        failed = failed + 1
    end
end

print("\n" .. string.rep("=", 60))
print(string.format("Results: %d passed, %d failed (%.1f%%)", 
    passed, failed, (passed / (passed + failed)) * 100))
print(string.rep("=", 60) .. "\n")

-- Exit with error code if any tests failed
os.exit(failed == 0 and 0 or 1)
