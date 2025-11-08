-- assistant_imagedialog.lua
-- Module for AI image generation functionality

local Device = require("device")
local InputDialog = require("ui/widget/inputdialog")
local UIManager = require("ui/uimanager")
local InfoMessage = require("ui/widget/infomessage")
local ConfirmBox = require("ui/widget/confirmbox")
local logger = require("logger")
local T = require("ffi/util").template
local util = require("util")
local _ = require("assistant_gettext")
local assistant_utils = require("assistant_utils")
local NetworkMgr = require("ui/network/manager")
local Trapper = require("ui/trapper")
local Font = require("ui/font")
local Size = require("ui/size")
local Screen = Device.screen

local ImageDialog = {}

function ImageDialog:new(assistant)
  local o = {
    assistant = assistant,
  }
  setmetatable(o, self)
  self.__index = self
  return o
end

function ImageDialog:show()
  self:createImageInputDialog()
end

-- Generate image with a pre-formatted prompt (for book-level prompts)
function ImageDialog:generateImageWithPrompt(formatted_prompt, system_prompt)
  -- Show loading message
  local loading_msg = InfoMessage:new{
    icon = "book.opened",
    text = _("Generating image..."),
  }
  UIManager:show(loading_msg)
  
  -- Create a specialized querier for image generation
  local image_querier = require("assistant_querier"):new({
    assistant = self.assistant,
    settings = self.assistant.settings,
  })
  
  -- Load the gemini_image provider (for image generation via OpenRouter)
  local ok, err = image_querier:load_model("gemini_image")
  if not ok then
    UIManager:close(loading_msg)
    UIManager:show(InfoMessage:new{
      text = T(_("Failed to load image generation model: %1"), err or _("Unknown error")),
      icon = "notice-warning"
    })
    return
  end
  
  -- Use the provided system prompt or default
  local sys_prompt = system_prompt or "You are an AI image generation assistant."
  
  -- Build message history
  local message_history = {
    {
      role = "system",
      content = sys_prompt
    },
    {
      role = "user",
      content = formatted_prompt
    }
  }
  
  local answer, err = image_querier:query(message_history, _("Generating image..."))
  
  UIManager:close(loading_msg)
  
  if err then
    image_querier:showError(err)
    return
  end
  
  if answer then
    -- Check if we got an image response
    if type(answer) == "table" and answer.type == "image" and answer.image_url then
      -- Handle image URL response
      self:handleImageResponse(formatted_prompt, answer.image_url)
    elseif type(answer) == "string" then
      -- Handle text response (fallback)
      UIManager:show(InfoMessage:new{
        text = T(_("Image generation response:\n\n%1\n\nNote: The response appears to be text rather than an image. This might indicate an issue with the image generation model configuration."), answer),
        timeout = 15
      })
      
      -- Save the response to notebook
      self:saveImageResponse(formatted_prompt, answer)
    else
      UIManager:show(InfoMessage:new{
        text = _("Unexpected response format from image generation service."),
        icon = "notice-warning"
      })
    end
  else
    UIManager:show(InfoMessage:new{
      text = _("No response received from image generation service."),
      icon = "notice-warning"
    })
  end
end

function ImageDialog:createImageInputDialog()
  self.input_dialog = InputDialog:new {
    title = _("Generate Image from Description"),
    input = "",
    input_hint = _("Describe the image you want to generate..."),
    input_type = "text",
    input_height = 6,
    allow_newline = true,
    input_multiline = true,
    text_height = math.floor(10 * Screen:scaleBySize(20)),
    width = Screen:getWidth() * 0.8,
    height = Screen:getHeight() * 0.4,
    buttons = {{
      {
        text = _("Cancel"),
        id = "cancel",
        callback = function()
          if self.input_dialog then
            UIManager:close(self.input_dialog)
            self.input_dialog = nil
          end
        end
      },
      {
        text = _("Generate"),
        is_enter_default = true,
        callback = function()
          local description = self.input_dialog:getInputText()
          if description and description:trim() ~= "" then
            UIManager:close(self.input_dialog)
            self.input_dialog = nil
            self:generateImage(description)
          else
            UIManager:show(InfoMessage:new{
              text = _("Please enter a description for the image."),
              timeout = 3
            })
          end
        end
      }
    }}
  }
  
  UIManager:show(self.input_dialog)
end

function ImageDialog:generateImage(description)
  -- Show loading message
  local loading_msg = InfoMessage:new{
    icon = "book.opened",
    text = _("Generating image with Nano Banana..."),
  }
  UIManager:show(loading_msg)
  
  -- Create a specialized querier for image generation
  local image_querier = require("assistant_querier"):new({
    assistant = self.assistant,
    settings = self.assistant.settings,
  })
  
  -- Load the gemini_image provider (for image generation via OpenRouter)
  local ok, err = image_querier:load_model("gemini_image")
  if not ok then
    UIManager:close(loading_msg)
    UIManager:show(InfoMessage:new{
      text = T(_("Failed to load image generation model: %1"), err or _("Unknown error")),
      icon = "notice-warning"
    })
    return
  end
  
  -- Get book context
  local DocSettings = require("docsettings")
  local doc = self.assistant.ui.document
  local doc_settings = DocSettings:open(doc.file)
  local percent_finished = doc_settings:readSetting("percent_finished") or 0
  local doc_props = doc_settings:child("doc_props")
  local title = doc_props:readSetting("title") or doc:getProps().title or "Unknown Title"
  local author = doc_props:readSetting("authors") or doc:getProps().authors or "Unknown Author"
  
  -- Get the prompt configuration (allow customization)
  local Prompts = require("assistant_prompts")
  local koutil = require("util")
  local user_prompts = koutil.tableGetValue(self.assistant.CONFIGURATION, "features", "prompts")
  local prompt_config = Prompts.getMergedCustomPrompts(user_prompts)["generate_image"]
  
  if not prompt_config then
    -- Fallback if prompt not found
    prompt_config = Prompts.assistant_prompts.generate_image
  end
  
  -- Get language setting
  local language = self.assistant.settings:readSetting("response_language", "English")
  
  -- Format the user prompt with placeholders
  local user_content = (prompt_config.user_prompt or ""):gsub("{(%w+)}", {
    user_input = description,
    title = title,
    author = author,
    progress = string.format("%.1f", percent_finished * 100),
    language = language
  })
  
  -- Get system prompt
  local system_prompt = prompt_config.system_prompt or "You are an AI image generation assistant."
  
  -- Build message history
  local message_history = {
    {
      role = "system",
      content = system_prompt
    },
    {
      role = "user",
      content = user_content
    }
  }
  
  local answer, err = image_querier:query(message_history, _("Generating image..."))
  
  UIManager:close(loading_msg)
  
  if err then
    image_querier:showError(err)
    return
  end
  
  if answer then
    -- Check if we got an image response
    if type(answer) == "table" and answer.type == "image" and answer.image_url then
      -- Handle image URL response
      self:handleImageResponse(description, answer.image_url)
    elseif type(answer) == "string" then
      -- Handle text response (fallback)
      UIManager:show(InfoMessage:new{
        text = T(_("Image generation response:\n\n%1\n\nNote: The response appears to be text rather than an image. This might indicate an issue with the image generation model configuration."), answer),
        timeout = 15
      })
      
      -- Save the response to notebook
      self:saveImageResponse(description, answer)
    else
      UIManager:show(InfoMessage:new{
        text = _("Unexpected response format from image generation service."),
        icon = "notice-warning"
      })
    end
  else
    UIManager:show(InfoMessage:new{
      text = _("No response received from image generation service."),
      icon = "notice-warning"
    })
  end
end

function ImageDialog:handleImageResponse(description, image_url)
  -- Show success message with image URL
  UIManager:show(InfoMessage:new{
    text = T(_("Image generated successfully!\n\nImage URL: %1\n\nThe image has been saved to your notebook."), image_url),
    timeout = 10
  })
  
  -- Save the image information to notebook
  local timestamp = os.date("%Y-%m-%d %H:%M:%S")
  local log_entry = string.format("\n\n## Image Generation - %s\n\n**Description:** %s\n\n**Image URL:** %s\n\n**Note:** You can download this image by visiting the URL above.\n\n---\n", 
    timestamp, description, image_url)
  
  assistant_utils.saveToNotebookFile(self.assistant, log_entry)
  
  -- Try to download and save the image locally
  self:downloadAndSaveImage(description, image_url)
end

function ImageDialog:downloadAndSaveImage(description, image_url)
  -- Show downloading message
  local downloading_msg = InfoMessage:new{
    icon = "book.opened",
    text = _("Downloading image..."),
  }
  UIManager:show(downloading_msg)
  
  -- Use the existing HTTP client from the base handler
  local BaseHandler = require("api_handlers.base")
  local handler = BaseHandler:new()
  
  -- Download the image
  local status, code, response = handler:makeRequest(image_url, {
    ["User-Agent"] = "assistant.koplugin/1.0"
  }, nil, "GET")
  
  UIManager:close(downloading_msg)
  
  if status and response then
    -- Generate a filename based on description and timestamp
    local timestamp = os.date("%Y%m%d_%H%M%S")
    local safe_description = description:gsub("[^%w%s]", ""):gsub("%s+", "_"):sub(1, 30)
    local filename = string.format("generated_image_%s_%s.png", safe_description, timestamp)
    
    -- Get the appropriate directory for saving
    local default_folder = util.tableGetValue(self.assistant.CONFIGURATION, "features", "default_folder_for_logs")
    local home_dir = G_reader_settings:readSetting("home_dir")
    local current_dir = self.assistant.ui.file_chooser and self.assistant.ui.file_chooser.path or self.assistant.ui:getLastDirFile()
    local target_dir = default_folder and default_folder ~= "" and util.pathExists(default_folder) and default_folder or (home_dir or current_dir)
    
    if target_dir then
      local filepath = target_dir .. "/" .. filename
      
      -- Save the image file
      local file = io.open(filepath, "wb")
      if file then
        file:write(response)
        file:close()
        
        UIManager:show(InfoMessage:new{
          text = T(_("Image saved successfully!\n\nFile: %1\n\nYou can view this image using your device's file manager."), filepath),
          timeout = 8
        })
        
        -- Show image information dialog
        self:showImageInfoDialog(description, filepath)
        
        logger.info("Image saved to:", filepath)
      else
        UIManager:show(InfoMessage:new{
          text = T(_("Failed to save image file: %1"), filepath),
          icon = "notice-warning",
          timeout = 5
        })
      end
    else
      UIManager:show(InfoMessage:new{
        text = _("Could not determine save directory for image."),
        icon = "notice-warning",
        timeout = 5
      })
    end
  else
    UIManager:show(InfoMessage:new{
      text = T(_("Failed to download image: %1"), code or _("Unknown error")),
      icon = "notice-warning",
      timeout = 5
    })
    logger.warn("Failed to download image:", code, response)
  end
end

function ImageDialog:showImageInfoDialog(description, filepath)
  -- Get file size and basic info
  local file_size = 0
  local file_exists = false
  local file = io.open(filepath, "rb")
  if file then
    file_size = file:seek("end")
    file:close()
    file_exists = true
  end
  
  local size_text = ""
  if file_size > 0 then
    if file_size > 1024 * 1024 then
      size_text = string.format("%.1f MB", file_size / (1024 * 1024))
    elseif file_size > 1024 then
      size_text = string.format("%.1f KB", file_size / 1024)
    else
      size_text = string.format("%d bytes", file_size)
    end
  end
  
  local info_text = string.format([[
Generated Image Information

Description: %s
File: %s
Size: %s
Status: %s

Note: Due to e-ink display limitations, the image cannot be displayed directly in this interface. You can view it using your device's file manager or transfer it to another device for viewing.
]], 
    description,
    filepath,
    size_text,
    file_exists and "Saved successfully" or "Save failed"
  )
  
  UIManager:show(ConfirmBox:new{
    title = _("Image Generated"),
    text = info_text,
    ok_text = _("OK"),
    ok_callback = function()
      -- Optional: Open file manager to the image location
      if self.assistant.ui.file_chooser then
        local dir = filepath:match("(.*/)")
        if dir then
          self.assistant.ui.file_chooser:changeToPath(dir)
        end
      end
    end,
    other_buttons = {{
      {
        text = _("Open File Manager"),
        callback = function()
          if self.assistant.ui.file_chooser then
            local dir = filepath:match("(.*/)")
            if dir then
              self.assistant.ui.file_chooser:changeToPath(dir)
            end
          end
        end
      }
    }}
  })
end

function ImageDialog:saveImageResponse(description, response)
  local timestamp = os.date("%Y-%m-%d %H:%M:%S")
  local log_entry = string.format("\n\n## Image Generation - %s\n\n**Description:** %s\n\n**Response:** %s\n\n---\n", 
    timestamp, description, response)
  
  -- Save to notebook using the existing utility
  assistant_utils.saveToNotebookFile(self.assistant, log_entry)
  
  UIManager:show(InfoMessage:new{
    text = _("Image generation response saved to notebook."),
    timeout = 3
  })
end

-- Main function to show the image dialog
local function showImageDialog(assistant)
  local dialog = ImageDialog:new(assistant)
  dialog:show()
end

return showImageDialog
