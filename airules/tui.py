from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Button, Input
from textual.containers import Container

from .config import get_config, write_config, get_config_path, CONFIG_FILENAME

class ConfigTUI(App):
    """A Textual app to manage .airulesrc configuration."""

    CSS_PATH = "tui.css"
    BINDINGS = [("q", "quit", "Quit")]

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Container(id="main-container")
        yield Footer()

    def on_mount(self) -> None:
        """Called when the app is mounted."""
        try:
            config = get_config()
            container = self.query_one("#main-container")

            config_path = get_config_path()
            container.mount(Static(f"[b]Configuration loaded from:[/b] {config_path}\n"))

            for section, options in config.items():
                container.mount(Static(f"[bold cyan][{section}][/bold cyan]"))
                for key, value in options.items():
                    container.mount(Static(f"  [b]{key}:[/b]"))
                    input_widget = Input(value, id=f"{section}_{key}")
                    container.mount(input_widget)
                container.mount(Static("\n"))
            
            container.mount(Button("Save", variant="primary", id="save"))

        except FileNotFoundError:
            self.query_one("#main-container").mount(
                Static("[bold red]ERROR: .airulesrc not found.[/bold red]")
            )
            self.query_one("#main-container").mount(
                Static("Please run [b]airules init[/b] to create one.")
            )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            try:
                config = get_config()
                for section in config.sections():
                    for key in config.options(section):
                        input_widget = self.query_one(f"#{section}_{key}", Input)
                        config.set(section, key, input_widget.value)
                
                write_config(config)
                self.query_one("#main-container").mount(Static("\n[bold green]✓ Configuration saved![/bold green]"))

            except Exception as e:
                self.query_one("#main-container").mount(Static(f"\n[bold red]✗ Error saving config: {e}[/bold red]"))

if __name__ == "__main__":
    app = ConfigTUI()
    app.run()
