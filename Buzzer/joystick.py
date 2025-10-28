from machine import Pin, ADC, PWM
import time
# Joystick
vrx = ADC(Pin(32))   # X
vry = ADC(Pin(33))   # Y
sw = Pin(26, Pin.IN, Pin.PULL_UP)  # Boton

for a in (vrx, vry):
    a.atten(ADC.ATTN_11DB) # 3v3
    a.width(ADC.WIDTH_12BIT) # 0-4095

# Buzzer
buzzer = PWM(Pin(25))
buzzer.duty(0)  # apagado al inicio

min_freq = 200     # frec min
max_freq = 2000    # frec max

while True:
    x = vrx.read()
    y = vry.read()
    boton = sw.value()  # 0 = presionado, 1 = suelto

    if boton == 0:  # si se presiona el botón
        # Mapear X (0-4095) → frecuencia (200-2000 Hz)
        freq = int(min_freq + (x / 4095) * (max_freq - min_freq))

        # Mapear Y (0-4095) → volumen (0-1023)
        vol = int((y / 4095) * 1023)

        # Aplicar al buzzer
        buzzer.freq(freq)
        buzzer.duty(vol)
    else:
        # Botón no presionado → silencio
        buzzer.duty(0)

    print("X:", x, "Y:", y, "Freq:", freq, "Vol:", vol, "Botón:", boton)
    time.sleep(0.05)
