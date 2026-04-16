from __future__ import annotations
from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widgets import Header, Footer, Label, OptionList, Static, Button
from textual.widgets.option_list import Option
from lib.chat_page import ChatPage
import ollama as oll
from typing import Callable, TYPE_CHECKING
if TYPE_CHECKING:
    from main import AppGUI

class ModelDisplay(Static):
    model_name = reactive("?")
    def render(self) -> str:
        return f"Current Model: {self.model_name}"

class ModelSelectionPrompt(Static):
    """Used to select a model for the agent"""
    app:AppGUI
    def __init__(self, model_selected_callback:Callable[[oll.ListResponse.Model],None], **kwargs):
        super().__init__(**kwargs)
        self.ollama_models = oll.list().models
        self.model_selected_callback = model_selected_callback

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Label("Please choose a model:")
        yield OptionList(
            *[Option(str(model.model), id=f"model-option-{n}") for n, model in enumerate(self.ollama_models)],
            id="option-list-container"
        )

    def on_show(self) -> None:
        """Focus the list so 'Enter' works immediately."""
        self.query_one(OptionList).focus()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        # Get the label or index of what was selected
        model_index = int(event.option.id.replace("model-option-", ""))
        model = self.ollama_models[model_index]
        self.model_selected_callback(model)
        self.app.set_page("chat-page")

