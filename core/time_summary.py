import datetime

def calculate_time_per_title(filepath):
    entries = []

    with open(filepath, "r") as file:
        for line in file:
            line = line.strip()
            if " - Active window: " not in line:
                continue
            timestamp_text, title = line.split(" - Active window: ", 1)
            timestamp = datetime.datetime.strptime(timestamp_text, "%Y-%m-%d %H:%M:%S")
            entries.append((timestamp, title))

    totals = {}

    if not entries:
        return totals

    streak_start = entries[0][0]
    streak_title = entries[0][1]

    for i in range(1, len(entries)):
        current_time, current_title = entries[i]

        if current_title != streak_title:
            duration = entries[i - 1][0] - streak_start
            totals[streak_title] = totals.get(streak_title, datetime.timedelta()) + duration
            streak_start = current_time
            streak_title = current_title

    last_duration = entries[-1][0] - streak_start
    totals[streak_title] = totals.get(streak_title, datetime.timedelta()) + last_duration

    return totals


if __name__ == "__main__":
    results = calculate_time_per_title("../data/activity.log")
    for title, duration in results.items():
        print(f"{title}: {duration}")