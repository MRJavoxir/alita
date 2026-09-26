import datetime
import subprocess

def notify(title, message):
    subprocess.run(["notify-send", title, message])

def check_time_rules():
    now = datetime.datetime.now()
    hour = now.hour

    if hour >= 0 and hour < 5:
        notify("Alita", "It's really late — might be worth wrapping up soon.")
    elif hour >= 5 and hour < 7:
        notify("Alita", "You're up early. Rough night or early start?")


if __name__ == "__main__":
    check_time_rules()