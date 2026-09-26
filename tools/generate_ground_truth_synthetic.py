#!/usr/bin/env python3
"""
Ground truth sintetico realista de un velero navegando 5 minutos.
Basado en EXPEDIENTE/37_PARAMETROS_NAUTICOS_REALES.md:
- Aceleracion gradual desde quieto
- Navegacion en un borde
- Una virada suave (30 s de transicion)
- Navegacion en el otro borde
"""
import json
import math

def generate(duration_s=300, output_path='docs/gnss/ground_truth_synthetic_5min.jsonl'):
    t0_ms = 1790279042897
    samples = []
    pos_x = 0.0
    pos_z = 0.0
    heading = 0.0
    speed_kn = 0.0

    for t in range(0, duration_s):
        # Plan de navegacion realista
        if t < 20:
            # Quieto en el muelle
            heading = 0.0
            speed_kn = 0.0
        elif t < 40:
            # Aceleracion gradual 0 -> 5 nudos
            speed_kn = 5.0 * (t - 20) / 20.0
            heading = 40.0
        elif t < 140:
            # Borde 1: rumbo +40 grados
            heading = 40.0
            speed_kn = 5.0
        elif t < 170:
            # Virada suave: gira de +40 a -40 en 30 segundos
            progress = (t - 140) / 30.0
            heading = 40.0 - 80.0 * progress
            speed_kn = 5.0
        else:
            # Borde 2: rumbo -40 grados
            heading = -40.0
            speed_kn = 5.0

        speed_ms = speed_kn / 1.94384
        rad = math.radians(heading)
        dx = speed_ms * math.sin(rad)
        dz = -speed_ms * math.cos(rad)

        # Sub-muestreo a 60 Hz para integracion suave
        for sub in range(60):
            dt = 1.0 / 60.0
            pos_x += dx * dt
            pos_z += dz * dt

        timestamp = t0_ms + t * 1000
        samples.append({
            "timestamp": timestamp,
            "elapsed_s": float(t),
            "pos_x": round(pos_x, 6),
            "pos_y": 0.0,
            "pos_z": round(pos_z, 6),
            "sog_kn": round(speed_kn, 4),
            "cog_deg": round(heading, 4),
            "hdg_deg": round(heading, 4),
            "roll_deg": 0.0,
            "pitch_deg": 0.0,
            "yaw_deg": round(heading, 4),
        })

    with open(output_path, 'w') as f:
        for s in samples:
            f.write(json.dumps(s) + '\n')

    # Calcular trayectoria real (suma de distancias entre puntos)
    trayecto = 0.0
    for i in range(1, len(samples)):
        dx = samples[i]['pos_x'] - samples[i-1]['pos_x']
        dz = samples[i]['pos_z'] - samples[i-1]['pos_z']
        trayecto += math.sqrt(dx*dx + dz*dz)
    desplazamiento = math.sqrt(samples[-1]['pos_x']**2 + samples[-1]['pos_z']**2)

    print(f'Muestras generadas: {len(samples)}')
    print(f'Duracion: {duration_s} segundos')
    print(f'Salida: {output_path}')
    print(f'Posicion final: ({samples[-1]["pos_x"]:.2f}, {samples[-1]["pos_z"]:.2f})')
    print(f'Longitud de trayectoria: {trayecto:.2f} m')
    print(f'Desplazamiento neto: {desplazamiento:.2f} m')

if __name__ == '__main__':
    generate()
