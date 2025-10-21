from machine import Pin, PWM
import time

# Configurar buzzer
buzzer = PWM(Pin(25))

# Frecuencia en Hz
buzzer.freq(440)

buzzer.duty(512)   # volumen medio

time.sleep(2)      # sonar 2 segundos

# Parar el sonido
buzzer.duty(0)
buzzer.deinit()
print("Listo")
