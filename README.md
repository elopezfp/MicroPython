# Fermentador IoT de cerveza

Este workspace incluye dos entregables:

1. Un documento tecnico en PDF para la actividad de definicion y diseno del proyecto.
2. Una simulacion web del fermentador con control de temperatura, bomba y ventiladores.

## Ejecutar la simulacion

```bash
python app.py
```

Abre despues `http://127.0.0.1:5000` en el navegador.

## Contenido del proyecto

- `app.py`: servidor Flask con la simulacion y la lectura del ESP32.
- `micropython_main.py`: firmware MicroPython del ESP32.
- `templates/index.html`: pantalla principal del simulador.
- `static/styles.css`: estilos del panel.
- `static/app.js`: logica de actualizacion de la interfaz.
- `ili9341.py`: driver de la pantalla TFT usado por el ESP32.