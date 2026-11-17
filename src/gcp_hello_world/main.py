# A simple hello world demo
            
from datetime import datetime     # Built-in Python module (no uv add needed)
from rich.console import Console  # Third-party library (installed via uv)
from rich.panel import Panel

console = Console()

def main():
    now = datetime.now().strftime("%H:%M:%S")
    console.print(Panel(f"[bold green]Hello, World![/bold green]\nThe time is [cyan]{now}[/cyan]"))

if __name__ == "__main__":
    main()