import datetime
import os

class ActivityLogger:
    def __init__(self, filepath="../data/activity.log"):
        self.filepath = filepath

    def log(self, message):
        now = datetime.datetime.now()
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
        with open(self.filepath, "a") as file:
            file.write(f"{timestamp} - {message}\n")

    def read_all(self):
        if not os.path.exists(self.filepath):
            print("No log file yet.")
            return
        with open(self.filepath, "r") as file:
            for line in file:
                print(line.strip())


if __name__ == "__main__":
    logger = ActivityLogger()
    logger.log("Alita logger test - Phase 1 starting")
    logger.read_all()