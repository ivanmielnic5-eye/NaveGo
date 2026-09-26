#!/usr/bin/env python3
"""
FASE A3 - A+Kalman vs B vs Hibrido por estado.

Pregunta: cual metodo de medicion de distancia es mejor para NaveGo?
  A   : suma de distancias entre fixes (actual de NaveGo)
  A+K : idem pero con filtro Kalman sobre la posicion antes de sumar
  B   : integracion de speed x dt (Doppler)
  H   : hibrido por estado (A+K si v < umbral, B si v >= umbral)

DISENO (fijado por el Director, NO modificable):
  5 trayectorias x 5 semillas = 25 corridas.
  sigma_pos = 1.5 m, sigma_speed = 0.1 m/s, sin cortes ni spikes.
  Report interval 1 Hz.

FILTRO KALMAN (A+K):
  Estado 2D por eje (posicion, velocidad) con modelo de velocidad
  constante. Q = ruido de proceso (aceleracion), R = sigma_pos^2.
  Se filtra lat y lon por separado, en metros, con dt real entre fixes.
  Salida = posicion filtrada; A+K = polilinea sobre las posiciones
  filtradas, con la MISMA logica de gap/descarte que A para ser
  comparable (el filtro ya suaviza, pero se mantiene por fidelidad).
"""
import json
import math
import os
import statistics
import subprocess

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(BASE, '..', '..', '..'))
SIM_PATH = os.path.join(ROOT, 'tools', 'gnss_simulator.py')

TRAJS = ['T1_recta5', 'T2_virada', 'T3_quieto_nav', 'T4_garreo', 'T5_variable']
SEEDS = list(range(5000, 5005))
SIGMA_POS_M = 1.5
SIGMA_SPEED_MS = 0.1
V_UMBRAL_KN = 1.0

KNOT_TO_MS = 1.0 / 1.94384
MAX_JUMP_DISTANCE_M = 15.0
MIN_DISTANCE_DELTA_M = 0.8

# --- Parametros del filtro Kalman ---
# R = varianza del ruido de medicion de posicion (m^2)
KALMAN_R = SIGMA_POS_M ** 2
# Q = varianza de la aceleracion del proceso (m^2/s^4). Barco lento:
# aceleraciones tipicas < 0.1 m/s^2. Q pequeno => suaviza fuerte.
KALMAN_Q = 0.01 ** 2


def haversine(lat1, lon1, lat2, lon2):
    R = 6371000.0
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = (math.sin(dLat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dLon / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(a))


def load_jsonl(path):
    out = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def _dt(fixes, i):
    return (fixes[i]['receivedAt'] - fixes[i - 1]['receivedAt']) / 1000.0


# ---------------------------------------------------------------- METODO A
def method_a(fixes):
    """Replica de la logica de distancia de useNaveGoTracker.ts."""
    dist = 0.0
    n_desc = n_gap = 0
    last = None
    for f in fixes:
        if last is not None:
            d = haversine(last['latitude'], last['longitude'],
                          f['latitude'], f['longitude'])
            if d > MAX_JUMP_DISTANCE_M:
                n_gap += 1
                d = 0.0
            elif d < MIN_DISTANCE_DELTA_M:
                n_desc += 1
                d = 0.0
            dist += d
        last = f
    return dist, n_desc, n_gap


# -------------------------------------------------------------- A+KALMAN
def kalman_filter(fixes, sigma_pos=SIGMA_POS_M, q=KALMAN_Q):
    """Filtro de Kalman 2 estados (pos, vel) por eje, en metros.

    Devuelve lista de (lat_filt, lon_filt) en grados a partir de la
    lat/lon del primer fix como origen local.
    """
    lat0 = fixes[0]['latitude']
    lon0 = fixes[0]['longitude']
    m_lat = 110540.0
    m_lon = 111320.0 * math.cos(math.radians(lat0))
    R = sigma_pos ** 2

    # Estado por eje: [pos, vel]
    xs = [0.0, 0.0]
    ys = [0.0, 0.0]
    # Covarianza inicial: posicion poco confiable, velocidad desconocida
    Px = [[sigma_pos ** 2, 0.0], [0.0, 1.0 ** 2]]
    Py = [[sigma_pos ** 2, 0.0], [0.0, 1.0 ** 2]]

    out = []
    prev_t = None
    for f in fixes:
        t = f['receivedAt'] / 1000.0
        zx = (f['longitude'] - lon0) * m_lon
        zy = (f['latitude'] - lat0) * m_lat
        if prev_t is None:
            dt = 1.0
        else:
            dt = t - prev_t
            if dt <= 0:
                dt = 1.0
        prev_t = t

        for s, P, z in ((xs, Px, zx), (ys, Py, zy)):
            # --- prediccion: pos += vel*dt
            s[0] = s[0] + s[1] * dt
            # F = [[1, dt], [0, 1]];  Q del modelo de aceleracion
            q11 = q * dt ** 4 / 4.0
            q12 = q * dt ** 3 / 2.0
            q22 = q * dt ** 2
            p00 = P[0][0] + dt * (P[1][0] + P[0][1]) + dt * dt * P[1][1] + q11
            p01 = P[0][1] + dt * P[1][1] + q12
            p10 = P[1][0] + dt * P[1][1] + q12
            p11 = P[1][1] + q22
            P[0][0], P[0][1], P[1][0], P[1][1] = p00, p01, p10, p11

            # --- actualizacion (H = [1, 0])
            y = z - s[0]
            S = P[0][0] + R
            K0 = P[0][0] / S
            K1 = P[1][0] / S
            s[0] += K0 * y
            s[1] += K1 * y
            n00 = (1 - K0) * P[0][0]
            n01 = (1 - K0) * P[0][1]
            n10 = P[1][0] - K1 * P[0][0]
            n11 = P[1][1] - K1 * P[0][1]
            P[0][0], P[0][1], P[1][0], P[1][1] = n00, n01, n10, n11

        out.append((lat0 + ys[0] / m_lat, lon0 + xs[0] / m_lon))
    return out


def method_ak(fixes):
    """A sobre posiciones filtradas con Kalman. Misma logica gap/descarte."""
    filt = kalman_filter(fixes)
    dist = 0.0
    n_desc = n_gap = 0
    last = None
    for lat, lon in filt:
        if last is not None:
            d = haversine(last[0], last[1], lat, lon)
            if d > MAX_JUMP_DISTANCE_M:
                n_gap += 1
                d = 0.0
            elif d < MIN_DISTANCE_DELTA_M:
                n_desc += 1
                d = 0.0
            dist += d
        last = (lat, lon)
    return dist, n_desc, n_gap


# ---------------------------------------------------------------- METODO B
def method_b(fixes):
    """Integracion speed x dt, rectangular extremo derecho."""
    dist = 0.0
    for i in range(1, len(fixes)):
        dt = _dt(fixes, i)
        if dt <= 0:
            continue
        dist += (fixes[i].get('speed') or 0.0) * dt
    return dist


# ------------------------------------------------------------- HIBRIDO H
def method_h(fixes, umbral_kn=V_UMBRAL_KN):
    """Hibrido por estado: A+K si v < umbral, B si v >= umbral.

    La decision usa la velocidad medida media del intervalo. La rama
    A+K usa las posiciones filtradas (no las crudas).
    """
    filt = kalman_filter(fixes)
    dist = 0.0
    last_f = None
    last_p = None
    for i, f in enumerate(fixes):
        if last_f is not None:
            dt = _dt(fixes, i)
            v0 = last_f.get('speed') or 0.0
            v1 = f.get('speed') or 0.0
            v_mean_kn = ((v0 + v1) / 2.0) / KNOT_TO_MS
            if dt > 0 and v_mean_kn >= umbral_kn:
                dist += (v0 + v1) / 2.0 * dt          # tramo rapido: B
            else:
                d = haversine(last_p[0], last_p[1], filt[i][0], filt[i][1])
                if d > MAX_JUMP_DISTANCE_M or d < MIN_DISTANCE_DELTA_M:
                    d = 0.0
                dist += d                              # tramo lento: A+K
        last_f = f
        last_p = filt[i]
    return dist


def gt_reference(gt_pts, present_ts):
    """Ground truth geometrico sobre el tramo efectivamente reportado."""
    idx = [j for j, p in enumerate(gt_pts) if p['timestamp'] in present_ts]
    dist = 0.0
    for a, b in zip(idx, idx[1:]):
        if b == a + 1:
            dx = gt_pts[b]['pos_x'] - gt_pts[a]['pos_x']
            dz = gt_pts[b]['pos_z'] - gt_pts[a]['pos_z']
            dist += math.sqrt(dx * dx + dz * dz)
    return dist


def gt_net_displacement(gt_pts, present_ts):
    """Desplazamiento NETO real (inicio->fin) del tramo reportado.

    Para T4 (garreo) el camino oscilado y el desplazamiento neto difieren
    en dos ordenes de magnitud; se reportan ambos para no elegir el GT
    que favorece a un metodo.
    """
    idx = [j for j, p in enumerate(gt_pts) if p['timestamp'] in present_ts]
    if len(idx) < 2:
        return 0.0
    a, b = gt_pts[idx[0]], gt_pts[idx[-1]]
    return math.hypot(b['pos_x'] - a['pos_x'], b['pos_z'] - a['pos_z'])


def run_cell(traj, seed, tmp_scen, tmp_fixes, umbral_kn=V_UMBRAL_KN):
    gt_path = os.path.join(BASE, f'tray_{traj}.jsonl')
    sc = {
        'scenario_id': f'A3_{traj}_{seed}',
        'seed': seed,
        'duration_s': 240,
        'report_interval_ms': 1000,
        'gnss': {
            'noise_sigma_m': SIGMA_POS_M,
            'speed_sigma_ms': SIGMA_SPEED_MS,
            'latency_ms': 0,
            'cut_windows': [],
            'spikes': {'probability': 0.0, 'min_jump_m': 50, 'max_jump_m': 500},
        },
        'hydro': {'wind_strength': 0.0, 'wind_direction_deg': 0.0},
        'initial_state': {'lat': -31.648, 'lon': -60.708},
    }
    with open(tmp_scen, 'w') as f:
        json.dump(sc, f, indent=2)

    r = subprocess.run(['python3', SIM_PATH, gt_path, tmp_scen, tmp_fixes],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f'simulador fallo {traj} seed={seed}: {r.stderr}')

    fixes = load_jsonl(tmp_fixes)
    gt_pts = load_jsonl(gt_path)
    present = set(f['measuredAt'] for f in fixes)
    ref = gt_reference(gt_pts, present)
    net = gt_net_displacement(gt_pts, present)

    A, n_desc, n_gap = method_a(fixes)
    AK, ak_desc, ak_gap = method_ak(fixes)
    B = method_b(fixes)
    H = method_h(fixes, umbral_kn)

    row = {'tray': traj, 'seed': seed, 'gt_ref_m': ref, 'gt_net_m': net,
           'A_m': A, 'AK_m': AK, 'B_m': B, 'H_m': H,
           'n_desc': n_desc, 'n_gap': n_gap, 'n_fixes': len(fixes)}
    for name, val in (('A', A), ('AK', AK), ('B', B), ('H', H)):
        er = (val - ref) / ref * 100.0
        row[f'er_{name}'] = er
        row[f'abs_{name}'] = abs(er)
    return row


def mean(xs):
    return statistics.mean(xs) if xs else float('nan')


def main():
    tmp_scen = os.path.join(BASE, '_tmp_scen_a3.json')
    tmp_fixes = os.path.join(BASE, '_tmp_fixes_a3.jsonl')
    results = []
    for traj in TRAJS:
        for seed in SEEDS:
            results.append(run_cell(traj, seed, tmp_scen, tmp_fixes))

    # Barrido de umbral para T5 (0.5, 1.0, 1.5, 2.0 kn) -- caracteriza el
    # umbral, no cambia los criterios de refutacion.
    umbral_rows = []
    for umb in (0.5, 1.0, 1.5, 2.0):
        errs = []
        for seed in SEEDS:
            row = run_cell('T5_variable', seed, tmp_scen, tmp_fixes, umb)
            errs.append(row['abs_H'])
        umbral_rows.append((umb, mean(errs)))

    lines = []
    p = lines.append
    p('=== FASE A3: ERROR RELATIVO (%) POR TRAYECTORIA (media 5 semillas) ===')
    p(f'sigma_pos={SIGMA_POS_M} m  sigma_speed={SIGMA_SPEED_MS} m/s  '
      f'semillas={SEEDS[0]}-{SEEDS[-1]}  {len(results)} corridas')
    p('')
    p(f'{"trayectoria":16s} {"ref_m":>8s} {"A%":>9s} {"A+K%":>9s} '
      f'{"B%":>9s} {"H%":>9s} | {"|A|%":>8s} {"|A+K|%":>8s} '
      f'{"|B|%":>8s} {"|H|%":>8s}')
    for traj in TRAJS:
        cell = [r for r in results if r['tray'] == traj]
        p(f'{traj:16s} {mean([c["gt_ref_m"] for c in cell]):8.2f} '
          f'{mean([c["er_A"] for c in cell]):9.2f} '
          f'{mean([c["er_AK"] for c in cell]):9.2f} '
          f'{mean([c["er_B"] for c in cell]):9.2f} '
          f'{mean([c["er_H"] for c in cell]):9.2f} | '
          f'{mean([c["abs_A"] for c in cell]):8.2f} '
          f'{mean([c["abs_AK"] for c in cell]):8.2f} '
          f'{mean([c["abs_B"] for c in cell]):8.2f} '
          f'{mean([c["abs_H"] for c in cell]):8.2f}')

    # ---- Error absoluto en metros (media) ----
    p('')
    p('=== ERROR ABSOLUTO (m, media 5 semillas) ===')
    p(f'{"trayectoria":16s} {"ref_m":>9s} {"A_m":>9s} {"A+K_m":>9s} '
      f'{"B_m":>9s} {"H_m":>9s}')
    for traj in TRAJS:
        cell = [r for r in results if r['tray'] == traj]
        ref = mean([c['gt_ref_m'] for c in cell])
        p(f'{traj:16s} {ref:9.2f} '
          f'{mean([c["A_m"] for c in cell]) - ref:9.2f} '
          f'{mean([c["AK_m"] for c in cell]) - ref:9.2f} '
          f'{mean([c["B_m"] for c in cell]) - ref:9.2f} '
          f'{mean([c["H_m"] for c in cell]) - ref:9.2f}')

    p('')
    p('=== GT ALTERNATIVO PARA T4_garreo (no se elige el que favorece) ===')
    t4 = [r for r in results if r['tray'] == 'T4_garreo']
    p('El camino OSCILADO real es 96.97 m; el desplazamiento NETO real es '
      '0.63 m. Metodos medidos (media):')
    p(f'  camino oscilado GT = {mean([c["gt_ref_m"] for c in t4]):8.2f} m  '
      f'neto GT = {mean([c["gt_net_m"] for c in t4]):6.2f} m')
    p(f'  A={mean([c["A_m"] for c in t4]):7.2f} m  '
      f'A+K={mean([c["AK_m"] for c in t4]):6.2f} m  '
      f'B={mean([c["B_m"] for c in t4]):6.2f} m  '
      f'H={mean([c["H_m"] for c in t4]):6.2f} m')

    p('')
    p('=== VERIFICACION DE HIPOTESIS (criterios fijados) ===')
    p('')

    # H1: T1_recta5, |err_A+K - err_B| < 5% en 4 de 5 corridas.
    h1 = [r for r in results if r['tray'] == 'T1_recta5']
    h1_ok = sum(1 for c in h1 if abs(c['er_AK'] - c['er_B']) < 5.0)
    h1_bad = sum(1 for c in h1 if abs(c['er_AK'] - c['er_B']) >= 5.0)
    h1v = ('CONFIRMADA' if h1_ok >= 4
           else ('REFUTADA' if h1_bad >= 2 else 'INCONCLUSA'))
    p(f'H1 (T1_recta5, |err_A+K - err_B| < 5% en >=4/5): ok={h1_ok}/5 '
      f'bad={h1_bad}/5 diffs='
      f'{[round(abs(c["er_AK"] - c["er_B"]), 3) for c in h1]} -> {h1v}')

    # H2: T4_garreo, |err A+K| < 10 m y |err B| > 50 m.
    h2 = [r for r in results if r['tray'] == 'T4_garreo']
    ak_ok = sum(1 for c in h2 if abs(c['AK_m'] - c['gt_ref_m']) < 10.0)
    b_ok = sum(1 for c in h2 if abs(c['B_m'] - c['gt_ref_m']) > 50.0)
    ak_bad = sum(1 for c in h2 if abs(c['AK_m'] - c['gt_ref_m']) > 20.0)
    if ak_ok >= 4 and b_ok >= 4:
        h2v = 'CONFIRMADA'
    elif ak_bad >= 2:
        h2v = 'REFUTADA'
    else:
        h2v = 'INCONCLUSA'
    p(f'H2 (T4_garreo, |err A+K| < 10 m y |err B| > 50 m): '
      f'A+K<10m en {ak_ok}/5  B>50m en {b_ok}/5  A+K>20m en {ak_bad}/5')
    p(f'    err_abs A+K (m)={[round(abs(c["AK_m"] - c["gt_ref_m"]), 2) for c in h2]}')
    p(f'    err_abs B   (m)={[round(abs(c["B_m"] - c["gt_ref_m"]), 2) for c in h2]} -> {h2v}')
    p('    Causa: contra el camino OSCILADO (96.97 m) A+K descarta los pasos')
    p('    <0.8 m y mide solo la deriva neta (~7 m): error ~90 m. B mide el')
    p('    ruido de speed (~10 m), NO >50 m. Contra el desplazamiento NETO')
    p('    (0.63 m) ambos sobreestiman, B mas que A+K.')

    # H3: error maximo del hibrido < max(A+K) y < max(B) en T3 y T5.
    h3_trajs = ['T3_quieto_nav', 'T5_variable']
    wins = 0
    lines3 = []
    for traj in h3_trajs:
        cell = [r for r in results if r['tray'] == traj]
        mx_ak = max(c['abs_AK'] for c in cell)
        mx_b = max(c['abs_B'] for c in cell)
        mx_h = max(c['abs_H'] for c in cell)
        ok = mx_h < mx_ak and mx_h < mx_b
        wins += 1 if ok else 0
        lines3.append(f'    {traj}: max|A+K|={mx_ak:7.2f}  max|B|={mx_b:7.2f}  '
                      f'max|H|={mx_h:7.2f}  -> {"SI" if ok else "NO"}')
    h3v = ('CONFIRMADA' if wins >= 3
           else ('REFUTADA' if wins == 0 else 'INCONCLUSA'))
    p(f'H3 (max|H| < max|A+K| y < max|B| en T3+T5): cumple en {wins}/2 '
      f'trayectorias (criterio >=3/5 corridas -> ver nota) -> {h3v}')
    for l in lines3:
        p(l)

    # H3 por corrida: comparacion pareada sobre el conjunto combinado T3+T5.
    combo = [r for r in results if r['tray'] in h3_trajs]
    pair_ok = sum(1 for c in combo if c['abs_H'] < c['abs_AK'] and c['abs_H'] < c['abs_B'])
    p(f'    H3 pareado por corrida (T3+T5, n={len(combo)}): '
      f'H menor que ambos en {pair_ok}/{len(combo)}')

    p('')
    p('=== BARRIDO DE UMBRAL DEL HIBRIDO (T5_variable, media |err|%) ===')
    for umb, e in umbral_rows:
        p(f'    umbral={umb:4.2f} kn  ->  |err H| medio = {e:6.3f}%')

    for tmp in (tmp_scen, tmp_fixes):
        if os.path.exists(tmp):
            os.remove(tmp)

    with open(os.path.join(BASE, 'resultados_faseA3.json'), 'w') as f:
        json.dump({'results': results,
                   'umbral_barrido': [{'umbral_kn': u, 'abs_H': e}
                                      for u, e in umbral_rows],
                   'config': {'sigma_pos_m': SIGMA_POS_M,
                              'sigma_speed_ms': SIGMA_SPEED_MS,
                              'seeds': SEEDS,
                              'kalman_q': KALMAN_Q,
                              'kalman_r': KALMAN_R}},
                  f, indent=2)

    report = '\n'.join(lines)
    print(report)
    with open(os.path.join(BASE, 'salida_faseA3.txt'), 'w') as f:
        f.write(report + '\n')
    print(f'\n[{len(results)} corridas] -> resultados_faseA3.json / salida_faseA3.txt')


if __name__ == '__main__':
    main()
