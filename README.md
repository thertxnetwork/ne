# Telegram Web App Launcher

A Python script to open Telegram web apps with initdata and fetch homepage content from Telegram sessions.

## Features

- 🚀 Open Telegram web apps programmatically
- 🔑 Generate initData for web app authentication
- 📥 Fetch homepage content from Telegram bots/web apps
- 💾 Save initData and homepage to files
- 🔐 Secure session management with Telethon

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

### Example

```bash
$ python telegram_webapp.py

============================================================
Telegram Web App Launcher with InitData
============================================================

Connecting to Telegram...
Already authenticated!

Enter bot username (without @): mybot

==================================================
Bot Information:
==================================================
Bot ID: 123456789
Bot Username: @mybot
Bot Name: My Bot

Your Information:
User ID: 987654321
Username: @myusername
Name: John Doe
==================================================

============================================================
Generating InitData...
============================================================

Web App Data Generated Successfully!
------------------------------------------------------------
URL: https://example.com/app?...
Query ID: AAHdF6IQAAAAANwXohAAGOMa

InitData (first 100 chars):
query_id=AAHdF6IQAAAAANwXohAAGOMa&user=%7B%22id%22%3A987654321%2C%22first_name%22%3A%22John%22...

Full initData saved to: initdata.txt

============================================================
Fetching Homepage...
============================================================

Web App URL: https://example.com/app?...
InitData: query_id=AAHdF6IQAAAAANwXohAAGOMa&user=%7B%22id...

Successfully fetched homepage (size: 15234 bytes)

Homepage saved to: homepage_mybot.html
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

- `telethon`: Telegram client library
- `requests`: HTTP library
- `python-dotenv`: Environment variable management

## License

MIT License - see LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues or questions, please open an issue on GitHub.