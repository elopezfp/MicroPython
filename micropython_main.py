import time
import json

try:
    from machine import Pin, SPI
    IS_MICROPYTHON = True
except ImportError:
    IS_MICROPYTHON = False
    class Pin:
        OUT = 0
        def __init__(self, pin_id, mode=None):
            self.pin_id = pin_id
        def value(self, v=None):
            pass

def setup_pins():
    enfriamiento = Pin(25, Pin.OUT)
    enfriamiento.value(1)  # HIGH = apagado por defecto (Low Level Trigger)
    return enfriamiento


RELAY_ACTIVE_LOW = True


def relay_on(pin):
    # Si el relé hace click pero no conmuta la carga, prueba a cambiar RELAY_ACTIVE_LOW.
    pin.value(0 if RELAY_ACTIVE_LOW else 1)


def relay_off(pin):
    pin.value(1 if RELAY_ACTIVE_LOW else 0)

def main():
    enfriamiento = setup_pins()

    if not IS_MICROPYTHON:
        print("Corre esto directo en el ESP32.")
        return

    print("=== INICIANDO FERMENTADOR ===")

    USE_TFT = False
    try:
        import ili9341
        spi = SPI(2, baudrate=32000000, sck=Pin(18), mosi=Pin(23), miso=Pin(19))
        display = ili9341.ILI9341(spi, cs=Pin(15), dc=Pin(2), rst=Pin(4))
        display.fill(0x0000)
        display.fill_rect(0, 0, 320, 40, 0x01CF)
        display.text("FERMENTADOR LOCAL", 30, 10, 0xFFFF, 2)
        USE_TFT = True
        print("Pantalla TFT iniciada!")
    except Exception as e:
        print("Sin pantalla TFT:", e)

    temperatura = 20.8
    setpoint = 19.5
    temp_min = 18.6
    temp_max = 21.2
    cool_on_temp = setpoint + 0.6
    cool_off_temp = setpoint - 0.6
    enfriando = False
    inicio = time.time()
    duracion_prueba = 120
    cerveza_lista = False
    agua_temp = 16.2
    humedad_pct = 62.0

    while True:
        elapsed_s = int(time.time() - inicio)

        if elapsed_s >= duracion_prueba:
            cerveza_lista = True
            enfriando = False
            relay_off(enfriamiento)
            temperatura = setpoint
            agua_temp = setpoint - 0.8
        else:
            if temperatura >= cool_on_temp and not enfriando:
                relay_on(enfriamiento)
                enfriando = True
            elif temperatura <= cool_off_temp and enfriando:
                relay_off(enfriamiento)
                enfriando = False

            if enfriando:
                temperatura -= 0.62
                agua_temp -= 0.28
                humedad_pct += 0.16
            else:
                temperatura += 0.48
                agua_temp += 0.14
                humedad_pct += 0.05

            temperatura = max(temp_min, min(temp_max, temperatura))
            agua_temp = max(10.0, min(24.5, agua_temp))
            humedad_pct = max(45.0, min(88.0, humedad_pct))

        if USE_TFT:
            temp_color = 0x07FF if enfriando else 0x07E0
            display.fill_rect(0, 80, 320, 50, 0x0000)
            display.text(f"{temperatura:.1f} C", 70, 80, temp_color, 4)
            display.fill_rect(0, 160, 320, 60, 0x0000)
            if cerveza_lista:
                display.text("CERVEZA LISTA", 60, 160, 0x07E0, 2)
            elif enfriando:
                display.text("ENFRIANDO", 80, 160, 0x07FF, 2)
            else:
                display.text("PRUEBA ALE", 80, 160, 0x07E0, 2)

        beer_progress = min(100, int((elapsed_s / duracion_prueba) * 100))
        beer_gravity = 1.050 - (beer_progress / 100.0) * 0.040
        if cerveza_lista:
            beer_progress = 100
            beer_gravity = 1.010

        data = {
            "temp": temperatura,
            "enfriando": enfriando,
            "setpoint": setpoint,
            "elapsed_s": elapsed_s,
            "test_duration_s": duracion_prueba,
            "beer_progress": beer_progress,
            "beer_ready": cerveza_lista,
            "beer_phase": "Lista" if cerveza_lista else ("Enfriando" if enfriando else "Subiendo temperatura"),
            "beer_gravity": round(beer_gravity, 4),
            "water_temp": round(agua_temp, 2),
            "humidity_pct": round(humedad_pct, 2),
        }
        print("JSON_DATA:" + json.dumps(data))

        if beer_progress >= 100:
            relay_off(enfriamiento)  # apagar relé al finalizar
            print("=== PROGRESO 100% ALCANZADO, DETENIENDO MICROPYTHON ===")
            break

        time.sleep(2)

if __name__ == "__main__":
    main()