import contextlib
import io
import os
import uuid
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

from .base import BaseTool, StepResult

class PythonExecutorTool(BaseTool):
    name = "python_executor"
    description = (
        "Executes Python code locally against the uploaded dataset. "
        "The pandas dataframe is available as the variable `df`. "
        "The pandas library is available as `pd`. "
        "The matplotlib.pyplot module is available as `plt`. "
        "If you want to generate and save a plot, you MUST save it to the directory path "
        "provided in the `artifact_dir` variable (e.g. plt.savefig(f'{artifact_dir}/my_plot.png')). "
        "Always use print() to output your final text or numerical answers so they can be captured."
    )
    parameters = {
        "code": {
            "type": "string",
            "description": "The raw Python script to execute. Do not wrap in markdown.",
            "required": True
        }
    }
    requires = []

    def execute(self, session_data: dict, args: dict, **kwargs) -> StepResult:
        code = args.get("code")
        if not code:
            return StepResult(tool_name=self.name, success=False, summary="Missing 'code' argument.")

        active_upload_id = session_data.get("active_upload_id")
        if not active_upload_id:
            return StepResult(tool_name=self.name, success=False, summary="No active upload found. The user needs to upload a CSV file first.")

        # Find the active upload
        uploads = session_data.get("uploads", [])
        active_upload = next((u for u in uploads if u["id"] == active_upload_id), None)
        if not active_upload:
            return StepResult(tool_name=self.name, success=False, summary="Active upload not found in session data.")

        try:
            # Load the dataframe
            try:
                df = pd.read_csv(active_upload["file_path"])
            except UnicodeDecodeError:
                df = pd.read_csv(active_upload["file_path"], encoding="latin1")
        except Exception as e:
            return StepResult(tool_name=self.name, success=False, summary=f"Failed to load dataset: {e}")

        # Setup artifact directory
        session_id = session_data.get("id")
        artifact_dir = Path("data/artifacts") / str(session_id)
        artifact_dir.mkdir(parents=True, exist_ok=True)

        existing_pngs = set(artifact_dir.glob("*.png"))

        from RestrictedPython import compile_restricted, safe_builtins
        from RestrictedPython.Guards import guarded_iter_unpack_sequence
        
        def my_getattr(obj, name):
            # Allow all attribute access for pandas/matplotlib to work
            return getattr(obj, name)

        class StdoutPrintCollector:
            def __init__(self, _getattr_=None):
                pass
            def __call__(self, *args, **kwargs):
                print(*args, **kwargs)
            def _call_print(self, *objects, **kwargs):
                print(*objects, **kwargs)

        # Setup the environment
        env = {
            '__builtins__': safe_builtins.copy(),
            '_print_': StdoutPrintCollector,
            '_getattr_': my_getattr,
            '_getitem_': lambda obj, key: obj[key],
            '_getiter_': iter,
            '_unpack_sequence_': guarded_iter_unpack_sequence,
            'df': df,
            'pd': pd,
            'plt': plt,
            'artifact_dir': str(artifact_dir)
        }

        # Redirect stdout
        stdout_capture = io.StringIO()
        import warnings
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", SyntaxWarning)
                byte_code = compile_restricted(code, '<string>', 'exec')
            with contextlib.redirect_stdout(stdout_capture):
                exec(byte_code, env)
            execution_success = True
            output = stdout_capture.getvalue().strip()
            if not output:
                output = "Code executed successfully but did not print anything. Please use print() to output results."
        except Exception as e:
            execution_success = False
            output = f"Execution error: {str(e)}"
            import traceback
            output += f"\n\nTraceback:\n{traceback.format_exc()}"

        current_pngs = set(artifact_dir.glob("*.png"))
        new_pngs = current_pngs - existing_pngs
        
        artifacts_dict = {}
        for i, png_path in enumerate(new_pngs):
            artifacts_dict[f"plot_{uuid.uuid4().hex[:6]}.png"] = str(png_path)

        return StepResult(
            tool_name=self.name,
            success=execution_success,
            summary=output if execution_success else f"Error:\n{output}",
            artifacts=artifacts_dict
        )
