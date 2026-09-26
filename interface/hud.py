import json, threading, time
import psutil
import webview
import sys
sys.path.insert(0, os.path.expanduser("~/alita/core"))
import hud_bridge

def stats_loop(window):
    psutil.cpu_percent(interval=None)
    time.sleep(0.5)
    last_msg_count = 0
    while True:
        cpu = psutil.cpu_percent(interval=None)
        vm = psutil.virtual_memory()
        disk = psutil.disk_usage('/').percent
        therm = []
        try:
            for name, entries in psutil.sensors_temperatures().items():
                for e in entries:
                    therm.append({"label": e.label or name, "temp": round(e.current)})
        except Exception:
            pass
        data = {
            "cpu": round(cpu),
            "ram_used_gb": round(vm.used / (1024**3), 1),
            "ram_total_gb": round(vm.total / (1024**3), 1),
            "ram_pct": round(vm.percent),
            "disk_pct": round(disk),
            "therm": therm[:8]
        }
        try:
            window.evaluate_js(f"window.updateStats && window.updateStats({json.dumps(data)})")
        except Exception:
            pass
        try:
            status = hud_bridge._read()
            window.evaluate_js(f"window.setHudState && window.setHudState({json.dumps(status.get('state','listening'))})")
            msgs = status.get("messages", [])
            if len(msgs) > last_msg_count:
                for m in msgs[last_msg_count:]:
                    window.evaluate_js(f"window.addMsg && window.addMsg({json.dumps(m.get('text',''))}, {json.dumps(m.get('role','assistant'))})")
                last_msg_count = len(msgs)
        except Exception:
            pass
        time.sleep(0.2)

class Api:
    def send_message(self, text):
        hud_bridge.set_typed_input(text)
        return True

window = webview.create_window(
    "ALITA",
    "file://" + os.path.expanduser("~/alita/interface/ALITA.html"),
    width=1400, height=900,
    background_color="#050809",
    js_api=Api()
)
webview.start(stats_loop, window)
