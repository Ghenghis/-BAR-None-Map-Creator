# Beyond All Reason - AI Map Creator

A user-friendly, AI-powered map generator for Beyond All Reason. No coding required!

## Features

- AI-generated terrain patterns (mountains, rivers, plateaus, craters, hills, archipelagos)
- Customizable map settings (size, metal spots, hills, random seed, terrain type)
- Live preview generation
- Complete map file creation for BAR
- **OpenAI chatbox:** Ask for help, suggestions, or design changes using text or your microphone
- Robust error handling and clear feedback for all actions

## Requirements

- Windows 11 (recommended)
- Python 3.7+
- Required packages (install with `pip install -r requirements.txt`):
  - numpy
  - pillow
  - scipy
  - openai
  - python-dotenv
  - speechrecognition
  - pyaudio

## Installation

1. Install Python 3.7+ from [python.org](https://www.python.org/downloads/)
2. Download or clone this repository
3. Open a terminal in the project directory
4. Install requirements:
   ```
   pip install -r requirements.txt
   ```
5. Copy `.env.example` to `.env` and fill in your OpenAI API key:
   - `OPENAI_API_KEY=your-key-here`

## Usage

1. Run the app:
   ```
   python map_creator_app.py
   ```
2. Configure map settings (name, description, size, terrain type, etc.)
3. Click **Generate Preview** to see your terrain
4. Click **Create Map** to generate a BAR-compatible map file
5. (Optional) Use the **chatbox** at the bottom to:
   - Ask for map design suggestions
   - Get help with errors or features
   - Use your microphone (click 🎤) to dictate messages
6. Copy the generated files from the output directory to your BAR maps directory
7. Your map will appear in the game's map selection menu

## Troubleshooting & Error Feedback

- **Invalid input:** If you enter an out-of-range value (e.g., map size too small), you'll see a warning popup and a chat message.
- **OpenAI or mic errors:** Any issues with OpenAI or microphone use will show as clear errors in the chat and as popups.
- **General errors:** All unexpected issues are caught and reported—no crashes!

## Map Types

- **Mountain Range:** Creates mountain ridges with peaks
- **River Valley:** Creates a river valley with surrounding terrain
- **Plateau:** Creates elevated flat areas with cliff edges
- **Crater:** Creates a terrain with multiple impact craters
- **Hills:** Creates a natural hilly terrain
- **Archipelago:** Creates islands surrounded by water

## FAQ

**Q: Do I need to know how to code?**
A: No! All features are accessible via the app's graphical interface.

**Q: What if I get an error?**
A: The app will always show a clear message and suggest how to fix it. Check the chatbox and popups for details.

**Q: How do I use the AI chatbox?**
A: Type your question or request, or use the 🎤 button to speak. The AI will respond in the chat area.

## Credits

Created with AI assistance for the Beyond All Reason community.

---

**Need help?**
- Use the chatbox in the app
- Check the chat and popups for troubleshooting tips
- Visit the BAR community forums for more support
