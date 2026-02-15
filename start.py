# start.py
"""
ABS Pipeline Control Center - Terminal User Interface
Run all pipeline operations from a single interactive menu
"""

import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm
    from rich.table import Table
    from rich.live import Live
    from rich.layout import Layout
    from rich import box
    from rich.text import Text
except ImportError:
    print("\n❌ Missing required package: rich")
    print("\nInstall with:")
    print("  pip install rich --break-system-packages")
    print("\nOr if using venv:")
    print("  venv\\Scripts\\activate")
    print("  pip install rich")
    sys.exit(1)

# Try to import configuration
try:
    from config import ABS_DATASETS, HISTORY_YEARS, OUTPUT_DIRECTORY
    CONFIG_LOADED = True
except ImportError:
    CONFIG_LOADED = False
    OUTPUT_DIRECTORY = "abs_data_output"
    HISTORY_YEARS = 10

console = Console()

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def clear_screen():
    """Clear terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def count_files_in_dir(directory):
    """Count CSV or PNG files in a directory"""
    if not os.path.exists(directory):
        return 0
    return len([f for f in os.listdir(directory) if f.endswith(('.csv', '.png'))])

def get_latest_file_date(directory, extension='.csv'):
    """Get the modification date of the most recently modified file"""
    if not os.path.exists(directory):
        return None
    
    files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith(extension)]
    if not files:
        return None
    
    latest_file = max(files, key=os.path.getmtime)
    mod_time = os.path.getmtime(latest_file)
    return datetime.fromtimestamp(mod_time)

def run_script(script_name, description, args=None):
    """
    Execute a Python script and capture its output
    Returns: (success: bool, output: str)
    """
    console.print(f"\n[bold cyan]▶ Running: {description}[/bold cyan]")
    console.print(f"[dim]Script: {script_name}[/dim]\n")
    
    cmd = [sys.executable, script_name]
    if args:
        cmd.extend(args)
    
    try:
        # Run script and capture output
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        
        # Display output
        if result.stdout:
            console.print(result.stdout)
        
        if result.stderr and result.returncode != 0:
            console.print(f"[red]{result.stderr}[/red]")
        
        if result.returncode == 0:
            console.print(f"\n[green]✓ {description} completed successfully[/green]")
            return True, result.stdout
        else:
            console.print(f"\n[red]✗ {description} failed with exit code {result.returncode}[/red]")
            return False, result.stderr
            
    except FileNotFoundError:
        console.print(f"[red]✗ Error: {script_name} not found[/red]")
        return False, f"Script {script_name} not found"
    except Exception as e:
        console.print(f"[red]✗ Error running {script_name}: {str(e)}[/red]")
        return False, str(e)

# =============================================================================
# MENU ACTIONS
# =============================================================================

def show_status():
    """Display current pipeline status"""
    clear_screen()
    
    # Create status panel
    status_table = Table(show_header=True, header_style="bold cyan", box=box.ROUNDED)
    status_table.add_column("Component", style="cyan", width=30)
    status_table.add_column("Status", width=50)
    
    # Check configuration
    if CONFIG_LOADED:
        dataset_count = len(ABS_DATASETS)
        status_table.add_row(
            "Configuration",
            f"[green]✓[/green] Loaded - {dataset_count} datasets, {HISTORY_YEARS} years history"
        )
    else:
        status_table.add_row(
            "Configuration",
            "[red]✗[/red] Not found - config.py missing"
        )
    
    # Check data files
    csv_count = count_files_in_dir(OUTPUT_DIRECTORY)
    last_data_update = get_latest_file_date(OUTPUT_DIRECTORY, '.csv')
    
    if csv_count > 0:
        date_str = last_data_update.strftime('%Y-%m-%d %H:%M') if last_data_update else "Unknown"
        status_table.add_row(
            "Data Files",
            f"[green]✓[/green] {csv_count} CSV files | Last update: {date_str}"
        )
    else:
        status_table.add_row(
            "Data Files",
            "[yellow]⚠[/yellow] No data files - run download (Option 1)"
        )
    
    # Check charts
    chart_count = count_files_in_dir("abs_charts_output")
    last_chart_update = get_latest_file_date("abs_charts_output", '.png')
    
    if chart_count > 0:
        date_str = last_chart_update.strftime('%Y-%m-%d %H:%M') if last_chart_update else "Unknown"
        status_table.add_row(
            "Static Charts",
            f"[green]✓[/green] {chart_count} PNG files | Last update: {date_str}"
        )
    else:
        status_table.add_row(
            "Static Charts",
            "[yellow]⚠[/yellow] No charts - run plotting (Option 2)"
        )
    
    # Check scripts
    scripts_present = []
    scripts_missing = []
    
    for script in ["config.py", "download.py", 
                   "generate_charts.py", "dashboard.py"]:
        if os.path.exists(script):
            scripts_present.append(script)
        else:
            scripts_missing.append(script)
    
    scripts_status = f"[green]✓[/green] {len(scripts_present)}/4 scripts available"
    if scripts_missing:
        scripts_status += f" ([yellow]{', '.join(scripts_missing)} missing[/yellow])"
    
    status_table.add_row("Pipeline Scripts", scripts_status)
    
    # Check dashboard dependencies
    try:
        import streamlit
        import plotly
        dashboard_status = "[green]✓[/green] Streamlit and Plotly installed"
    except ImportError:
        dashboard_status = "[yellow]⚠[/yellow] Dashboard dependencies missing (streamlit/plotly)"
    
    status_table.add_row("Dashboard", dashboard_status)
    
    console.print(Panel(status_table, title="[bold]Pipeline Status[/bold]", border_style="cyan"))

def download_data():
    """Run the data download script"""
    clear_screen()
    
    if not os.path.exists("download.py"):
        console.print("[red]✗ download.py not found[/red]")
        return
    
    # Ask if user wants to filter
    console.print("\n[bold]Download Options:[/bold]")
    console.print("1. Download all datasets")
    console.print("2. Download only monthly datasets")
    console.print("3. Download only quarterly datasets")
    
    choice = Prompt.ask("\nSelect option", choices=["1", "2", "3"], default="1")
    
    args = []
    if choice == "2":
        args = ["--freq", "monthly"]
    elif choice == "3":
        args = ["--freq", "quarterly"]
    
    # Run download
    success, output = run_script(
        "download.py",
        "Data Download",
        args
    )
    
    if success:
        # Show summary
        csv_count = count_files_in_dir(OUTPUT_DIRECTORY)
        console.print(f"\n[bold green]Summary:[/bold green]")
        console.print(f"  • Total CSV files: {csv_count}")
        console.print(f"  • Location: {OUTPUT_DIRECTORY}/")

def generate_charts():
    """Run the chart generation script"""
    clear_screen()
    
    if not os.path.exists("generate_charts.py"):
        console.print("[red]✗ generate_charts.py not found[/red]")
        return
    
    # Check if data exists
    csv_count = count_files_in_dir(OUTPUT_DIRECTORY)
    if csv_count == 0:
        console.print("[yellow]⚠ No data files found. Run download first (Option 1)[/yellow]")
        if not Confirm.ask("\nContinue anyway?", default=False):
            return
    
    # Run plotting
    success, output = run_script(
        "generate_charts.py",
        "Chart Generation"
    )
    
    if success:
        # Show summary
        chart_count = count_files_in_dir("abs_charts_output")
        console.print(f"\n[bold green]Summary:[/bold green]")
        console.print(f"  • Total PNG files: {chart_count}")
        console.print(f"  • Location: abs_charts_output/")

def launch_dashboard():
    """Launch the Streamlit dashboard"""
    clear_screen()
    
    if not os.path.exists("dashboard.py"):
        console.print("[red]✗ dashboard.py not found[/red]")
        return
    
    # Check dependencies
    try:
        import streamlit
        import plotly
    except ImportError:
        console.print("[red]✗ Dashboard dependencies missing[/red]")
        console.print("\nInstall with:")
        console.print("  pip install streamlit plotly --break-system-packages")
        return
    
    # Check if data exists
    csv_count = count_files_in_dir(OUTPUT_DIRECTORY)
    if csv_count == 0:
        console.print("[yellow]⚠ No data files found. Run download first (Option 1)[/yellow]")
        if not Confirm.ask("\nContinue anyway?", default=False):
            return
    
    console.print("\n[bold cyan]Launching dashboard...[/bold cyan]")
    console.print("[dim]Press Ctrl+C in this window to stop the dashboard[/dim]\n")
    
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "dashboard.py"])
    except KeyboardInterrupt:
        console.print("\n[yellow]Dashboard stopped[/yellow]")

def full_update():
    """Run complete update cycle: download → charts"""
    clear_screen()
    
    console.print(Panel(
        "[bold]Full Pipeline Update[/bold]\n\n"
        "This will:\n"
        "  1. Download latest data from ABS\n"
        "  2. Generate all static charts",
        border_style="cyan"
    ))
    
    if not Confirm.ask("\nProceed?", default=True):
        return
    
    # Step 1: Download
    console.print("\n[bold cyan]═══ Step 1: Data Download ═══[/bold cyan]")
    success, _ = run_script("download.py", "Data Download")
    
    if not success:
        console.print("\n[red]Pipeline halted due to download error[/red]")
        return
    
    # Step 2: Charts
    console.print("\n[bold cyan]═══ Step 2: Chart Generation ═══[/bold cyan]")
    success, _ = run_script("generate_charts.py", "Chart Generation")
    
    # Final summary
    console.print("\n[bold green]═══ Pipeline Complete ═══[/bold green]")
    csv_count = count_files_in_dir(OUTPUT_DIRECTORY)
    chart_count = count_files_in_dir("abs_charts_output")
    console.print(f"  • Data files: {csv_count}")
    console.print(f"  • Charts: {chart_count}")

def show_datasets():
    """Display configured datasets"""
    clear_screen()
    
    if not CONFIG_LOADED:
        console.print("[red]✗ Configuration not loaded[/red]")
        return
    
    table = Table(show_header=True, header_style="bold cyan", box=box.ROUNDED)
    table.add_column("Dataset", style="cyan", width=35)
    table.add_column("Catalogue", justify="center", width=12)
    table.add_column("Frequency", justify="center", width=12)
    table.add_column("Tables", justify="center", width=10)
    
    for dataset in ABS_DATASETS:
        table.add_row(
            dataset['name'],
            dataset['cat_id'],
            dataset['frequency'],
            str(len(dataset['tables']))
        )
    
    console.print(Panel(table, title=f"[bold]Configured Datasets ({len(ABS_DATASETS)} total)[/bold]", border_style="cyan"))

# =============================================================================
# MAIN MENU
# =============================================================================

def show_menu():
    """Display main menu"""
    clear_screen()
    
    # Header
    header = Text()
    header.append("ABS Economic Data Pipeline\n", style="bold cyan")
    header.append("Control Center", style="bold white")
    
    console.print(Panel(header, border_style="cyan", padding=(1, 2)))
    
    # Menu options
    menu_table = Table(show_header=False, box=None, padding=(0, 2))
    menu_table.add_column("Option", style="bold yellow", width=8)
    menu_table.add_column("Description", style="white")
    
    menu_table.add_row("0", "Show pipeline status")
    menu_table.add_row("1", "Download data from ABS")
    menu_table.add_row("2", "Generate static charts")
    menu_table.add_row("3", "Launch interactive dashboard")
    menu_table.add_row("4", "Full update (download + charts)")
    menu_table.add_row("5", "View configured datasets")
    menu_table.add_row("Q", "Quit")
    
    console.print(menu_table)
    console.print()

def main():
    """Main program loop"""
    
    while True:
        show_menu()
        
        choice = Prompt.ask(
            "[bold cyan]Select option[/bold cyan]",
            choices=["0", "1", "2", "3", "4", "5", "q", "Q"],
            default="0"
        ).upper()
        
        if choice == "Q":
            console.print("\n[cyan]Goodbye![/cyan]\n")
            break
        elif choice == "0":
            show_status()
        elif choice == "1":
            download_data()
        elif choice == "2":
            generate_charts()
        elif choice == "3":
            launch_dashboard()
        elif choice == "4":
            full_update()
        elif choice == "5":
            show_datasets()
        
        if choice != "Q":
            console.print("\n")
            Prompt.ask("[dim]Press Enter to continue[/dim]", default="")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Interrupted by user[/yellow]\n")
        sys.exit(0)
