#!/usr/bin/env python3
"""
Demo script to showcase the beautiful terminal UI of the Telegram Web App Launcher.
This demo shows what the UI looks like without requiring actual Telegram credentials.
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.align import Align
from rich import box
from rich.syntax import Syntax
import time

console = Console()


def demo_ui():
    """Demonstrate the beautiful terminal UI."""
    
    # Clear screen
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
    
    # Configuration panel
    console.print("[bold yellow]📋 Configuration[/bold yellow]")
    console.print()
    console.print("[green]✓ API ID loaded from environment[/green]")
    console.print("[green]✓ API Hash loaded from environment[/green]")
    console.print("[green]✓ Phone loaded from environment[/green]")
    console.print()
    
    # Connection status
    console.print(Panel("[bold cyan]Connecting to Telegram...[/bold cyan]", border_style="cyan"))
    time.sleep(1)
    console.print("[green]✅ Already authenticated![/green]")
    console.print()
    
    # Bot information table
    table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
    table.add_column("Property", style="cyan", width=20)
    table.add_column("Value", style="green")
    
    table.add_row("🤖 Bot ID", "123456789")
    table.add_row("🏷️  Bot Username", "@example_bot")
    table.add_row("📝 Bot Name", "Example Bot")
    table.add_row("", "")
    table.add_row("👤 Your User ID", "987654321")
    table.add_row("🏷️  Your Username", "@john_doe")
    table.add_row("📝 Your Name", "John Doe")
    
    console.print(Panel(
        table,
        title="[bold cyan]Bot & User Information[/bold cyan]",
        border_style="cyan"
    ))
    console.print()
    
    # InitData generation
    console.print(Panel(
        "[bold cyan]Generating InitData...[/bold cyan]",
        border_style="cyan"
    ))
    time.sleep(1)
    console.print()
    
    # Results table
    results_table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
    results_table.add_column("Property", style="cyan", width=15)
    results_table.add_column("Value", style="green")
    
    results_table.add_row("🌐 URL", "https://example.com/app?tgWebAppVersion=6.0&tgWebAppPlatform=an...")
    results_table.add_row("🆔 Query ID", "AAHdF6IQAAAAANwXohAAGOMa")
    results_table.add_row("🔑 InitData", "query_id=AAHdF6IQAAAAANwXohAAGOMa&user=%7B%22id%22%3A987654321%2C%22...")
    results_table.add_row("💾 Saved to", "initdata.txt")
    
    console.print(Panel(
        results_table,
        title="[bold green]✅ InitData Generated Successfully![/bold green]",
        border_style="green"
    ))
    console.print()
    
    # Homepage fetching
    console.print(Panel(
        "[bold cyan]Fetching Homepage...[/bold cyan]",
        border_style="cyan"
    ))
    time.sleep(1)
    console.print()
    
    # URL info
    url_table = Table(show_header=False, box=box.SIMPLE)
    url_table.add_column("Label", style="cyan")
    url_table.add_column("Value", style="yellow")
    url_table.add_row("🌐 Web App URL", "https://example.com/app?tgWebAppVersion=6.0...")
    url_table.add_row("🔑 InitData", "query_id=AAHdF6IQAAAAANwXohAAGOMa&user=%7B%22id...")
    
    console.print(url_table)
    console.print()
    console.print(f"[green]✅ Successfully fetched homepage (15.43 KB)[/green]")
    console.print()
    
    # Summary table
    summary_table = Table(show_header=False, box=box.SIMPLE)
    summary_table.add_column("Label", style="cyan")
    summary_table.add_column("Value", style="green")
    summary_table.add_row("📄 Filename", "homepage_example_bot.html")
    summary_table.add_row("📊 Size", "15.43 KB")
    summary_table.add_row("📝 Lines", "342")
    
    console.print(Panel(
        summary_table,
        title="[bold green]✅ Homepage Saved Successfully![/bold green]",
        border_style="green"
    ))
    console.print()
    
    # HTML preview
    html_preview = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Telegram Web App</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
</head>
<body>
    <h1>Welcome to Telegram Web App!</h1>
..."""
    
    syntax = Syntax(html_preview, "html", theme="monokai", line_numbers=False)
    console.print(Panel(
        syntax,
        title="[bold yellow]📄 Homepage Preview[/bold yellow]",
        border_style="yellow"
    ))
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
    
    console.print("[green]✅ Disconnected from Telegram.[/green]")
    console.print()
    
    # Info message
    info = Panel(
        "[bold cyan]This is a demo of the UI. To use the actual script, run:[/bold cyan]\n"
        "[yellow]python telegram_webapp.py[/yellow]",
        title="[bold magenta]ℹ️  Info[/bold magenta]",
        border_style="magenta"
    )
    console.print(info)


if __name__ == "__main__":
    console.print("[bold cyan]Starting UI Demo...[/bold cyan]")
    console.print()
    time.sleep(1)
    demo_ui()
    console.print("\n[bold green]Demo completed! 🎉[/bold green]")
