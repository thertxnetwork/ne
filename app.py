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
    python app.py
"""

import asyncio
import base64
import hashlib
import hmac
import json
import os
import time
import glob
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse
from typing import Optional, Dict, List

from telethon import TelegramClient, functions
from telethon.tl.types import InputBotAppShortName, InputUser
from dotenv import load_dotenv
import requests

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.prompt import Prompt, Confirm
from rich.text import Text
from rich.layout import Layout
from rich.align import Align
from rich import box
from rich.syntax import Syntax
from rich.markdown import Markdown
import colorama
from colorama import Fore, Back, Style

# Load environment variables
load_dotenv()

# Initialize Rich console and colorama
console = Console()
colorama.init(autoreset=True)


class TelegramWebAppLauncher:
    """Handle Telegram session and web app launching with beautiful terminal UI."""
    
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
        
    def print_header(self):
        """Print a beautiful header."""
        header_text = Text()
        header_text.append("🚀 ", style="bold yellow")
        header_text.append("Telegram Web App Launcher", style="bold cyan")
        header_text.append(" 🚀", style="bold yellow")
        
        console.print()
        console.print(Panel(
            Align.center(header_text),
            border_style="bright_blue",
            box=box.DOUBLE
        ))
        console.print()
        
    async def connect(self):
        """Connect to Telegram and authenticate with beautiful UI."""
        with console.status("[bold cyan]Connecting to Telegram...", spinner="dots"):
            self.client = TelegramClient(self.session_name, self.api_id, self.api_hash)
            await self.client.connect()
        
        if not await self.client.is_user_authorized():
            # Need to authenticate
            if not self.phone:
                console.print("[red]❌ Session not authorized and no phone number provided[/red]")
                return
            
            # Send code request
            await self.client.send_code_request(self.phone)
            console.print(f"[yellow]📱 Code sent to {self.phone}[/yellow]")
            code = Prompt.ask("[bold cyan]Enter the verification code[/bold cyan]")
            
            with console.status("[bold cyan]Signing in...", spinner="dots"):
                try:
                    await self.client.sign_in(self.phone, code)
                    console.print("[green]✅ Successfully authenticated![/green]")
                except Exception as e:
                    # Might need password for 2FA
                    if "password" in str(e).lower():
                        password = Prompt.ask("[bold cyan]Enter your 2FA password[/bold cyan]", password=True)
                        await self.client.sign_in(password=password)
                        console.print("[green]✅ Successfully authenticated with 2FA![/green]")
                    else:
                        raise
        else:
            console.print("[green]✅ Already authenticated![/green]")
            
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
        Generate initData for Telegram web app with beautiful progress display.
        
        Args:
            bot_username: Bot username (without @)
            start_param: Optional start parameter
            
        Returns:
            Dictionary containing initData and related information
        """
        try:
            with console.status("[bold cyan]Generating initData...", spinner="dots"):
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
            console.print(f"[red]❌ Error generating initData: {e}[/red]")
            return None
            
    async def fetch_homepage(self, bot_username: str) -> Optional[str]:
        """
        Fetch the homepage content from a Telegram bot/web app with beautiful progress.
        
        Args:
            bot_username: Bot username (without @)
            
        Returns:
            Homepage content as string
        """
        try:
            # Get the web app data
            web_app_data = await self.generate_init_data(bot_username)
            
            if not web_app_data or not web_app_data.get('url'):
                console.print("[red]❌ Failed to get web app URL[/red]")
                return None
                
            url = web_app_data['url']
            init_data = web_app_data.get('init_data', '')
            
            # Display URL info
            url_table = Table(show_header=False, box=box.SIMPLE)
            url_table.add_column("Label", style="cyan")
            url_table.add_column("Value", style="yellow")
            url_table.add_row("🌐 Web App URL", url[:80] + "..." if len(url) > 80 else url)
            if init_data:
                url_table.add_row("🔑 InitData", init_data[:50] + "..." if len(init_data) > 50 else init_data)
            
            console.print(url_table)
            console.print()
            
            # Fetch the homepage
            headers = {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36',
            }
            
            with console.status("[bold cyan]Fetching homepage...", spinner="dots"):
                response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                size_kb = len(response.text) / 1024
                console.print(f"[green]✅ Successfully fetched homepage ({size_kb:.2f} KB)[/green]")
                return response.text
            else:
                console.print(f"[red]❌ Failed to fetch homepage: HTTP {response.status_code}[/red]")
                return None
                
        except Exception as e:
            console.print(f"[red]❌ Error fetching homepage: {e}[/red]")
            return None
            
    async def get_bot_info(self, bot_username: str):
        """
        Get information about a bot with beautiful table display.
        
        Args:
            bot_username: Bot username (without @)
        """
        try:
            with console.status(f"[bold cyan]Fetching bot information for @{bot_username}...", spinner="dots"):
                bot = await self.client.get_entity(bot_username)
                me = await self.client.get_me()
            
            # Create a beautiful table
            table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
            table.add_column("Property", style="cyan", width=20)
            table.add_column("Value", style="green")
            
            # Bot information
            table.add_row("🤖 Bot ID", str(bot.id))
            table.add_row("🏷️  Bot Username", f"@{bot.username}")
            table.add_row("📝 Bot Name", bot.first_name)
            table.add_row("", "")  # Separator
            
            # User information
            table.add_row("👤 Your User ID", str(me.id))
            table.add_row("🏷️  Your Username", f"@{me.username}" if me.username else "None")
            table.add_row("📝 Your Name", f"{me.first_name} {me.last_name if me.last_name else ''}")
            
            console.print()
            console.print(Panel(
                table,
                title="[bold cyan]Bot & User Information[/bold cyan]",
                border_style="cyan"
            ))
            console.print()
            
        except Exception as e:
            console.print(f"[red]❌ Error getting bot info: {e}[/red]")


def find_session_files() -> List[str]:
    """Find all .session files in the current directory."""
    session_files = glob.glob("*.session")
    return [os.path.splitext(f)[0] for f in session_files]


async def get_session_info(session_name: str, api_id: int, api_hash: str) -> Optional[Dict]:
    """
    Get information about a session file.
    
    Args:
        session_name: Name of the session file (without .session extension)
        api_id: Telegram API ID
        api_hash: Telegram API Hash
        
    Returns:
        Dictionary with session info or None if session is invalid
    """
    try:
        client = TelegramClient(session_name, api_id, api_hash)
        await client.connect()
        
        if await client.is_user_authorized():
            me = await client.get_me()
            await client.disconnect()
            return {
                'session_name': session_name,
                'user_id': me.id,
                'phone': me.phone,
                'username': me.username,
                'first_name': me.first_name,
                'last_name': me.last_name
            }
        else:
            await client.disconnect()
            return None
    except Exception as e:
        return None


async def display_sessions(api_id: int, api_hash: str) -> Optional[str]:
    """
    Display available sessions and let user select one.
    
    Args:
        api_id: Telegram API ID
        api_hash: Telegram API Hash
        
    Returns:
        Selected session name or None to create new session
    """
    session_files = find_session_files()
    
    if not session_files:
        console.print("[yellow]📂 No existing sessions found.[/yellow]")
        console.print()
        return None
    
    console.print("[bold cyan]📱 Available Telegram Sessions[/bold cyan]")
    console.print()
    
    # Create table for sessions
    table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
    table.add_column("#", style="cyan", width=5)
    table.add_column("Session Name", style="green")
    table.add_column("Phone", style="yellow")
    table.add_column("Username", style="blue")
    table.add_column("Name", style="white")
    
    valid_sessions = []
    
    with console.status("[bold cyan]Loading sessions...", spinner="dots"):
        for idx, session_name in enumerate(session_files, 1):
            info = await get_session_info(session_name, api_id, api_hash)
            if info:
                valid_sessions.append(info)
                username_display = f"@{info['username']}" if info['username'] else "None"
                name_display = f"{info['first_name']} {info['last_name'] if info['last_name'] else ''}".strip()
                table.add_row(
                    str(idx),
                    session_name,
                    info['phone'] or "N/A",
                    username_display,
                    name_display
                )
    
    if not valid_sessions:
        console.print("[yellow]📂 No valid sessions found.[/yellow]")
        console.print()
        return None
    
    console.print(table)
    console.print()
    
    # Add option to create new session
    console.print(f"[cyan]{len(valid_sessions) + 1}. [bold]Create New Session[/bold][/cyan]")
    console.print()
    
    # Get user choice
    while True:
        choice = Prompt.ask(
            f"[bold cyan]Select session (1-{len(valid_sessions) + 1})[/bold cyan]",
            default="1"
        )
        
        try:
            choice_num = int(choice)
            if 1 <= choice_num <= len(valid_sessions):
                selected = valid_sessions[choice_num - 1]
                console.print(f"[green]✅ Selected: {selected['session_name']} ({selected['phone']})[/green]")
                console.print()
                return selected['session_name']
            elif choice_num == len(valid_sessions) + 1:
                console.print("[green]✅ Creating new session...[/green]")
                console.print()
                return None
            else:
                console.print(f"[red]Invalid choice. Please enter 1-{len(valid_sessions) + 1}[/red]")
        except ValueError:
            console.print("[red]Invalid input. Please enter a number.[/red]")


async def main():
    """Main function with beautiful terminal UI."""
    
    # Clear screen and show header
    console.clear()
    
    # Beautiful ASCII art header
    header = Text()
    header.append("╔══════════════════════════════════════════════════════════╗\n", style="bold bright_blue")
    header.append("║  ", style="bold bright_blue")
    header.append("🚀 TELEGRAM WEB APP LAUNCHER WITH INITDATA 🚀", style="bold cyan")
    header.append("  ║\n", style="bold bright_blue")
    header.append("╚══════════════════════════════════════════════════════════╝", style="bold bright_blue")
    
    console.print(header)
    console.print()
    
    # Show features
    features = Table(show_header=False, box=None, padding=(0, 2))
    features.add_column(style="cyan")
    features.add_row("✨ Open Telegram web apps programmatically")
    features.add_row("🔑 Generate initData for web app authentication")
    features.add_row("📥 Fetch homepage content from Telegram bots")
    features.add_row("💾 Save initData and homepage to files")
    
    console.print(Panel(features, title="[bold magenta]Features[/bold magenta]", border_style="magenta"))
    console.print()
    
    # Get credentials
    console.print("[bold yellow]📋 Configuration[/bold yellow]")
    console.print()
    
    api_id = os.getenv('API_ID')
    api_hash = os.getenv('API_HASH')
    
    if not api_id:
        api_id = Prompt.ask("[cyan]Enter your Telegram API ID[/cyan]")
    else:
        console.print(f"[green]✓ API ID loaded from environment[/green]")
        
    if not api_hash:
        api_hash = Prompt.ask("[cyan]Enter your Telegram API Hash[/cyan]")
    else:
        console.print(f"[green]✓ API Hash loaded from environment[/green]")
        
    try:
        api_id = int(api_id)
    except ValueError:
        console.print("[red]❌ Error: API_ID must be a number[/red]")
        return
    
    console.print()
    
    # Display and select session
    selected_session = await display_sessions(api_id, api_hash)
    
    # Determine session name and phone
    if selected_session:
        # Using existing session
        session_name = selected_session
        phone = None  # Not needed for existing session
    else:
        # Creating new session - need phone number
        phone = os.getenv('PHONE')
        if not phone:
            phone = Prompt.ask("[cyan]Enter your phone number (with country code, e.g., +1234567890)[/cyan]")
        else:
            console.print(f"[green]✓ Phone loaded from environment[/green]")
        
        # Generate session name from phone or timestamp
        session_name = Prompt.ask(
            "[cyan]Enter session name[/cyan]",
            default=f"session_{phone.replace('+', '').replace(' ', '')}"
        )
        console.print()
    
    # Initialize launcher
    launcher = TelegramWebAppLauncher(api_id, api_hash, phone or "", session_name)
    
    try:
        # Connect and authenticate
        console.print(Panel("[bold cyan]Connecting to Telegram...[/bold cyan]", border_style="cyan"))
        await launcher.connect()
        console.print()
        
        # Get bot username(s) from environment or prompt
        bot_usernames_env = os.getenv('BOT_USERNAME', '').strip()
        
        if bot_usernames_env:
            # Parse bot usernames from environment (comma-separated)
            bot_usernames = [bot.strip() for bot in bot_usernames_env.split(',') if bot.strip()]
            console.print(f"[green]✓ Bot username(s) loaded from environment: {', '.join(bot_usernames)}[/green]")
            console.print()
        else:
            # Prompt for bot username
            bot_username_input = Prompt.ask("[bold cyan]Enter bot username(s) (comma-separated for multiple, without @)[/bold cyan]")
            bot_usernames = [bot.strip() for bot in bot_username_input.split(',') if bot.strip()]
            console.print()
        
        # Process each bot
        for idx, bot_username in enumerate(bot_usernames, 1):
            if len(bot_usernames) > 1:
                console.print(f"[bold yellow]═══ Processing Bot {idx}/{len(bot_usernames)}: @{bot_username} ═══[/bold yellow]")
                console.print()
            
            # Show bot information
            await launcher.get_bot_info(bot_username)
            
            # Generate initData
            console.print(Panel(
                "[bold cyan]Generating InitData...[/bold cyan]",
                border_style="cyan"
            ))
            console.print()
            
            web_app_data = await launcher.generate_init_data(bot_username)
            
            if web_app_data:
                # Create results table
                results_table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
                results_table.add_column("Property", style="cyan", width=15)
                results_table.add_column("Value", style="green")
                
                results_table.add_row("🌐 URL", web_app_data['url'][:60] + "..." if len(web_app_data['url']) > 60 else web_app_data['url'])
                results_table.add_row("🆔 Query ID", str(web_app_data.get('query_id', 'N/A')))
                
                if web_app_data.get('init_data'):
                    init_data_preview = web_app_data['init_data'][:80] + "..."
                    results_table.add_row("🔑 InitData", init_data_preview)
                    
                    # Save to file with bot username
                    initdata_filename = f"initdata_{bot_username}.txt" if len(bot_usernames) > 1 else "initdata.txt"
                    with open(initdata_filename, 'w') as f:
                        f.write(web_app_data['init_data'])
                    results_table.add_row("💾 Saved to", initdata_filename)
                else:
                    results_table.add_row("⚠️  Note", "No initData in query parameters")
                
                console.print(Panel(
                    results_table,
                    title="[bold green]✅ InitData Generated Successfully![/bold green]",
                    border_style="green"
                ))
                console.print()
                    
            # Fetch homepage
            console.print(Panel(
                "[bold cyan]Fetching Homepage...[/bold cyan]",
                border_style="cyan"
            ))
            console.print()
            
            homepage = await launcher.fetch_homepage(bot_username)
            
            if homepage:
                # Save homepage to file
                filename = f"homepage_{bot_username}.html"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(homepage)
                
                # Create summary table
                summary_table = Table(show_header=False, box=box.SIMPLE)
                summary_table.add_column("Label", style="cyan")
                summary_table.add_column("Value", style="green")
                summary_table.add_row("📄 Filename", filename)
                summary_table.add_row("📊 Size", f"{len(homepage) / 1024:.2f} KB")
                summary_table.add_row("📝 Lines", str(homepage.count('\n')))
                
                console.print(Panel(
                    summary_table,
                    title="[bold green]✅ Homepage Saved Successfully![/bold green]",
                    border_style="green"
                ))
                console.print()
                
                # Show preview
                preview_lines = homepage[:400]
                if len(homepage) > 400:
                    preview_lines += "\n..."
                
                syntax = Syntax(preview_lines, "html", theme="monokai", line_numbers=False)
                console.print(Panel(
                    syntax,
                    title="[bold yellow]📄 Homepage Preview[/bold yellow]",
                    border_style="yellow"
                ))
            
            console.print()
            
            # Add separator between bots
            if idx < len(bot_usernames):
                console.print()
        
        console.print()
        
        # Final success message
        success_panel = Panel(
            Align.center(
                Text("✨ All operations completed successfully! ✨", style="bold green")
            ),
            border_style="bright_green",
            box=box.DOUBLE
        )
        console.print(success_panel)
        console.print()
                
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Operation cancelled by user.[/yellow]")
    except Exception as e:
        console.print(f"\n[red]❌ Error: {e}[/red]")
        import traceback
        console.print("[dim]" + traceback.format_exc() + "[/dim]")
    finally:
        # Disconnect
        with console.status("[bold cyan]Disconnecting...", spinner="dots"):
            await launcher.disconnect()
        console.print("[green]✅ Disconnected from Telegram.[/green]")
        console.print()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]👋 Goodbye![/yellow]")

