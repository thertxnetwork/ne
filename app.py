#!/usr/bin/env python3
"""
Telegram Web App Launcher with InitData and Authorization

This script allows you to:
1. Connect to Telegram and select a session
2. Generate initData for a bot's web app
3. Authorize with the backend API

Requirements:
- Telegram API credentials (API_ID and API_HASH)
- Phone number for authentication (only for new sessions)
- Bot username

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
            start_param: Optional start parameter (e.g., for ?startapp= URLs)
            
        Returns:
            Dictionary containing initData and related information
        """
        try:
            with console.status("[bold cyan]Generating initData...", spinner="dots"):
                # Get bot entity
                bot = await self.client.get_entity(bot_username)
                me = await self.client.get_me()
                
                # Get full bot info to check for web apps
                full_bot = await self.client.get_entity(bot)
                
                result = None
                web_app_url = None
                
                # Get bot info to find web app URL
                try:
                    bot_info = await self.client(functions.users.GetFullUserRequest(bot))
                    
                    if bot_info.full_user.bot_info and hasattr(bot_info.full_user.bot_info, 'menu_button'):
                        menu_button = bot_info.full_user.bot_info.menu_button
                        if hasattr(menu_button, 'url'):
                            web_app_url = menu_button.url
                            console.print(f"[green]✓ Found web app URL: {web_app_url[:60]}...[/green]")
                except Exception as e:
                    console.print(f"[yellow]⚠️  Could not get bot info: {str(e)[:80]}[/yellow]")
                
                # Method 1: Try RequestWebViewRequest with the actual web app URL
                if web_app_url and not result:
                    try:
                        console.print(f"[cyan]Trying method 1 (with web app URL)...[/cyan]")
                        result = await self.client(functions.messages.RequestWebViewRequest(
                            peer=bot,
                            bot=bot,
                            platform='android',
                            url=web_app_url
                        ))
                        console.print(f"[green]✓ Method 1 succeeded![/green]")
                    except Exception as e:
                        console.print(f"[yellow]⚠️  Method 1 failed: {str(e)[:100]}[/yellow]")
                
                # Method 2: Try RequestAppWebViewRequest (for bots with attached web apps)
                if hasattr(full_bot, 'bot_info_version') and not result:
                    try:
                        console.print(f"[cyan]Trying method 2 (RequestAppWebViewRequest)...[/cyan]")
                        from telethon.tl.types import InputBotAppShortName
                        result = await self.client(functions.messages.RequestAppWebViewRequest(
                            peer=bot,
                            app=InputBotAppShortName(
                                bot_id=bot,
                                short_name="start"  # Common short name
                            ),
                            platform='android',
                            write_allowed=True,
                            start_param=start_param if start_param else ""
                        ))
                        console.print(f"[green]✓ Method 2 succeeded![/green]")
                    except Exception as e:
                        console.print(f"[yellow]⚠️  Method 2 failed: {str(e)[:100]}[/yellow]")
                
                # Method 3: Try with from_bot_menu flag
                if not result:
                    try:
                        console.print(f"[cyan]Trying method 3 (from_bot_menu)...[/cyan]")
                        result = await self.client(functions.messages.RequestWebViewRequest(
                            peer=bot,
                            bot=bot,
                            platform='android',
                            from_bot_menu=True,
                            url=''
                        ))
                        console.print(f"[green]✓ Method 3 succeeded![/green]")
                    except Exception as e:
                        console.print(f"[yellow]⚠️  Method 3 failed: {str(e)[:100]}[/yellow]")
                
                # Method 4: Try without from_bot_menu but with start_param
                if not result:
                    try:
                        console.print(f"[cyan]Trying method 4 (with start_param)...[/cyan]")
                        result = await self.client(functions.messages.RequestWebViewRequest(
                            peer=bot,
                            bot=bot,
                            platform='android',
                            url='',
                            start_param=start_param if start_param else ""
                        ))
                        console.print(f"[green]✓ Method 4 succeeded![/green]")
                    except Exception as e:
                        console.print(f"[yellow]⚠️  Method 4 failed: {str(e)[:100]}[/yellow]")
            
            if not result:
                console.print(f"[red]❌ Could not generate initData for this bot[/red]")
                return None
            
            # Parse the URL to extract query parameters
            parsed_url = urlparse(result.url)
            
            # Extract tgWebAppData (initData) from fragment or query
            init_data = None
            
            # Try fragment first (format: #tgWebAppData=...)
            if parsed_url.fragment:
                fragment_params = parse_qs(parsed_url.fragment)
                if 'tgWebAppData' in fragment_params:
                    init_data = fragment_params['tgWebAppData'][0]
            
            # Try query parameters if not in fragment
            if not init_data:
                query_params = parse_qs(parsed_url.query)
                if 'tgWebAppData' in query_params:
                    init_data = query_params['tgWebAppData'][0]
            
            # If still no initData, try to extract from the full URL
            if not init_data and 'tgWebAppData=' in result.url:
                # Extract everything after tgWebAppData=
                try:
                    init_data_start = result.url.find('tgWebAppData=') + len('tgWebAppData=')
                    init_data_part = result.url[init_data_start:]
                    # Stop at & or # if present
                    if '&' in init_data_part:
                        init_data_part = init_data_part.split('&')[0]
                    if '#' in init_data_part:
                        init_data_part = init_data_part.split('#')[0]
                    # URL decode
                    from urllib.parse import unquote
                    init_data = unquote(init_data_part)
                except Exception:
                    pass
            
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
    
    async def authorize_backend(self, init_data: str, auth_url: str = "https://numbernewone.com/auth/telegram/authorize") -> Optional[Dict]:
        """
        Authorize with the backend API using initData.
        
        Args:
            init_data: The initData string
            auth_url: Backend authorization URL
            
        Returns:
            Response from the backend as dictionary
        """
        try:
            console.print(Panel(
                f"[bold cyan]Authorizing with Backend...[/bold cyan]\n[yellow]URL: {auth_url}[/yellow]",
                border_style="cyan"
            ))
            console.print()
            
            # Prepare the payload
            payload = {
                "initData": init_data
            }
            
            # Make POST request
            with console.status("[bold cyan]Sending authorization request...", spinner="dots"):
                response = requests.post(
                    auth_url,
                    json=payload,
                    headers={
                        'Content-Type': 'application/json',
                        'User-Agent': 'Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36'
                    },
                    timeout=30
                )
            
            # Check response
            if response.status_code == 200:
                console.print(f"[green]✅ Authorization successful! (Status: {response.status_code})[/green]")
                
                # Try to parse JSON response
                try:
                    response_data = response.json()
                    
                    # Display response in a nice table
                    response_table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
                    response_table.add_column("Field", style="cyan", width=20)
                    response_table.add_column("Value", style="green")
                    
                    for key, value in response_data.items():
                        # Convert value to string, truncate if too long
                        value_str = str(value)
                        if len(value_str) > 100:
                            value_str = value_str[:97] + "..."
                        response_table.add_row(key, value_str)
                    
                    console.print()
                    console.print(Panel(
                        response_table,
                        title="[bold green]✅ Backend Response[/bold green]",
                        border_style="green"
                    ))
                    console.print()
                    
                    return response_data
                except Exception as e:
                    console.print(f"[yellow]⚠️  Response is not JSON: {response.text[:200]}[/yellow]")
                    return {"response": response.text, "status_code": response.status_code}
            else:
                console.print(f"[red]❌ Authorization failed! (Status: {response.status_code})[/red]")
                console.print(f"[red]Response: {response.text[:500]}[/red]")
                return None
                
        except requests.exceptions.Timeout:
            console.print(f"[red]❌ Request timeout after 30 seconds[/red]")
            return None
        except requests.exceptions.RequestException as e:
            console.print(f"[red]❌ Request error: {e}[/red]")
            return None
        except Exception as e:
            console.print(f"[red]❌ Error during authorization: {e}[/red]")
            return None
    
    async def fetch_accounts(self, bearer_token: str, status: str = "pending", base_url: str = "https://numbernewone.com") -> Optional[Dict]:
        """
        Fetch accounts from the backend API with specific status.
        
        Args:
            bearer_token: Bearer token from authorization response
            status: Account status to filter (pending, accepted, rejected)
            base_url: Base URL for the API
            
        Returns:
            Response from the backend as dictionary containing accounts list
        """
        try:
            console.print(Panel(
                f"[bold cyan]Fetching {status.upper()} Accounts...[/bold cyan]\n[yellow]Status Filter: {status}[/yellow]",
                border_style="cyan"
            ))
            console.print()
            
            # Build the filters and sorts
            filters = [
                {"model": "Account", "field": "status", "op": "eq", "value": status},
                {"model": "Account", "field": "invoice_id", "op": "is", "value": None}
            ]
            sorts = [
                {"model": "Account", "field": "created_at", "direction": "desc"}
            ]
            
            # Build URL with parameters
            params = {
                "size": 24,
                "filters": json.dumps(filters),
                "sorts": json.dumps(sorts)
            }
            
            accounts_url = f"{base_url}/accounts/"
            
            # Make GET request
            with console.status(f"[bold cyan]Fetching {status} accounts...", spinner="dots"):
                response = requests.get(
                    accounts_url,
                    params=params,
                    headers={
                        'Authorization': f'Bearer {bearer_token}',
                        'Accept': 'application/json, text/plain, */*',
                        'User-Agent': 'Mozilla/5.0 (Linux; Android 13; SM-G981B) AppleWebKit/537.36',
                        'Origin': 'https://numbernewone.netlify.app',
                        'Referer': 'https://numbernewone.netlify.app/'
                    },
                    timeout=30
                )
            
            # Check response
            if response.status_code == 200:
                console.print(f"[green]✅ Successfully fetched {status} accounts! (Status: {response.status_code})[/green]")
                
                # Parse JSON response
                try:
                    accounts_data = response.json()
                    
                    # Display summary
                    total_accounts = accounts_data.get('total', 0)
                    items_count = len(accounts_data.get('items', []))
                    
                    summary_table = Table(show_header=False, box=box.SIMPLE)
                    summary_table.add_column("Label", style="cyan")
                    summary_table.add_column("Value", style="green")
                    summary_table.add_row("📊 Total Accounts", str(total_accounts))
                    summary_table.add_row("📄 Items Fetched", str(items_count))
                    summary_table.add_row("📑 Current Page", accounts_data.get('currentPage', 'N/A'))
                    
                    console.print()
                    console.print(Panel(
                        summary_table,
                        title=f"[bold green]✅ {status.upper()} Accounts Summary[/bold green]",
                        border_style="green"
                    ))
                    console.print()
                    
                    # Display accounts in a table
                    if items_count > 0:
                        accounts_table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
                        accounts_table.add_column("#", style="cyan", width=4)
                        accounts_table.add_column("UID", style="yellow", width=12)
                        accounts_table.add_column("Phone", style="green", width=18)
                        accounts_table.add_column("TID", style="blue", width=12)
                        accounts_table.add_column("Status", style="magenta", width=12)
                        accounts_table.add_column("Price", style="cyan", width=8)
                        
                        for idx, account in enumerate(accounts_data.get('items', [])[:10], 1):  # Show first 10
                            uid_short = account.get('uid', '')[:8] + "..."
                            phone = account.get('formattedPhone', account.get('phone', 'N/A'))
                            tid = str(account.get('tid', 'N/A'))
                            acc_status = account.get('status', 'N/A')
                            price = f"${account.get('price', 0)}"
                            
                            accounts_table.add_row(str(idx), uid_short, phone, tid, acc_status, price)
                        
                        if items_count > 10:
                            accounts_table.add_row("...", "...", "...", "...", "...", "...")
                        
                        console.print(Panel(
                            accounts_table,
                            title=f"[bold cyan]📱 {status.upper()} Accounts (showing {min(10, items_count)} of {items_count})[/bold cyan]",
                            border_style="cyan"
                        ))
                        console.print()
                    
                    return accounts_data
                except Exception as e:
                    console.print(f"[yellow]⚠️  Failed to parse response: {e}[/yellow]")
                    console.print(f"[dim]Response: {response.text[:200]}[/dim]")
                    return {"response": response.text, "status_code": response.status_code}
            else:
                console.print(f"[red]❌ Failed to fetch accounts! (Status: {response.status_code})[/red]")
                console.print(f"[red]Response: {response.text[:500]}[/red]")
                return None
                
        except requests.exceptions.Timeout:
            console.print(f"[red]❌ Request timeout after 30 seconds[/red]")
            return None
        except requests.exceptions.RequestException as e:
            console.print(f"[red]❌ Request error: {e}[/red]")
            return None
        except Exception as e:
            console.print(f"[red]❌ Error fetching accounts: {e}[/red]")
            return None
    
    async def fetch_dashboard(self, bearer_token: str, base_url: str = "https://numbernewone.com") -> Optional[Dict]:
        """
        Fetch dashboard statistics from the backend API.
        
        Args:
            bearer_token: Bearer token from authorization response
            base_url: Base URL for the API
            
        Returns:
            Response from the backend as dictionary containing user stats, balance, and account count
        """
        try:
            console.print(Panel(
                "[bold cyan]Fetching Dashboard Statistics...[/bold cyan]",
                border_style="cyan"
            ))
            console.print()
            
            dashboard_url = f"{base_url}/dashboard/"
            
            # Make GET request
            with console.status("[bold cyan]Fetching dashboard data...", spinner="dots"):
                response = requests.get(
                    dashboard_url,
                    headers={
                        'Authorization': f'Bearer {bearer_token}',
                        'Accept': 'application/json, text/plain, */*',
                        'User-Agent': 'Mozilla/5.0 (Linux; Android 13; SM-G981B) AppleWebKit/537.36',
                        'Origin': 'https://numbernewone.netlify.app',
                        'Referer': 'https://numbernewone.netlify.app/'
                    },
                    timeout=30
                )
            
            # Check response
            if response.status_code == 200:
                console.print(f"[green]✅ Successfully fetched dashboard! (Status: {response.status_code})[/green]")
                console.print()
                
                # Parse JSON response
                try:
                    dashboard_data = response.json()
                    
                    # Extract key information
                    user_info = dashboard_data.get('user', {})
                    invoice_info = dashboard_data.get('invoice', {})
                    account_info = dashboard_data.get('account', {})
                    order_info = dashboard_data.get('order', {})
                    
                    # Display User Information
                    user_table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
                    user_table.add_column("Property", style="cyan", width=25)
                    user_table.add_column("Value", style="green")
                    
                    user_table.add_row("👤 Role", user_info.get('role', 'N/A'))
                    user_table.add_row("🔗 Can Referrer", "Yes" if user_info.get('canReferrer') else "No")
                    user_table.add_row("➕ Can Add Account", "Yes" if user_info.get('canAddAccount') else "No")
                    user_table.add_row("📝 Can Register Account", "Yes" if user_info.get('canRegisterAccount') else "No")
                    
                    # Telegram Authentication
                    tg_auth = user_info.get('telegramAuthentication', {})
                    if tg_auth:
                        user_table.add_row("📱 Telegram ID", str(tg_auth.get('telegramId', 'N/A')))
                        user_table.add_row("✓ Verified", "Yes" if tg_auth.get('isVerified') else "No")
                    
                    # Referrer
                    if user_info.get('referrerTelegramId'):
                        user_table.add_row("👥 Referrer ID", str(user_info.get('referrerTelegramId')))
                    
                    # Joined Date
                    if user_info.get('joinedDate'):
                        from datetime import datetime
                        joined_date = datetime.fromtimestamp(user_info.get('joinedDate')).strftime('%Y-%m-%d %H:%M:%S')
                        user_table.add_row("📅 Joined Date", joined_date)
                    
                    console.print(Panel(
                        user_table,
                        title="[bold green]👤 User Information[/bold green]",
                        border_style="green"
                    ))
                    console.print()
                    
                    # Display Balance & Payment Information
                    balance_table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
                    balance_table.add_column("Property", style="cyan", width=25)
                    balance_table.add_column("Value", style="yellow")
                    
                    # Highlight available balance
                    available_balance = invoice_info.get('paymentAvailableF', 'N/A')
                    balance_table.add_row("💰 Available Balance", f"[bold green]{available_balance}[/bold green]")
                    
                    paid_balance = invoice_info.get('paymentPaidF', 'N/A')
                    balance_table.add_row("💵 Total Paid", paid_balance)
                    
                    balance_table.add_row("💱 Currency", invoice_info.get('currency', 'N/A').upper())
                    balance_table.add_row("✅ Payment Available", "Yes" if invoice_info.get('isPaymentAvailable') else "No")
                    balance_table.add_row("🔓 Payment Open", "Yes" if invoice_info.get('isPaymentOpen') else "No")
                    
                    # Payment limits
                    min_limit = invoice_info.get('minPaymentLimit', 'N/A')
                    max_limit = invoice_info.get('maxPaymentLimit', 'N/A')
                    balance_table.add_row("📊 Min Payment Limit", f"${min_limit}")
                    balance_table.add_row("📊 Max Payment Limit", f"${max_limit}")
                    
                    console.print(Panel(
                        balance_table,
                        title="[bold yellow]💰 Balance & Payment Information[/bold yellow]",
                        border_style="yellow"
                    ))
                    console.print()
                    
                    # Display Account & Order Statistics
                    stats_table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
                    stats_table.add_column("Category", style="cyan", width=25)
                    stats_table.add_column("Value", style="green")
                    
                    account_count = account_info.get('count', 0)
                    stats_table.add_row("📱 Total Accounts", f"[bold]{account_count}[/bold]")
                    
                    is_order_open = order_info.get('isOpen', False)
                    stats_table.add_row("📦 Order Status", "[bold green]Open[/bold green]" if is_order_open else "[bold red]Closed[/bold red]")
                    
                    console.print(Panel(
                        stats_table,
                        title="[bold blue]📊 Account & Order Statistics[/bold blue]",
                        border_style="blue"
                    ))
                    console.print()
                    
                    return dashboard_data
                except Exception as e:
                    console.print(f"[yellow]⚠️  Failed to parse response: {e}[/yellow]")
                    console.print(f"[dim]Response: {response.text[:200]}[/dim]")
                    return {"response": response.text, "status_code": response.status_code}
            else:
                console.print(f"[red]❌ Failed to fetch dashboard! (Status: {response.status_code})[/red]")
                console.print(f"[red]Response: {response.text[:500]}[/red]")
                return None
                
        except requests.exceptions.Timeout:
            console.print(f"[red]❌ Request timeout after 30 seconds[/red]")
            return None
        except requests.exceptions.RequestException as e:
            console.print(f"[red]❌ Request error: {e}[/red]")
            return None
        except Exception as e:
            console.print(f"[red]❌ Error fetching dashboard: {e}[/red]")
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
    
    async def submit_account_phone(self, bearer_token: str, phone: str, submit_type: str, base_url: str):
        """
        Submit a phone number to the backend for account registration.
        
        Args:
            bearer_token: Bearer token for authentication
            phone: Phone number to submit (e.g., "40753074864")
            submit_type: Type of submission (e.g., "login")
            base_url: Base URL for the API
            
        Returns:
            Dictionary with response data including sentCodeInfo
        """
        try:
            url = f"{base_url}/telegram/submit-account-phone"
            
            headers = {
                'Authorization': f'Bearer {bearer_token}',
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Linux; Android 13; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Mobile Safari/537.36',
                'Origin': 'https://numbernewone.netlify.app',
                'Referer': 'https://numbernewone.netlify.app/'
            }
            
            payload = {
                "phone": phone,
                "submitType": submit_type
            }
            
            console.print()
            console.print(Panel(
                f"[cyan]Submitting phone:[/cyan] [yellow]{phone}[/yellow]\n[cyan]Submit type:[/cyan] [yellow]{submit_type}[/yellow]",
                title="[bold cyan]📱 Submitting Account Phone[/bold cyan]",
                border_style="cyan"
            ))
            
            with console.status("[bold cyan]Sending phone number...", spinner="dots"):
                response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                console.print("[green]✅ Phone submitted successfully![/green]")
                
                # Display response
                table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
                table.add_column("Field", style="cyan", width=20)
                table.add_column("Value", style="green")
                
                table.add_row("Phone", data.get('phone', 'N/A'))
                
                sent_code_info = data.get('sentCodeInfo', {})
                table.add_row("Code Type", sent_code_info.get('codeType', 'N/A'))
                table.add_row("Next Type", sent_code_info.get('nextType', 'N/A'))
                table.add_row("Timeout", str(sent_code_info.get('timeout', 'N/A')))
                
                console.print()
                console.print(Panel(
                    table,
                    title="[bold green]✅ Phone Submission Response[/bold green]",
                    border_style="green"
                ))
                
                return data
            else:
                console.print(f"[red]❌ Failed to submit phone: HTTP {response.status_code}[/red]")
                console.print(f"[red]Response: {response.text}[/red]")
                return None
                
        except Exception as e:
            console.print(f"[red]❌ Error submitting phone: {e}[/red]")
            return None
    
    async def submit_account_code(self, bearer_token: str, phone: str, code: str, base_url: str):
        """
        Submit verification code for account registration.
        
        Args:
            bearer_token: Bearer token for authentication
            phone: Phone number that received the code
            code: Verification code received
            base_url: Base URL for the API
            
        Returns:
            True if successful, False otherwise
        """
        try:
            url = f"{base_url}/telegram/submit-account-code"
            
            headers = {
                'Authorization': f'Bearer {bearer_token}',
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Linux; Android 13; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Mobile Safari/537.36',
                'Origin': 'https://numbernewone.netlify.app',
                'Referer': 'https://numbernewone.netlify.app/'
            }
            
            payload = {
                "phone": phone,
                "code": code
            }
            
            console.print()
            console.print(Panel(
                f"[cyan]Phone:[/cyan] [yellow]{phone}[/yellow]\n[cyan]Code:[/cyan] [yellow]{code}[/yellow]",
                title="[bold cyan]🔐 Submitting Verification Code[/bold cyan]",
                border_style="cyan"
            ))
            
            with console.status("[bold cyan]Verifying code...", spinner="dots"):
                response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 204:
                console.print("[green]✅ Account submitted successfully! (Status: 204 No Content)[/green]")
                console.print("[green]✓ The account has been added to your dashboard[/green]")
                return True
            elif response.status_code == 200:
                console.print("[green]✅ Account submitted successfully![/green]")
                try:
                    data = response.json()
                    console.print(f"[green]Response: {json.dumps(data, indent=2)}[/green]")
                except:
                    pass
                return True
            else:
                console.print(f"[red]❌ Failed to submit code: HTTP {response.status_code}[/red]")
                console.print(f"[red]Response: {response.text}[/red]")
                return False
                
        except Exception as e:
            console.print(f"[red]❌ Error submitting code: {e}[/red]")
            return False


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


def save_token(token: str, filename: str = '.token'):
    """Save bearer token to file for persistence."""
    try:
        with open(filename, 'w') as f:
            f.write(token)
        console.print(f"[green]✓ Token saved to {filename}[/green]")
        return True
    except Exception as e:
        console.print(f"[red]❌ Failed to save token: {e}[/red]")
        return False


def load_token(filename: str = '.token') -> Optional[str]:
    """Load bearer token from file."""
    try:
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                token = f.read().strip()
            if token:
                console.print(f"[green]✓ Token loaded from {filename}[/green]")
                return token
            else:
                console.print(f"[yellow]⚠️  Token file is empty[/yellow]")
                return None
        else:
            return None
    except Exception as e:
        console.print(f"[red]❌ Failed to load token: {e}[/red]")
        return None


def show_menu():
    """Display interactive menu and return user choice."""
    console.print()
    menu_table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
    menu_table.add_column("Option", style="cyan", width=5)
    menu_table.add_column("Description", style="white")
    
    menu_table.add_row("1", "📊 View Dashboard (Balance & Stats)")
    menu_table.add_row("2", "📱 View Pending Accounts")
    menu_table.add_row("3", "✅ View Accepted Accounts")
    menu_table.add_row("4", "❌ View Rejected Accounts")
    menu_table.add_row("5", "➕ Submit New Account (Phone + Code)")
    menu_table.add_row("6", "🔄 Re-authenticate (Get New Token)")
    menu_table.add_row("7", "🚪 Exit")
    
    console.print(Panel(
        menu_table,
        title="[bold cyan]📋 Main Menu[/bold cyan]",
        border_style="cyan"
    ))
    console.print()
    
    choice = Prompt.ask("[bold cyan]Select an option (1-7)[/bold cyan]", default="1")
    return choice


async def handle_menu_choice(choice: str, launcher, bearer_token: str, base_url: str):
    """Handle menu choice and perform corresponding action."""
    try:
        choice_num = int(choice)
    except ValueError:
        console.print("[red]Invalid input. Please enter a number between 1-7.[/red]")
        return bearer_token, False  # Continue loop
    
    if choice_num == 1:
        # View Dashboard
        console.print()
        dashboard_data = await launcher.fetch_dashboard(bearer_token, base_url)
        if dashboard_data:
            with open('dashboard.json', 'w') as f:
                json.dump(dashboard_data, f, indent=2)
            console.print(f"[green]✓ Dashboard data saved to dashboard.json[/green]")
        console.print()
        return bearer_token, False  # Continue loop
    
    elif choice_num == 2:
        # View Pending Accounts
        console.print()
        accounts_data = await launcher.fetch_accounts(bearer_token, 'pending', base_url)
        if accounts_data:
            with open('accounts_pending.json', 'w') as f:
                json.dump(accounts_data, f, indent=2)
            console.print(f"[green]✓ Pending accounts saved to accounts_pending.json[/green]")
        console.print()
        return bearer_token, False  # Continue loop
    
    elif choice_num == 3:
        # View Accepted Accounts
        console.print()
        accounts_data = await launcher.fetch_accounts(bearer_token, 'accepted', base_url)
        if accounts_data:
            with open('accounts_accepted.json', 'w') as f:
                json.dump(accounts_data, f, indent=2)
            console.print(f"[green]✓ Accepted accounts saved to accounts_accepted.json[/green]")
        console.print()
        return bearer_token, False  # Continue loop
    
    elif choice_num == 4:
        # View Rejected Accounts
        console.print()
        accounts_data = await launcher.fetch_accounts(bearer_token, 'rejected', base_url)
        if accounts_data:
            with open('accounts_rejected.json', 'w') as f:
                json.dump(accounts_data, f, indent=2)
            console.print(f"[green]✓ Rejected accounts saved to accounts_rejected.json[/green]")
        console.print()
        return bearer_token, False  # Continue loop
    
    elif choice_num == 5:
        # Submit New Account
        console.print()
        console.print("[cyan]📱 Account Submission Process (2 Steps)[/cyan]")
        console.print("[cyan]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/cyan]")
        console.print()
        
        console.print("[bold yellow]Step 1: Submit Phone Number[/bold yellow]")
        console.print()
        
        # Get phone number
        phone = Prompt.ask("[bold cyan]Enter phone number (e.g., 40753074864)[/bold cyan]")
        
        # Get submit type
        submit_type = Prompt.ask(
            "[bold cyan]Enter submit type[/bold cyan]",
            default="login",
            choices=["login", "register"]
        )
        
        console.print()
        console.print("[yellow]📤 Sending phone number to server...[/yellow]")
        
        # Submit phone
        phone_response = await launcher.submit_account_phone(bearer_token, phone, submit_type, base_url)
        
        if phone_response:
            console.print()
            console.print("[bold yellow]Step 2: Enter Verification Code[/bold yellow]")
            console.print()
            console.print("[green]✅ OTP has been sent to your Telegram app![/green]")
            console.print("[yellow]⏳ Please check your Telegram app for the verification code[/yellow]")
            console.print()
            
            # Get verification code
            code = Prompt.ask("[bold cyan]Enter the verification code you received[/bold cyan]")
            
            console.print()
            console.print("[yellow]📤 Submitting verification code...[/yellow]")
            
            # Submit code
            success = await launcher.submit_account_code(bearer_token, phone, code, base_url)
            
            if success:
                console.print()
                console.print("[green]🎉 Account successfully added to your dashboard![/green]")
                console.print("[cyan]💡 You can now view it in the Pending/Accepted/Rejected accounts sections[/cyan]")
            else:
                console.print()
                console.print("[red]❌ Failed to submit verification code. Please try again.[/red]")
        else:
            console.print()
            console.print("[red]❌ Failed to submit phone number. Please check your input and try again.[/red]")
        
        console.print()
        return bearer_token, False  # Continue loop
    
    elif choice_num == 6:
        # Re-authenticate
        console.print()
        console.print("[yellow]⚠️  Re-authentication requested[/yellow]")
        console.print("[cyan]You will need to generate new initData and authorize again...[/cyan]")
        console.print()
        return None, True  # Signal to re-authenticate
    
    elif choice_num == 7:
        # Exit
        console.print()
        console.print("[cyan]👋 Thank you for using Telegram Web App Launcher![/cyan]")
        console.print()
        return bearer_token, True  # Exit loop
    
    else:
        console.print("[red]Invalid option. Please select 1-7.[/red]")
        return bearer_token, False  # Continue loop


async def main():
    """Main function with beautiful terminal UI and persistent authentication."""
    
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
    features.add_row("✨ Connect to Telegram with saved sessions")
    features.add_row("🔑 Generate initData for web app authentication")
    features.add_row("🌐 Authorize with backend API")
    features.add_row("📊 Fetch dashboard statistics and account balance")
    features.add_row("📱 Fetch accounts with status filtering")
    features.add_row("💾 Save all data to files")
    
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
    
    # Check for existing token
    console.print("[bold yellow]🔐 Authentication Status[/bold yellow]")
    console.print()
    existing_token = load_token()
    
    if existing_token:
        console.print("[green]✅ Found existing authentication token![/green]")
        console.print("[cyan]You can skip re-authentication and go directly to the menu.[/cyan]")
        console.print()
        
        if Confirm.ask("[bold cyan]Do you want to use the existing token?[/bold cyan]", default=True):
            # Skip authentication, go straight to menu
            console.print()
            console.print("[green]✓ Using existing token...[/green]")
            console.print()
            
            # Get base URL for API calls
            base_url = os.getenv('API_BASE_URL', 'https://numbernewone.com')
            
            # Initialize launcher (minimal, no connection needed for API calls)
            launcher = TelegramWebAppLauncher(api_id, api_hash, "", "temp_session")
            
            # Show menu loop
            bearer_token = existing_token
            while True:
                choice = show_menu()
                bearer_token, should_exit = await handle_menu_choice(choice, launcher, bearer_token, base_url)
                
                if should_exit:
                    if bearer_token is None:
                        # User wants to re-authenticate
                        console.print("[yellow]Proceeding to re-authentication...[/yellow]")
                        console.print()
                        break  # Break out of menu loop to continue with auth
                    else:
                        # User wants to exit
                        return
            # If we reach here, user wants to re-authenticate, continue with normal flow
        else:
            console.print("[yellow]⚠️  Will authenticate with new credentials...[/yellow]")
            console.print()
    else:
        console.print("[yellow]ℹ️  No existing token found. You will need to authenticate.[/yellow]")
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
        
        # Get single bot username from environment or prompt
        bot_username = os.getenv('BOT_USERNAME', '').strip()
        
        if bot_username:
            console.print(f"[green]✓ Bot username loaded from environment: {bot_username}[/green]")
            console.print()
        else:
            # Prompt for bot username
            bot_username = Prompt.ask("[bold cyan]Enter bot username (without @)[/bold cyan]")
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
        
        if web_app_data and web_app_data.get('init_data'):
            # Create results table
            results_table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
            results_table.add_column("Property", style="cyan", width=15)
            results_table.add_column("Value", style="green")
            
            results_table.add_row("🌐 URL", web_app_data['url'][:60] + "..." if len(web_app_data['url']) > 60 else web_app_data['url'])
            results_table.add_row("🆔 Query ID", str(web_app_data.get('query_id', 'N/A')))
            
            init_data = web_app_data['init_data']
            init_data_preview = init_data[:80] + "..." if len(init_data) > 80 else init_data
            results_table.add_row("🔑 InitData", init_data_preview)
            
            # Save to file
            with open('initdata.txt', 'w') as f:
                f.write(init_data)
            results_table.add_row("💾 Saved to", "initdata.txt")
            
            console.print(Panel(
                results_table,
                title="[bold green]✅ InitData Generated Successfully![/bold green]",
                border_style="green"
            ))
            console.print()
            
            # Ask if user wants to authorize with backend
            auth_url = os.getenv('AUTH_URL', 'https://numbernewone.com/auth/telegram/authorize')
            
            if Confirm.ask("[bold cyan]Do you want to authorize with the backend API?[/bold cyan]", default=True):
                console.print()
                auth_response = await launcher.authorize_backend(init_data, auth_url)
                
                if auth_response:
                    # Save response to file
                    with open('auth_response.json', 'w') as f:
                        json.dump(auth_response, f, indent=2)
                    console.print(f"[green]✓ Response saved to auth_response.json[/green]")
                    console.print()
                    
                    # Extract Bearer token from response
                    bearer_token = None
                    if isinstance(auth_response, dict):
                        # Try to find token in common response fields (including camelCase variants)
                        bearer_token = (auth_response.get('token') or 
                                      auth_response.get('access_token') or 
                                      auth_response.get('accessToken') or 
                                      auth_response.get('bearer_token'))
                        
                        # If not found in direct fields, check if there's a nested data object
                        if not bearer_token and 'data' in auth_response:
                            bearer_token = (auth_response['data'].get('token') or 
                                          auth_response['data'].get('access_token') or
                                          auth_response['data'].get('accessToken'))
                    
                    # If we found a bearer token, save it and show menu
                    if bearer_token:
                        console.print(f"[green]✓ Bearer token extracted from response[/green]")
                        console.print()
                        
                        # Save token to file for persistence
                        save_token(bearer_token)
                        console.print()
                        
                        # Get base URL from environment or use default
                        base_url = os.getenv('API_BASE_URL', 'https://numbernewone.com')
                        
                        # Show interactive menu
                        console.print("[bold green]✨ Authentication successful! You can now use the menu.[/bold green]")
                        console.print()
                        
                        # Menu loop
                        while True:
                            choice = show_menu()
                            bearer_token, should_exit = await handle_menu_choice(choice, launcher, bearer_token, base_url)
                            
                            if should_exit:
                                if bearer_token is None:
                                    # User wants to re-authenticate
                                    console.print("[yellow]⚠️  Token cleared. Please restart the script to re-authenticate.[/yellow]")
                                break  # Exit menu loop
                    else:
                        console.print(f"[yellow]⚠️  No bearer token found in authorization response[/yellow]")
                        console.print(f"[yellow]💡 Tip: Save the token manually from auth_response.json and use it with the API[/yellow]")
                        console.print()
        else:
            console.print("[red]❌ Failed to generate initData[/red]")
        
        console.print()
        
        # Final success message
        success_panel = Panel(
            Align.center(
                Text("✨ Operation completed successfully! ✨", style="bold green")
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

