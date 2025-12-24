"""
Example usage of the TelegramWebAppLauncher class.

This example demonstrates how to use the script programmatically
rather than interactively.
"""

import asyncio
import os
from telegram_webapp import TelegramWebAppLauncher


async def example_usage():
    """Example of using TelegramWebAppLauncher programmatically."""
    
    # Set your credentials (better to use environment variables)
    API_ID = int(os.getenv('API_ID', '12345'))  # Replace with your API_ID
    API_HASH = os.getenv('API_HASH', 'your_api_hash')  # Replace with your API_HASH
    PHONE = os.getenv('PHONE', '+1234567890')  # Replace with your phone
    BOT_USERNAME = 'your_bot'  # Replace with the bot username (without @)
    
    # Initialize the launcher
    launcher = TelegramWebAppLauncher(API_ID, API_HASH, PHONE)
    
    try:
        # Connect to Telegram
        print("Connecting to Telegram...")
        await launcher.connect()
        print("Connected!")
        
        # Get bot information
        print(f"\nGetting information for @{BOT_USERNAME}...")
        await launcher.get_bot_info(BOT_USERNAME)
        
        # Generate initData
        print(f"\nGenerating initData for @{BOT_USERNAME}...")
        web_app_data = await launcher.generate_init_data(BOT_USERNAME)
        
        if web_app_data:
            print("\n✅ InitData generated successfully!")
            print(f"URL: {web_app_data['url']}")
            
            if web_app_data.get('init_data'):
                print(f"InitData length: {len(web_app_data['init_data'])} characters")
                
                # Save initData to file
                with open('initdata_example.txt', 'w') as f:
                    f.write(web_app_data['init_data'])
                print("InitData saved to: initdata_example.txt")
        
        # Fetch homepage
        print(f"\nFetching homepage from @{BOT_USERNAME}...")
        homepage = await launcher.fetch_homepage(BOT_USERNAME)
        
        if homepage:
            print(f"✅ Homepage fetched successfully! ({len(homepage)} bytes)")
            
            # Save to file
            with open(f'homepage_example_{BOT_USERNAME}.html', 'w', encoding='utf-8') as f:
                f.write(homepage)
            print(f"Homepage saved to: homepage_example_{BOT_USERNAME}.html")
        else:
            print("❌ Failed to fetch homepage")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Always disconnect
        await launcher.disconnect()
        print("\nDisconnected from Telegram.")


if __name__ == "__main__":
    # Run the example
    asyncio.run(example_usage())
