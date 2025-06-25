from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Button, Input
from textual.containers import Container

from .config import get_config, CONFIG_FILENAME

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

            container.mount(Static(f"[b]Configuration loaded from:[/b] {CONFIG_FILENAME}\n"))

            for section, options in config.items():
                container.mount(Static(f"[bold cyan][{section}][/bold cyan]"))
                for key, value in options.items():
                                        input_widget = Input(value, id=f"{section}_{key}")
                    container.mount(Static(f"  [b]{key}:[/b]"))
                    container.mount(input_widget)
                container.mount(Static("\n")) # Add a blank line for spacing

        except FileNotFoundError:
            self.query_one("#main-container").mount(
                Static("[bold red]ERROR: .airulesrc not found.[/bold red]")
            )
            self.query_one("#main-container").mount(
                Static("Please run [b]airules init[/b] to create one.")
            )

            container.mount(Button("Save", variant="primary", id="save"))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            try:
                config = get_config()
                for section in config.sections():
                    for key in config.options(section):
                        input_widget = self.query_one(f"#{section}_{key}", Input)
                        config.set(section, key, input_widget.value)
                
                from .config import write_config
                write_config(config)
                self.mount(Static("[bold green]Configuration saved![/bold green]"))

            except Exception as e:
                self.mount(Static(f"[bold red]Error saving config: {e}[/bold red]"))

if __name__ == "__main__":
    app = ConfigTUI()
    app.run()
