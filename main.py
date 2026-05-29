from machine import Pin, ADC
import time

red = Pin(14, Pin.OUT)
yellow = Pin(12, Pin.OUT)
green = Pin(13, Pin.OUT)

sensor = ADC(Pin(32))
sensor.atten(ADC.ATTN_11DB)    # rango 3.3V
sensor.width(ADC.WIDTH_12BIT)  # resolución 0-4095

NO_FIELD_LOW = 2100
NO_FIELD_HIGH = 2350

while True:
    value = sensor.read()
    print("Valor ADC:", value)

    red.value(0)
    yellow.value(0)
    green.value(0)

    # Si hay campo magnetico lo hace
    if not (NO_FIELD_LOW <= value <= NO_FIELD_HIGH):

        # Calcular valor absoluto
        if value < NO_FIELD_LOW:
            intensity = NO_FIELD_LOW - value
        else:
            intensity = value - NO_FIELD_HIGH

        # Dependiendo de la intensidad encendemos LED
        if intensity < 200:     # Baja -> verde
            green.value(1)
        elif intensity < 500:   # Media -> amarillo
            yellow.value(1)
        else:                  # Alta -> rojo
            red.value(1)

    time.sleep(0.2)
