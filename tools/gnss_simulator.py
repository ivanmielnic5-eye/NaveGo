#!/usr/bin/env python3
import json, random, math, sys, os

def noise_to_latlon(sigma_m, lat_deg):
    sigma_lat = sigma_m / 110540.0
    sigma_lon = sigma_m / (111320.0 * math.cos(math.radians(lat_deg)))
    return sigma_lat, sigma_lon

def meters_to_latlon(dx_m, dy_m, lat_deg):
    dlat = dy_m / 110540.0
    dlon = dx_m / (111320.0 * math.cos(math.radians(lat_deg)))
    return dlat, dlon

def run(gt_path, scenario_path, out_path):
    with open(scenario_path) as f:
        sc = json.load(f)
    rng = random.Random(sc["seed"])

    lat0 = sc["initial_state"]["lat"]
    lon0 = sc["initial_state"]["lon"]
    sigma_m = sc["gnss"]["noise_sigma_m"]
    latency_ms = sc["gnss"]["latency_ms"]
    interval_ms = sc["report_interval_ms"]
    cuts = sc["gnss"]["cut_windows"]
    spike = sc["gnss"]["spikes"]
    # FASE A2: error de Doppler en el speed medido (m/s). Opcional y
    # retrocompatible: si el escenario no lo declara, vale 0.0 y el
    # simulador se comporta igual que antes.
    sigma_speed_ms = sc["gnss"].get("speed_sigma_ms", 0.0)

    gt = []
    with open(gt_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                gt.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    output = []
    last_report = -1e9
    for m in gt:
        t = m["timestamp"]
        if t - last_report < interval_ms:
            continue
        last_report = t
        in_cut = any(
            (m["elapsed_s"] >= c["start_s"]) and
            (m["elapsed_s"] < c["start_s"] + c["duration_s"])
            for c in cuts
        )
        if in_cut:
            continue

        sigma_lat, sigma_lon = noise_to_latlon(sigma_m, lat0)
        base_dlat, base_dlon = meters_to_latlon(m["pos_x"], m["pos_z"], lat0)
        noise_dlat = rng.gauss(0, sigma_lat)
        noise_dlon = rng.gauss(0, sigma_lon)
        if rng.random() < spike["probability"]:
            jump_m = rng.uniform(spike["min_jump_m"], spike["max_jump_m"])
            angle = rng.uniform(0, 2 * math.pi)
            jlat, jlon = meters_to_latlon(
                jump_m * math.cos(angle),
                jump_m * math.sin(angle),
                lat0,
            )
            noise_dlat += jlat
            noise_dlon += jlon
        lat = lat0 + base_dlat + noise_dlat
        lon = lon0 + base_dlon + noise_dlon
        measured_at = m["timestamp"]
        received_at = measured_at + latency_ms
        accuracy = sigma_m * 1.5
        speed_real_ms = m["sog_kn"] / 1.94384
        # Doppler imperfecto: ruido gaussiano aditivo. Se acota a >= 0
        # porque un receptor no reporta velocidad negativa en magnitud.
        speed_meas_ms = speed_real_ms
        if sigma_speed_ms > 0.0:
            speed_meas_ms = max(0.0, speed_real_ms + rng.gauss(0, sigma_speed_ms))
        fix = {
            "measuredAt": measured_at,
            "receivedAt": received_at,
            "latitude": lat,
            "longitude": lon,
            "accuracy": accuracy,
            "speed": speed_meas_ms,
            "speed_real": speed_real_ms,
            "heading": m["cog_deg"],
        }
        output.append(fix)

    with open(out_path, "w") as f:
        for fix in output:
            f.write(json.dumps(fix) + "\n")
    print(f"Fixes generados: {len(output)}")
    print(f"Ground truth leido: {len(gt)} muestras")
    print(f"Salida: {out_path}")

def main():
    if len(sys.argv) < 4:
        print("Uso: gnss_simulator.py <ground_truth.jsonl> <scenario.json> <salida.jsonl>")
        sys.exit(1)
    run(sys.argv[1], sys.argv[2], sys.argv[3])

if __name__ == "__main__":
    main()
