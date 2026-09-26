import subprocess
import time
import ast

def get_active_window():
    result = subprocess.run(
        [
            "gdbus", "call", "--session",
            "--dest", "org.gnome.Shell",
            "--object-path", "/org/gnome/Shell/Extensions/WindowsExt",
            "--method", "org.gnome.Shell.Extensions.WindowsExt.FocusTitle"
        ],
        capture_output=True,
        text=True
    )
    output = result.stdout.strip()

    try:
        parsed = ast.literal_eval(output)
        title = parsed[0]
    except (ValueError, SyntaxError, IndexError):
        title = output

    return title


if __name__ == "__main__":
    from logger import ActivityLogger

    logger = ActivityLogger()

    while True:
        try:
            title = get_active_window()
            logger.log(f"Active window: {title}")
            print(f"Logged: {title}")
        except Exception as error:
            logger.log(f"Tracker error (skipped): {error}")
        time.sleep(10)