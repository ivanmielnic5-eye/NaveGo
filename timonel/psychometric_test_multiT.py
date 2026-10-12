import numpy as np
import scipy.optimize as opt
import scipy.special as sp


def psychometric_rel(delta, k, dT):
    """P(TERMINAR | delta) = sigmoid(k * (delta + dT))."""
    return sp.expit(k * (delta + dT))


def fit_multi_T(deltas, probs):
    initial = [0.5, 0.0]
    bounds = ([0.01, -5.0], [50.0, 5.0])
    popt, pcov = opt.curve_fit(
        psychometric_rel, deltas, probs,
        p0=initial, bounds=bounds, maxfev=10000
    )
    k, dT = popt
    perr = np.sqrt(np.diag(pcov))
    residuals = probs - psychometric_rel(deltas, k, dT)
    ss_res = np.sum(residuals**2)
    ss_tot = np.sum((probs - np.mean(probs))**2)
    r2 = 1 - ss_res / (ss_tot + 1e-8)
    return {"k": float(k), "dT": float(dT),
            "k_err": float(perr[0]), "dT_err": float(perr[1]),
            "r2": float(r2)}


if __name__ == "__main__":
    rng = np.random.default_rng(42)
    T_values = [10.0, 15.0, 20.0, 25.0]
    k_true = 1.70   # k efectivo (despues del softmax 2L)
    dT_true = -0.3  # sesgo real del modelo simulado
    noise = 0.03

    deltas = []
    probs = []
    for T in T_values:
        for d in np.linspace(T - 8, T + 8, 30):
            delta = T - d
            p_teorica = psychometric_rel(delta, k_true, dT_true)
            p_obs = np.clip(p_teorica + rng.normal(0, noise), 0, 1)
            deltas.append(delta)
            probs.append(p_obs)

    deltas = np.array(deltas)
    probs = np.array(probs)

    res = fit_multi_T(deltas, probs)

    print("=== RECUPERACION DE PARAMETROS (4 T mezclados, con ruido) ===")
    print(f"  k_true  = {k_true:.3f}")
    print(f"  k_fit   = {res['k']:.3f} (+/- {res['k_err']:.3f})")
    print(f"  dT_true = {dT_true:+.3f}")
    print(f"  dT_fit  = {res['dT']:+.3f} (+/- {res['dT_err']:.3f})")
    print(f"  R2      = {res['r2']:.4f}")
    print()
    ok = (abs(res['k'] - k_true) < 0.15
          and abs(res['dT'] - dT_true) < 0.1
          and res['r2'] > 0.9)
    if ok:
        print(">>> RECUPERACION CORRECTA. El fix de Notebook LLM funciona. <<<")
    else:
        print(">>> RECUPERACION FALLA. Revisar. <<<")
