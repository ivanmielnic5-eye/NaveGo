import numpy as np
import scipy.optimize as opt
import scipy.special as sp


def psychometric_function(d, k, T_hat):
    """P(TERMINAR | d) = sigmoid(k * (T_hat - d))."""
    return sp.expit(k * (T_hat - d))


def fit_psychometric_curve(distances, probabilities):
    """Ajusta la curva psicometrica. Devuelve T_hat, k y R2."""
    distances = np.asarray(distances, dtype=np.float64)
    probabilities = np.asarray(probabilities, dtype=np.float64)

    # Initial guess: k razonable, T_hat en el rango de distancias
    initial_guess = [0.5, float(np.median(distances))]

    # Bounds correctos: k positivo, T_hat en rango amplio de distancias
    bounds = ([0.01, 0.0], [50.0, 1000.0])

    popt, pcov = opt.curve_fit(
        psychometric_function, distances, probabilities,
        p0=initial_guess, bounds=bounds, maxfev=10000
    )

    k, T_hat = popt
    perr = np.sqrt(np.diag(pcov)) if pcov is not None else [0.0, 0.0]

    residuals = probabilities - psychometric_function(distances, k, T_hat)
    ss_res = np.sum(residuals**2)
    ss_tot = np.sum((probabilities - np.mean(probabilities))**2)
    r_squared = 1.0 - (ss_res / (ss_tot + 1e-8))

    return {
        "T_hat": float(T_hat),
        "T_hat_std_err": float(perr[1]),
        "k_sharpness": float(k),
        "k_std_err": float(perr[0]),
        "r_squared": float(r_squared),
    }


if __name__ == "__main__":
    # Test sintetico: T real = 15m, k real = 0.8
    rng = np.random.default_rng(42)
    T_real = 15.0
    k_real = 0.8

    distancias = np.linspace(5, 25, 200)
    # Probabilidad teorica
    probs_teoricas = psychometric_function(distancias, k_real, T_real)
    # Agregar ruido
    probs_observadas = np.clip(probs_teoricas + rng.normal(0, 0.03, len(distancias)), 0, 1)

    resultado = fit_psychometric_curve(distancias, probs_observadas)

    print("=== RESULTADO DEL AJUSTE ===")
    print(f"  T_real    = {T_real:.2f}")
    print(f"  T_hat     = {resultado['T_hat']:.3f} (+/- {resultado['T_hat_std_err']:.3f})")
    print(f"  k_real    = {k_real:.2f}")
    print(f"  k_sharp   = {resultado['k_sharpness']:.3f} (+/- {resultado['k_std_err']:.3f})")
    print(f"  R2        = {resultado['r_squared']:.4f}")
    print()
    if abs(resultado['T_hat'] - T_real) < 0.5 and abs(resultado['k_sharpness'] - k_real) < 0.3:
        print(">>> EL AJUSTE FUNCIONA. Recupera T y k del sintetico. <<<")
    else:
        print(">>> EL AJUSTE FALLA. Revisar. <<<")
