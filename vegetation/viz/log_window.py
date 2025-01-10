import sys
import io
import solara


class StdoutCapture:
    def __init__(self):
        self.output = io.StringIO()
        self.old_stdout = None

    def __enter__(self):
        self.old_stdout = sys.stdout
        sys.stdout = self.output
        return self.output

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self.old_stdout


def make_log_window_component():
    @solara.component
    def StdoutDisplay():
        # Create a state to store captured output
        output, set_output = solara.use_state("")

        # Capture stdout when model runs
        def capture_output():
            with StdoutCapture() as stdout:
                # Your model operations here
                model.step()
                set_output(stdout.getvalue())

        return solara.Column(
            solara.Button("Capture Output", on_click=capture_output),
            solara.Textarea(value=output, read_only=True),
        )

    return StdoutDisplay
