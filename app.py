from __future__ import annotations

import random
import threading
import time
from collections import deque
from datetime import datetime

from flask import Flask, jsonify, render_template, request

import webbrowser
import socket
import subprocess
import os
from serial.tools import list_ports


app = Flask(__name__)

state_lock = threading.Lock()
history = deque(maxlen=120)

state = {
    "mode": "auto",
    "setpoint_c": 18.0,
    "temperature_c": 20.4,
    "water_temp_c": 19.1,
    "humidity_pct": 56.0,
    "fan_speed_pct": 45,
    "pump_on": True,
    "peltier_power_pct": 30,
    "esp32_connected": True,
    "wifi_rssi": -58,
    "uptime_s": 0,
    "status": "Esperando ESP32",
    "alarm": False,
    "beer_progress_pct": 0,
    "beer_ready": False,
    "beer_phase": "Preparando prueba",
    "beer_gravity": 1.050,
    "last_update": datetime.now().isoformat(timespec="seconds"),
}

# bandera para abrir el navegador una sola vez cuando el ESP32 se conecte
browser_opened = False
# timestamp del último JSON recibido
last_json_time = 0.0


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def add_history_entry() -> None:
    history.append(
        {
            "ts": datetime.now().strftime("%H:%M:%S"),
            "temperature_c": round(state["temperature_c"], 2),
            "water_temp_c": round(state["water_temp_c"], 2),
            "setpoint_c": round(state["setpoint_c"], 2),
        }
    )


def build_status() -> str:
    if state["alarm"]:
        return "Alarma termica: revisar refrigeracion"
    delta = state["temperature_c"] - state["setpoint_c"]
    if abs(delta) < 0.3:
        return "Temperatura estable"
    if delta > 0:
        return "Enfriando fermentacion"
    return "Recuperando calor"


def set_online_state_from_data(data: dict) -> None:
    state["esp32_connected"] = True
    state["temperature_c"] = data.get("temp", 0.0)
    state["setpoint_c"] = data.get("setpoint", state.get("setpoint_c", 18.0))
    is_cooling = data.get("enfriando", False)
    state["pump_on"] = is_cooling
    state["fan_speed_pct"] = 100 if is_cooling else 0
    state["peltier_power_pct"] = 100 if is_cooling else 0
    if "water_temp" in data:
        state["water_temp_c"] = float(data["water_temp"])
    state["beer_progress_pct"] = int(data.get("beer_progress", 0))
    state["beer_ready"] = bool(data.get("beer_ready", False))
    state["beer_phase"] = str(data.get("beer_phase", "Fermentando"))
    state["beer_gravity"] = float(data.get("beer_gravity", 0.0))
    if "humidity_pct" in data:
        state["humidity_pct"] = float(data["humidity_pct"])
    state["uptime_s"] += 2
    state["status"] = "Cerveza virtual lista" if state["beer_ready"] else f"Cerveza virtual: {state['beer_phase']}"
    state["last_update"] = datetime.now().isoformat(timespec="seconds")


import json

virtual_og = 1.050 # Densidad original inicial
virtual_fg = virtual_og

FIRMWARE_PORT = os.environ.get("FIRMWARE_PORT", "COM3")
AUTO_START_FIRMWARE = os.environ.get("AUTO_START_FIRMWARE", "1") == "1"


def detect_firmware_ports() -> list[str]:
    available = {port.device.upper() for port in list_ports.comports()}
    ordered: list[str] = []
    for port in (FIRMWARE_PORT, "COM5"):
        if port.upper() in available and port not in ordered:
            ordered.append(port)
    for port in (FIRMWARE_PORT, "COM5"):
        if port not in ordered:
            ordered.append(port)
    return ordered


def set_zero_state() -> None:
    # Sin ESP32: dejar los valores a cero/por defecto (no simulados)
    state["temperature_c"] = 0.0
    state["water_temp_c"] = 0.0
    state["humidity_pct"] = 0.0
    state["fan_speed_pct"] = 0
    state["pump_on"] = False
    state["peltier_power_pct"] = 0
    state["esp32_connected"] = False
    state["wifi_rssi"] = 0
    state["status"] = "Esperando ESP32"
    state["alarm"] = False
    state["beer_progress_pct"] = 0
    state["beer_ready"] = False
    state["beer_phase"] = "Sin datos del ESP32"
    state["beer_gravity"] = 0.0

def simulation_loop() -> None:
    global browser_opened
    global last_json_time
    def ensure_browser_open() -> None:
        global browser_opened
        if browser_opened:
            return
        for _ in range(10):
            try:
                s = socket.create_connection(("127.0.0.1", 5000), timeout=0.5)
                s.close()
                webbrowser.open("http://127.0.0.1:5000", new=2)
                print("Abriendo navegador en http://127.0.0.1:5000")
                browser_opened = True
                return
            except Exception:
                time.sleep(0.5)

    def start_bridge() -> None:
        global mp_proc
        if mp_proc is not None:
            return
        ensure_browser_open()
        for port in detect_firmware_ports():
            cmd = ["mpremote", "connect", port, "run", "micropython_main.py"]
            print(f"Lanzando puente serial: {' '.join(cmd)}")
            try:
                mp_proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                threading.Thread(target=_mpremote_reader_thread, args=(mp_proc,), daemon=True).start()
                return
            except Exception as e:
                print(f"No se pudo usar {port}: {e}")
                mp_proc = None

    print(f"Preparando puente de datos por {FIRMWARE_PORT} (la app no abre COM3 directamente)")
    with state_lock:
        state["esp32_connected"] = False

    if AUTO_START_FIRMWARE:
        start_bridge()

    while True:
        # El lector de mpremote actualiza el estado; no reseteamos por pausas cortas.
        time.sleep(0.5)


def update_from_payload(payload: dict) -> None:
    if "mode" in payload and payload["mode"] in {"auto", "manual"}:
        state["mode"] = payload["mode"]
    if "setpoint_c" in payload:
        state["setpoint_c"] = float(clamp(float(payload["setpoint_c"]), 10, 28))
    if "fan_speed_pct" in payload:
        state["fan_speed_pct"] = int(clamp(float(payload["fan_speed_pct"]), 0, 100))
    if "pump_on" in payload:
        state["pump_on"] = bool(payload["pump_on"])
    if "peltier_power_pct" in payload:
        state["peltier_power_pct"] = int(clamp(float(payload["peltier_power_pct"]), 0, 100))
    state["status"] = build_status()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/state")
def api_state():
    with state_lock:
        payload = dict(state)
        payload["history"] = list(history)
    return jsonify(payload)


@app.route("/api/control", methods=["POST"])
def api_control():
    payload = request.get_json(force=True, silent=True) or {}
    with state_lock:
        update_from_payload(payload)
        if payload.get("action") == "reset":
            state["temperature_c"] = 20.4
            state["water_temp_c"] = 19.1
            state["humidity_pct"] = 56.0
            state["fan_speed_pct"] = 45
            state["pump_on"] = True
            state["peltier_power_pct"] = 30
            state["mode"] = "auto"
            state["alarm"] = False
            state["status"] = "Sistema reiniciado"
            state["beer_progress_pct"] = 0
            state["beer_ready"] = False
            state["beer_phase"] = "Preparando prueba"
            state["beer_gravity"] = 1.050
            history.clear()
            add_history_entry()
        response = dict(state)
        response["history"] = list(history)
    return jsonify({"ok": True, "state": response})


def bootstrap() -> None:
    with state_lock:
        set_zero_state()
        history.clear()
        add_history_entry()
    thread = threading.Thread(target=simulation_loop, daemon=True)
    thread.start()


# control para lanzar mpremote desde la app y leer su stdout
mp_proc = None

def _mpremote_reader_thread(proc: subprocess.Popen) -> None:
    global mp_proc
    global last_json_time
    try:
        while True:
            line = proc.stdout.readline()
            if not line:
                if proc.poll() is not None:
                    print("mpremote proceso finalizado")
                    break
                time.sleep(0.05)
                continue
            line = line.strip()
            if line.startswith("JSON_DATA:"):
                try:
                    data = json.loads(line.replace("JSON_DATA:", ""))
                    with state_lock:
                        set_online_state_from_data(data)
                        last_json_time = time.time()
                        if not history or history[-1]["ts"] != datetime.now().strftime("%H:%M:%S"):
                            add_history_entry()
                except Exception:
                    pass
            elif line:
                print(f"mpremote: {line}")
    finally:
        mp_proc = None
        last_json_time = 0.0
        with state_lock:
            set_zero_state()


@app.route('/api/run_firmware', methods=['POST'])
def api_run_firmware():
    """Inicia `mpremote run micropython_main.py` como subproceso y lee su salida.
    Útil para pruebas sin copiar :main.py en el dispositivo.
    """
    global mp_proc
    if mp_proc is not None:
        return jsonify({"ok": False, "msg": "Firmware ya en ejecución"}), 400
    try:
        # abrir navegador antes de lanzar
        try:
            s = socket.create_connection(("127.0.0.1", 5000), timeout=0.5)
            s.close()
            webbrowser.open("http://127.0.0.1:5000", new=2)
        except Exception:
            pass

        for port in detect_firmware_ports():
            cmd = ["mpremote", "connect", port, "run", "micropython_main.py"]
            try:
                mp_proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                t = threading.Thread(target=_mpremote_reader_thread, args=(mp_proc,), daemon=True)
                t.start()
                return jsonify({"ok": True, "cmd": cmd})
            except Exception:
                mp_proc = None

        return jsonify({"ok": False, "error": "No se detectó COM3 ni COM5"}), 500
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


bootstrap()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)