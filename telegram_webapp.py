#!/usr/bin/env python3
"""
Telegram Web App Launcher with InitData

This script allows you to:
1. Open a Telegram web app with initdata
2. Fetch the homepage from a Telegram session

Requirements:
- Telegram API credentials (API_ID and API_HASH)
- Phone number for authentication
- Bot username or web app URL

Usage:
    python telegram_webapp.py
"""

import asyncio
import base64
import hashlib
import hmac
import json
import os
import time
from urllib.parse import parse_qs, urlencode, urlparse
from typing import Optional, Dict

from telethon import TelegramClient, functions
from telethon.tl.types import InputBotAppShortName, InputUser
from dotenv import load_dotenv
import requests


# Load environment variables
load_dotenv()


class TelegramWebAppLauncher:
    """Handle Telegram session and web app launching."""
    
    def __init__(self, api_id: int, api_hash: str, phone: str, session_name: str = "telegram_session"):
        """
        Initialize the Telegram client.
        
        Args:
            api_id: Telegram API ID
            api_hash: Telegram API Hash
            phone: Phone number for authentication
            session_name: Session file name
        """
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone = phone
        self.session_name = session_name
        self.client = None
        
    async def connect(self):
        """Connect to Telegram and authenticate."""
        self.client = TelegramClient(self.session_name, self.api_id, self.api_hash)
        await self.client.connect()
        
        if not await self.client.is_user_authorized():
            await self.client.send_code_request(self.phone)
            print(f"Code sent to {self.phone}")
            code = input("Enter the code you received: ")
            await self.client.sign_in(self.phone, code)
            print("Successfully authenticated!")
        else:
            print("Already authenticated!")
            
    async def disconnect(self):
        """Disconnect from Telegram."""
        if self.client:
            await self.client.disconnect()
            
    async def get_web_app_url(self, bot_username: str, app_short_name: str = "app") -> Optional[str]:
        """
        Get the web app URL from a bot.
        
        Args:
            bot_username: Bot username (without @)
            app_short_name: Short name of the web app
            
        Returns:
            Web app URL or None
        """
        try:
            # Get bot entity
            bot = await self.client.get_entity(bot_username)
            
            # Request web app
            result = await self.client(functions.messages.RequestWebViewRequest(
                peer=bot,
                bot=bot,
                platform='android',
                url=''
            ))
            
            return result.url
        except Exception as e:
            print(f"Error getting web app URL: {e}")
            return None
            
    async def generate_init_data(self, bot_username: str, start_param: str = "") -> Optional[Dict]:
        """
        Generate initData for Telegram web app.
        
        Args:
            bot_username: Bot username (without @)
            start_param: Optional start parameter
            
        Returns:
            Dictionary containing initData and related information
        """
        try:
            # Get bot entity
            bot = await self.client.get_entity(bot_username)
            me = await self.client.get_me()
            
            # Request web view to get the URL with initData
            result = await self.client(functions.messages.RequestWebViewRequest(
                peer=bot,
                bot=bot,
                platform='android',
                url='',
                start_param=start_param
            ))
            
            # Parse the URL to extract query parameters
            parsed_url = urlparse(result.url)
            query_params = parse_qs(parsed_url.fragment if parsed_url.fragment else parsed_url.query)
            
            # Extract tgWebAppData (initData)
            init_data = None
            if 'tgWebAppData' in query_params:
                init_data = query_params['tgWebAppData'][0]
            elif parsed_url.fragment:
                # Try to extract from fragment
                fragment_params = parse_qs(parsed_url.fragment)
                if 'tgWebAppData' in fragment_params:
                    init_data = fragment_params['tgWebAppData'][0]
            
            return {
                'url': result.url,
                'init_data': init_data,
                'bot_username': bot_username,
                'user_id': me.id,
                'query_id': result.query_id,
                'full_url': result.url
            }
        except Exception as e:
            print(f"Error generating initData: {e}")
            return None
            
    async def fetch_homepage(self, bot_username: str) -> Optional[str]:
        """
        Fetch the homepage content from a Telegram bot/web app.
        
        Args:
            bot_username: Bot username (without @)
            
        Returns:
            Homepage content as string
        """
        try:
            # Get the web app data
            web_app_data = await self.generate_init_data(bot_username)
            
            if not web_app_data or not web_app_data.get('url'):
                print("Failed to get web app URL")
                return None
                
            url = web_app_data['url']
            init_data = web_app_data.get('init_data', '')
            
            print(f"\nWeb App URL: {url}")
            print(f"InitData: {init_data[:50]}..." if init_data else "InitData: None")
            
            # Fetch the homepage
            headers = {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36',
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                print(f"\nSuccessfully fetched homepage (size: {len(response.text)} bytes)")
                return response.text
            else:
                print(f"Failed to fetch homepage: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error fetching homepage: {e}")
            return None
            
    async def get_bot_info(self, bot_username: str):
        """
        Get information about a bot.
        
        Args:
            bot_username: Bot username (without @)
        """
        try:
            bot = await self.client.get_entity(bot_username)
            me = await self.client.get_me()
            
            print("\n" + "="*50)
            print("Bot Information:")
            print("="*50)
            print(f"Bot ID: {bot.id}")
            print(f"Bot Username: @{bot.username}")
            print(f"Bot Name: {bot.first_name}")
            print(f"\nYour Information:")
            print(f"User ID: {me.id}")
            print(f"Username: @{me.username}" if me.username else "Username: None")
            print(f"Name: {me.first_name} {me.last_name if me.last_name else ''}")
            print("="*50)
            
        except Exception as e:
            print(f"Error getting bot info: {e}")


async def main():
    """Main function to demonstrate the script functionality."""
    print("="*60)
    print("Telegram Web App Launcher with InitData")
    print("="*60)
    
    # Get credentials from environment variables or user input
    api_id = os.getenv('API_ID')
    api_hash = os.getenv('API_HASH')
    phone = os.getenv('PHONE')
    
    if not api_id:
        api_id = input("Enter your Telegram API ID: ")
    if not api_hash:
        api_hash = input("Enter your Telegram API Hash: ")
    if not phone:
        phone = input("Enter your phone number (with country code, e.g., +1234567890): ")
        
    try:
        api_id = int(api_id)
    except ValueError:
        print("Error: API_ID must be a number")
        return
        
    # Initialize launcher
    launcher = TelegramWebAppLauncher(api_id, api_hash, phone)
    
    try:
        # Connect and authenticate
        print("\nConnecting to Telegram...")
        await launcher.connect()
        
        # Get bot username
        bot_username = input("\nEnter bot username (without @): ")
        
        # Show bot information
        await launcher.get_bot_info(bot_username)
        
        # Generate initData
        print("\n" + "="*60)
        print("Generating InitData...")
        print("="*60)
        web_app_data = await launcher.generate_init_data(bot_username)
        
        if web_app_data:
            print("\nWeb App Data Generated Successfully!")
            print("-"*60)
            print(f"URL: {web_app_data['url']}")
            print(f"Query ID: {web_app_data.get('query_id', 'N/A')}")
            
            if web_app_data.get('init_data'):
                print(f"\nInitData (first 100 chars):")
                print(web_app_data['init_data'][:100] + "...")
                
                # Save to file
                with open('initdata.txt', 'w') as f:
                    f.write(web_app_data['init_data'])
                print("\nFull initData saved to: initdata.txt")
            else:
                print("\nNote: No initData in query parameters (might be embedded in URL)")
                
        # Fetch homepage
        print("\n" + "="*60)
        print("Fetching Homepage...")
        print("="*60)
        homepage = await launcher.fetch_homepage(bot_username)
        
        if homepage:
            # Save homepage to file
            filename = f"homepage_{bot_username}.html"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(homepage)
            print(f"\nHomepage saved to: {filename}")
            
            # Show preview
            preview = homepage[:500]
            print(f"\nHomepage Preview (first 500 chars):")
            print("-"*60)
            print(preview)
            if len(homepage) > 500:
                print("...")
                
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Disconnect
        await launcher.disconnect()
        print("\nDisconnected from Telegram.")


if __name__ == "__main__":
    asyncio.run(main())
