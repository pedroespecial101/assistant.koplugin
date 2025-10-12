# Changelog

All notable changes to the Assistant AI Helper Plugin for KOReader will be documented in this file.

## [Unreleased]

### Added
- **Image Generation Feature**: Added new menu item "Generate Image from Description" that uses Gemini 2.5 Flash Image (Nano Banana) via OpenRouter
  - New menu item available in both reader and filemanager modes
  - Uses the `google/gemini-2.5-flash-image` model for AI-powered image generation
  - Automatically downloads and saves generated images as PNG files
  - Saves image generation logs to the notebook for future reference
  - Provides image information dialog with file details and file manager integration
  - Supports configurable image parameters (aspect ratio, quality) through configuration.lua
  - New API handler `gemini_image` for specialized image generation requests

### Technical Details
- Added `assistant_imagedialog.lua` module for image generation UI and functionality
- Added `api_handlers/gemini_image.lua` for Gemini 2.5 Flash Image API integration
- Updated `configuration.lua` with new `gemini_image` provider configuration
- Updated `main.lua` with new menu items and event handlers for image generation
- Integrated with existing notebook system for logging image generation requests and responses

### Configuration
- New provider `gemini_image` available in configuration.lua
- Configurable image parameters: aspect_ratio (1:1, 16:9, 9:16, 4:3, 3:4) and quality (low, medium, high)
- Uses same OpenRouter API key as other providers
- Images saved to configured default folder or current directory

### Usage
1. Highlight text or select "Generate Image from Description" from the AI Assistant menu
2. Enter a description of the image you want to generate
3. The AI will generate an image using Gemini 2.5 Flash Image (Nano Banana)
4. The image will be automatically downloaded and saved as a PNG file
5. Image information and generation log will be saved to your notebook
6. Use the file manager integration to easily locate and view generated images

### Limitations
- Images cannot be displayed directly in the KOReader interface due to e-ink display limitations
- Generated images must be viewed using the device's file manager or transferred to another device
- Requires internet connection for image generation and download
- Image generation is subject to OpenRouter API rate limits and costs

---

## Previous Versions

*This changelog was created to document the new image generation feature. Previous versions of the plugin did not maintain a formal changelog.*
