import os

from textual import events
from textual.widgets import Header, Footer, Label, OptionList, Static, Button, Input
from typing import TYPE_CHECKING
from lib.utility import set_permanent_env_var, test_ollama_connection
if TYPE_CHECKING:
    from main import AppGUI

class OllamaURLInput(Input):
    """A TextArea that submits on Enter instead of adding a newline."""
    app:"AppGUI"
    async def _on_key(self, event: events.Key) -> None:
        if event.key == "enter" or event.key == "shift+enter":
            event.prevent_default()
            event.stop()
            url = self.value.strip()
            if url == "":
                url = self.placeholder
            if test_ollama_connection(url):
                set_permanent_env_var("OLLAMA_HOST", url)
                self.app.set_page("model-selector-page")
            else:
                error_label = self.screen.query_one("#ollama-url-input-error", Label)
                error_label.content = f"Failed to connect to Ollama server at: {url}"

class OllamaUrlPage(Static):
    app:"AppGUI"
    def compose(self):
        yield Label("Please enter the URL for your Ollama server:")
        yield OllamaURLInput(placeholder=os.getenv("OLLAMA_HOST"))
        yield Label("NOTE: This will set your OLLAMA_HOST environment variable.", id="ollama-url-input-note")
        yield Label("", id="ollama-url-input-error")
