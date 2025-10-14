from machine import Pin, ADC
import time


red = Pin(14, Pin.OUT)
yellow = Pin(12, Pin.OUT)
green = Pin(13, Pin.OUT)


sensor = ADC(Pin(32))
sensor.atten(ADC.ATTN_11DB)    # 3.3V
sensor.width(ADC.WIDTH_12BIT)  # 0-4095 bits

NO_FIELD_LOW = 2100
NO_FIELD_HIGH = 2350

while True:
    value = sensor.read()
    print("Valor ADC:", value)

    red.value(0)
    yellow.value(0)
    green.value(0)

    if NO_FIELD_LOW <= value <= NO_FIELD_HIGH:
        yellow.value(1)  # No hay
    elif value > NO_FIELD_HIGH:
        green.value(1)   # Positivo
    else:
        red.value(1) # Negativo

    time.sleep(0.2)
