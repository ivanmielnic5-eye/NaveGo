# Esquema de etiquetas V2

Dos archivos JSON por escenario, INDEPENDIENTES del evaluador.

## traj_events_<traj>_<seed>.json — eventos de trayectoria

Describen el MOVIMIENTO REAL del barco. Producidos por gen_traj.py.

Ejemplo:

    {
      "traj_id": "detencion_5kn_20s",
      "seed": 8100,
      "duration_s": 300,
      "events": [
        {"type": "speed_change", "t_s": 0, "v_old_ms": null, "v_new_ms": 2.572},
        {"type": "stop", "t_start_s": 200, "t_end_s": 220},
        {"type": "speed_change", "t_s": 220, "v_old_ms": 0.0, "v_new_ms": 2.572},
        {"type": "turn", "t_start_s": 60, "t_end_s": 75, "angle_deg": 90}
      ]
    }

Tipos: speed_change, stop, turn.

## obs_events_<traj>_<gnss>_<seed>.json — eventos de observación

Describen LO QUE SE INYECTÓ en las observaciones. Producidos por gen_obs.py.

Ejemplo:

    {
      "traj_id": "recta_const_5kn",
      "gnss_cfg": {"noise_sigma_m": 1.0, "speed_sigma_ms": 0.0, "latency_ms": 300,
                   "cut_windows": [{"start_s": 150, "duration_s": 10}]},
      "seed": 8100,
      "T0_ms": 1790279042897,
      "fixes_sha256": "...",
      "events": [
        {"type": "cut", "start_s": 150, "duration_s": 10, "advance_m": 25.7},
        {"type": "missing_fix", "timestamp_expected": 1790279192897, "reason": "cut"},
        {"type": "spike_config", "probability": 0.01, "min_jump_m": 50, "max_jump_m": 500},
        {"type": "batch_config", "period_s": 3}
      ]
    }

Tipos: cut, missing_fix, spike_config, batch_config.

## Etiqueta por salto candidato (en el evaluador)

Para cada par (fix[i-1], fix[i]) con d_pair > 15 m, el evaluador asigna:

| Etiqueta | Regla |
|---|---|
| INJECTED_CUT | Existe cut con fix[i-1].measuredAt < cut_window_start y fix[i].measuredAt > cut_window_end |
| INJECTED_SPIKE | Existe spike con fix_index == i |
| NO_INJECTED_EVENT | No hay cut ni spike en la ventana |
| NO_ETIQUETABLE | Datos insuficientes |

Regla dura: NO_INJECTED_EVENT NO significa "ruido". Significa que el
generador no inyectó nada. El evaluador reporta:
- n_shift_m = desplazamiento real según GT.
- n_shift_err = d_pair - n_shift_m = componente atribuible a error de posición.

## Umbral de aceptación del etiquetado

NO_ETIQUETABLE <= 5 % por archivo. Si se supera, el etiquetado es débil,
se detiene la corrida y se revisa.
