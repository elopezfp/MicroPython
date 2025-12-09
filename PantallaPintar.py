from machine import Pin, SPI
from tft_libs.ili9341 import Display as ILI9341
import time

# SPI setup
spi = SPI(
    2,
    baudrate=2_000_000,      # Para que funcionen bien ambos dispositivos
    sck=Pin(18),
    mosi=Pin(23),
    miso=Pin(19)
)

# Iniciar Pantalla TFT
tft = ILI9341(
    spi,
    cs=Pin(5),
    dc=Pin(21),
    rst=Pin(13),
    width=240,
    height=320
)

# Limpiar pantalla y mostrar mensaje inicial
tft.clear()
tft.draw_text8x8(10, 10, "Touch Paint v3", 0xFFFF)
tft.draw_text8x8(10, 30, "Toca para dibujar :)", 0x07E0)

#Iniciar Touch XPT2046
cs_touch = Pin(15, Pin.OUT, value=1)

GET_X = 0b11010000
GET_Y = 0b10010000

# Calibración de la pantalla
X_MIN = 205
X_MAX = 1860
Y_MIN = 191
Y_MAX = 2047

# Leer Coordenadas
def read_touch_raw():
    cs_touch.value(0)
    time.sleep_us(40)

    rx = bytearray(3)

    # dummy + real X
    spi.write_readinto(bytearray([GET_X,0,0]), rx)
    spi.write_readinto(bytearray([GET_X,0,0]), rx)
    x = (rx[1] << 4) | (rx[2] >> 4)

    # dummy + real Y
    spi.write_readinto(bytearray([GET_Y,0,0]), rx)
    spi.write_readinto(bytearray([GET_Y,0,0]), rx)
    y = (rx[1] << 4) | (rx[2] >> 4)

    cs_touch.value(1)
    return x, y

# Adaptar coordenadas al tamaño de la pantalla 
def normalize(x_raw, y_raw):
    # X directo
    x = int((x_raw - X_MIN) * 240 / (X_MAX - X_MIN))

    # Y INVERTIDO
    y = int((Y_MAX - y_raw) * 320 / (Y_MAX - Y_MIN))
    y -= 23

    # Limitar dentro de pantalla
    x = max(0, min(239, x))
    y = max(0, min(319, y))

    return x, y

# Preparar para dibujar 
colors = [0xF800, 0x07E0, 0x001F, 0xFFE0, 0xF81F, 0x07FF, 0xFFFF]
color_idx = 0
last_touch = 0
last_print = 0  

# Listo
print("Sistema listo. Dibuja!")


# Bucle principal
while True:
    x_raw, y_raw = read_touch_raw()

    # Detectar toque válido
    if (X_MIN - 100) < x_raw < (X_MAX + 100) and (Y_MIN - 100) < y_raw < (Y_MAX + 100):
        current = time.ticks_ms()

        # Dibujo rápido
        if time.ticks_diff(current, last_touch) > 15:
            x, y = normalize(x_raw, y_raw)
            tft.fill_circle(x, y, 4, colors[color_idx])

            # Cambiar color cada segundo
            if (current % 1000) < 20:
                color_idx = (color_idx + 1) % len(colors)

            last_touch = current

        # Mostrar coordenadas cada 1 segundo en la consola del ESP32
        if time.ticks_diff(current, last_print) > 1000:
            x, y = normalize(x_raw, y_raw)
            print("Coordenadas:", x, y)
            last_print = current

    time.sleep(0.005)
