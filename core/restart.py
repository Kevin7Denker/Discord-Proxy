import os
import sys

def restart() -> None:
    """Gracefully restart the current process.

    This function re‑executes the Python interpreter with the original script
    and arguments. It is used when the launcher detects the known fatal error
    2012 and wants to restart without requiring the user to manually close the
    application.
    """
    python_exe = sys.executable
    script_path = os.path.abspath(sys.argv[0])
    args = sys.argv[1:]
    # Replace the current process with a fresh one
    os.execv(python_exe, [python_exe, script_path] + args)
