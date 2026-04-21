from textual import events
from textual.reactive import reactive
from textual.widget import Widget

class ToggleBox(Widget):
    """Toggles between different types."""
    
    DEFAULT_CSS = """
    ToggleBox {
        background: rgb(30,35,50);
        height:1;
    }
    """

    render_buffer = reactive("?")

    def __init__(self, *options:list[str], starting_option_index:int=0, option_colors:list[str]|None = None, **kwargs):
        super().__init__(**kwargs)
        self.options = options
        self.selected_index = starting_option_index

        self.styles.width = max((len(opt) for opt in options), default=0) + 2
        
        self.option_colors = option_colors

        if self.option_colors and len(self.option_colors) != len(self.options):
            raise IndexError("The length of options and option colors must be the same.")
        
        self.render_buffer = f"{self.options[self.selected_index]: ^{self.styles.width}}"

        if self.option_colors:
            self.styles.background = self.option_colors[self.selected_index]
    
    def render(self):
        return self.render_buffer
    
    def _on_click(self, event: events.Click):
        if event.button == 1:
            self.selected_index = (self.selected_index + 1) % len(self.options)
            if self.option_colors is not None:
                self.styles.background = self.option_colors[self.selected_index]

            self.render_buffer = f"{self.options[self.selected_index]: ^{self.styles.width}}"