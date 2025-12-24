# Telegram Web App Launcher

A Python script with a **beautiful terminal UI** to open Telegram web apps with initdata and fetch homepage content from Telegram sessions.

![Python Version](https://img.shields.io/badge/python-3.7+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## 🎨 Beautiful Terminal UI

This script features a stunning, colorful terminal interface powered by [Rich](https://github.com/Textualize/rich):
- 🌈 Multiple colors and styles
- 📊 Beautiful tables and panels
- ⚡ Progress indicators and spinners
- 🎯 Syntax highlighting for code previews
- ✨ Professional and modern design

### UI Demo

Run the demo to see the beautiful interface:
```bash
python demo_ui.py
```

## Features

- 🚀 Open Telegram web apps programmatically
- 🔑 Generate initData for web app authentication
- 📥 Fetch homepage content from Telegram bots/web apps
- 💾 Save initData and homepage to files
- 🔐 Secure session management with Telethon
- 🎨 **Beautiful, colorful terminal UI**
- 📊 **Interactive prompts and progress indicators**

## Prerequisites

- Python 3.7 or higher
- Telegram account
- Telegram API credentials (API_ID and API_HASH)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/thertxnetwork/ne.git
cd ne
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Get your Telegram API credentials:
   - Go to https://my.telegram.org/apps
   - Log in with your phone number
   - Create a new application
   - Copy your `API_ID` and `API_HASH`

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your credentials
```

## Usage

### Basic Usage

Run the script:
```bash
python telegram_webapp.py
```

The script will:
1. Prompt for your Telegram credentials (if not in .env)
2. Authenticate with Telegram (code will be sent to your account)
3. Ask for the bot username
4. Generate initData for the web app
5. Fetch and save the homepage

### Environment Variables

You can set these in `.env` file or provide them when prompted:

- `API_ID`: Your Telegram API ID (integer)
- `API_HASH`: Your Telegram API Hash (string)
- `PHONE`: Your phone number with country code (e.g., +1234567890)

### Example Output

The script provides a beautiful, colorful terminal experience:

```bash
$ python telegram_webapp.py

╔══════════════════════════════════════════════════════════╗
║  🚀 TELEGRAM WEB APP LAUNCHER WITH INITDATA 🚀  ║
╚══════════════════════════════════════════════════════════╝

╭─────────────── Features ───────────────╮
│  ✨ Open Telegram web apps programmatically  │
│  🔑 Generate initData for web app authentication  │
│  📥 Fetch homepage content from Telegram bots  │
│  💾 Save initData and homepage to files  │
╰────────────────────────────────────────╯

📋 Configuration

✓ API ID loaded from environment
✓ API Hash loaded from environment
✓ Phone loaded from environment

╭─ Connecting to Telegram... ─╮
│ Connecting to Telegram...   │
╰──────────────────────────────╯

✅ Already authenticated!

Enter bot username (without @): mybot

╭───────────── Bot & User Information ─────────────╮
│ Property            │ Value                      │
├─────────────────────┼────────────────────────────┤
│ 🤖 Bot ID          │ 123456789                  │
│ 🏷️  Bot Username   │ @mybot                     │
│ 📝 Bot Name        │ My Bot                     │
│                     │                            │
│ 👤 Your User ID    │ 987654321                  │
│ 🏷️  Your Username  │ @myusername                │
│ 📝 Your Name       │ John Doe                   │
╰───────────────────────────────────────────────────╯

╭────────────── ✅ InitData Generated Successfully! ──────────────╮
│ Property      │ Value                                           │
├───────────────┼─────────────────────────────────────────────────┤
│ 🌐 URL        │ https://example.com/app?tgWebAppVersion=6.0...│
│ 🆔 Query ID   │ AAHdF6IQAAAAANwXohAAGOMa                       │
│ 🔑 InitData   │ query_id=AAHdF6IQAAAAANwXohAAGOMa&user=...    │
│ 💾 Saved to   │ initdata.txt                                   │
╰─────────────────────────────────────────────────────────────────╯

╭────────────── Fetching Homepage... ──────────────╮
│ Fetching homepage...                             │
╰──────────────────────────────────────────────────╯

✅ Successfully fetched homepage (15.43 KB)

╭────────────── ✅ Homepage Saved Successfully! ──────────────╮
│ Label      │ Value                                          │
├────────────┼────────────────────────────────────────────────┤
│ 📄 Filename│ homepage_mybot.html                           │
│ 📊 Size    │ 15.43 KB                                      │
│ 📝 Lines   │ 342                                           │
╰────────────────────────────────────────────────────────────╯

╔══════════════════════════════════════════════════════╗
║  ✨ All operations completed successfully! ✨       ║
╚══════════════════════════════════════════════════════╝

✅ Disconnected from Telegram.
```

## Output Files

The script generates the following files:

- `initdata.txt`: Contains the full initData string for web app authentication
- `homepage_<botname>.html`: The fetched homepage HTML content
- `telegram_session.session`: Telegram session file (keep this secure!)

## Use Cases

1. **Web App Development**: Test your Telegram web apps with real initData
2. **Bot Testing**: Verify bot web app functionality
3. **Data Collection**: Fetch and analyze web app content
4. **Automation**: Integrate with other tools for automated testing

## Security Notes

- ⚠️ Keep your `.env` file and session files secure
- ⚠️ Never commit `.session` files or credentials to version control
- ⚠️ API credentials and session files are in `.gitignore` by default

## API Reference

### TelegramWebAppLauncher Class

```python
launcher = TelegramWebAppLauncher(api_id, api_hash, phone)
```

#### Methods

- `connect()`: Connect and authenticate with Telegram
- `disconnect()`: Disconnect from Telegram
- `generate_init_data(bot_username, start_param="")`: Generate initData for a web app
- `fetch_homepage(bot_username)`: Fetch the homepage content
- `get_bot_info(bot_username)`: Get information about a bot

## Troubleshooting

### "Invalid API_ID or API_HASH"
- Verify your credentials from https://my.telegram.org/apps
- Ensure API_ID is an integer

### "Phone number not registered"
- Make sure you're using the correct phone number format (+countrycode)
- The number must be registered with Telegram

### "Cannot find entity"
- Check that the bot username is correct (without @)
- Ensure the bot exists and is accessible

## Dependencies

- `telethon`: Telegram client library for Python
- `requests`: HTTP library for fetching web content
- `python-dotenv`: Environment variable management
- `rich`: Beautiful terminal formatting and UI components
- `colorama`: Cross-platform colored terminal text

All dependencies are listed in `requirements.txt` and can be installed with:
```bash
pip install -r requirements.txt
```

## License

MIT License - see LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues or questions, please open an issue on GitHub.