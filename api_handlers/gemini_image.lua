local BaseHandler = require("api_handlers.base")
local json = require("json")
local koutil = require("util")
local logger = require("logger")

local GeminiImageHandler = BaseHandler:new()

function GeminiImageHandler:query(message_history, gemini_settings)
    
    local requestBodyTable = {
        model = gemini_settings.model or "google/gemini-2.5-flash-image",
        messages = message_history,
        max_tokens = gemini_settings.max_tokens or 4096,
        temperature = gemini_settings.temperature or 0.7,
        stream = koutil.tableGetValue(gemini_settings, "additional_parameters", "stream") or false,
        modalities = {"image", "text"}, -- Required for image generation
    }
    
    -- Add image generation specific parameters
    if gemini_settings.image_config then
        requestBodyTable.image_config = gemini_settings.image_config
    end
    
    -- Get additional parameters from settings
    local additional_params = gemini_settings.additional_parameters or {}
    if additional_params.image_config then
        requestBodyTable.image_config = additional_params.image_config
    end
    
    local requestBody = json.encode(requestBodyTable)
    local headers = {
        ["Content-Type"] = "application/json",
        ["Authorization"] = "Bearer " .. gemini_settings.api_key,
        ["HTTP-Referer"] = "https://github.com/omer-faruq/assistant.koplugin",
        ["X-Title"] = "assistant.koplugin"
    }

    if requestBodyTable.stream then
        -- For streaming responses, we need to handle the response differently
        headers["Accept"] = "text/event-stream"
        return self:backgroundRequest(gemini_settings.base_url, headers, requestBody)
    end
    
    local status, code, response = self:makeRequest(gemini_settings.base_url, headers, requestBody)

    if status then
        local success, responseData = pcall(json.decode, response)
        if success then
            -- Handle image generation response according to OpenRouter format
            -- Images are in message.images array, not in content
            local images = koutil.tableGetValue(responseData, "choices", 1, "message", "images")
            if images and type(images) == "table" and #images > 0 then
                -- Get the first image (or you could return all images)
                local first_image = images[1]
                if first_image and first_image.image_url and first_image.image_url.url then
                    return {
                        type = "image",
                        image_url = first_image.image_url.url,
                        images = images,  -- Include all images if there are multiple
                        content = koutil.tableGetValue(responseData, "choices", 1, "message", "content") or "Image generated successfully"
                    }
                end
            end
            
            -- Fallback to text content if no images
            local text_content = koutil.tableGetValue(responseData, "choices", 1, "message", "content")
            if text_content then return text_content end
        end
        
        -- server response error message
        logger.warn("API Error", code, response)
        if success then
            local err_msg = koutil.tableGetValue(responseData, "error", "message")
            if err_msg then return nil, err_msg end
        end
    end
    
    if code == BaseHandler.CODE_CANCELLED then
        return nil, response
    end
    return nil, "Error: " .. (code or "unknown") .. " - " .. response
end

return GeminiImageHandler
