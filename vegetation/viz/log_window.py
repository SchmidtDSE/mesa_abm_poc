from solara import use_effect, use_state, component, Column, Markdown
import logging
from pathlib import Path
from typing import Callable
import datetime


class MemoryLogHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.logs = []
        self.callback = None

    def emit(self, record):
        log_entry = self.format(record)
        self.logs.append(log_entry)
        if self.callback:
            self.callback()

    def get_logs(self):
        return "\n".join(self.logs)

    def set_callback(self, callback):
        self.callback = callback


# Create log dir
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Create handlers
file_handler = logging.FileHandler(log_dir / "vegetation.log")
memory_handler = MemoryLogHandler()

# Set format
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
memory_handler.setFormatter(formatter)

# Setup logger
logger = logging.getLogger("vegetation")
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(memory_handler)


def make_log_window_component() -> Callable:
    @component
    def LogDisplay(__model) -> Column:
        logs, set_logs = use_state("")

        def update_logs():
            set_logs(memory_handler.get_logs())

        # Set the callback to update logs
        memory_handler.set_callback(update_logs)

        # Initial update
        update_logs()

        return Markdown(
            logs,
            style={
                "maxHeight": "400px",
                "overflowY": "auto",
                "border": "1px solid #ccc",
                "padding": "10px",
                "fontFamily": "monospace",
            },
        )

    return LogDisplay
