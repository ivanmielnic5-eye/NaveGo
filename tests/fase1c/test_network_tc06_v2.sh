#!/usr/bin/env bash
# LOGOS - Fase 1C / TC-06
# Prueba de aislamiento de red mediante Bubblewrap.
# Usa únicamente un servidor TCP temporal en loopback.
# No modifica firewall ni necesita conexión a Internet.
# No demuestra aislamiento universal del sistema.

TC06_ROOT=""
TC06_SERVER_PID=""

tc06_cleanup() {
    local rc=$?
    local cleanup_failed=false
    trap - EXIT

    if [[ -n "${TC06_SERVER_PID:-}" ]]; then
        kill "$TC06_SERVER_PID" 2>/dev/null || true
        wait "$TC06_SERVER_PID" 2>/dev/null || true
        TC06_SERVER_PID=""
    fi

    if [[ -n "${TC06_ROOT:-}" ]]; then
        case "$TC06_ROOT" in
            /tmp/logos_tc06.*)
                if [[ -L "$TC06_ROOT" ]]; then
                    printf '%s\n' \
                      '[ERROR_LIMPIEZA] El temporal es un enlace simbólico.' >&2
                    cleanup_failed=true
                elif [[ -e "$TC06_ROOT" ]]; then
                    if [[ -d "$TC06_ROOT" ]] &&
                       rm -rf -- "$TC06_ROOT"; then
                        TC06_ROOT=""
                    else
                        printf '%s\n' \
                          '[ERROR_LIMPIEZA] No se pudo limpiar el temporal.' >&2
                        cleanup_failed=true
                    fi
                else
                    TC06_ROOT=""
                fi
                ;;
            *)
                printf '%s\n' \
                  '[ERROR_LIMPIEZA] Ruta temporal fuera del patrón esperado.' >&2
                cleanup_failed=true
                ;;
        esac
    fi

    if [[ "$cleanup_failed" == true && "$rc" -eq 0 ]]; then
        rc=3
    fi

    if [[ "$cleanup_failed" == false ]]; then
        printf '%s\n' '[+] Limpieza TC-06 completada.'
    fi

    exit "$rc"
}

tc06_infra_error() {
    printf '[ERROR_INFRAESTRUCTURA] %s\n' "$*" >&2
    exit 2
}

tc06_main() {
    set -Eeuo pipefail
    umask 077

    trap tc06_cleanup EXIT
    trap 'exit 129' HUP
    trap 'exit 130' INT
    trap 'exit 143' TERM

    local cmd bwrap_bin port host_output smoke_output smoke_rc
    local net_output net_rc
    local -a bwrap_args

    for cmd in bwrap python3 mktemp chmod mkdir rm; do
        command -v "$cmd" >/dev/null 2>&1 ||
            tc06_infra_error "Falta la herramienta: $cmd"
    done

    [[ -x /usr/bin/python3 ]] ||
        tc06_infra_error 'No existe /usr/bin/python3.'

    bwrap_bin="$(command -v bwrap)"
    TC06_ROOT="$(mktemp -d /tmp/logos_tc06.XXXXXX)" ||
        tc06_infra_error 'No se pudo crear el temporal.'
    chmod 700 -- "$TC06_ROOT" ||
        tc06_infra_error 'No se pudo proteger el temporal.'

    # Servidor temporal: solo escucha en el loopback del host.
    cat > "$TC06_ROOT/server.py" <<'PY_SERVER'
import socket
import sys
from pathlib import Path

port_file = Path(sys.argv[1])

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", 0))
    server.listen(8)
    server.settimeout(0.25)
    port_file.write_text(str(server.getsockname()[1]), encoding="ascii")

    while True:
        try:
            conn, _ = server.accept()
        except socket.timeout:
            continue

        with conn:
            try:
                conn.sendall(b"LOGOS_TC06_HOST_OK\n")
            except OSError:
                pass
PY_SERVER

    # Cliente dentro del sandbox:
    # solo considera bloqueo válido errores típicos de conectividad.
    cat > "$TC06_ROOT/client.py" <<'PY_CLIENT'
import errno
import socket
import sys

port = int(sys.argv[1])
expected_block_errors = {
    errno.ECONNREFUSED,
    errno.ENETUNREACH,
    errno.EHOSTUNREACH,
}

try:
    conn = socket.create_connection(("127.0.0.1", port), timeout=2.0)
except OSError as exc:
    if exc.errno in expected_block_errors:
        print(f"BLOCKED:{type(exc).__name__}:{exc.errno}")
        raise SystemExit(0)

    print(f"CLIENT_ERROR:{type(exc).__name__}:{exc.errno}")
    raise SystemExit(42)
else:
    conn.close()
    print("REACHED:TCP_CONNECTION_SUCCEEDED")
    raise SystemExit(41)
PY_CLIENT

    printf '%s\n' '=== LOGOS TC-06: INICIO ==='

    /usr/bin/python3 -S "$TC06_ROOT/server.py" "$TC06_ROOT/port" \
        >"$TC06_ROOT/server.stdout" \
        2>"$TC06_ROOT/server.stderr" &
    TC06_SERVER_PID=$!

    # Esperar a que el servidor publique el puerto efímero.
    for _ in {1..100}; do
        [[ -s "$TC06_ROOT/port" ]] && break

        if ! kill -0 "$TC06_SERVER_PID" 2>/dev/null; then
            break
        fi
        sleep 0.05
    done

    [[ -s "$TC06_ROOT/port" ]] ||
        tc06_infra_error 'El servidor de control no arrancó.'

    port="$(<"$TC06_ROOT/port")"
    [[ "$port" =~ ^[0-9]+$ ]] ||
        tc06_infra_error 'El servidor publicó un puerto inválido.'

    # Control positivo: demostrar que el servidor es accesible desde el host.
    if ! host_output="$(
        /usr/bin/python3 -S - "$port" <<'PY_HOST'
import socket
import sys

port = int(sys.argv[1])
with socket.create_connection(("127.0.0.1", port), timeout=2.0) as conn:
    conn.settimeout(2.0)
    data = conn.recv(128).decode("ascii").strip()

print(data)
PY_HOST
    )"; then
        tc06_infra_error 'El host no pudo conectarse a su servidor de control.'
    fi

    [[ "$host_output" == "LOGOS_TC06_HOST_OK" ]] ||
        tc06_infra_error 'El control positivo devolvió una respuesta inesperada.'

    printf '%s\n' '[+] Control positivo: el host alcanzó su servidor TCP.'

    # El root de Bubblewrap es nuevo; /usr se expone de solo lectura.
    # Únicamente se comparte el cliente de prueba, no el servidor ni el host.
    bwrap_args=(
        --unshare-user
        --unshare-net
        --die-with-parent
        --new-session
        --clearenv
        --setenv LC_ALL C
        --setenv PATH /usr/bin
        --setenv PYTHONDONTWRITEBYTECODE 1
        --dir /usr
        --ro-bind /usr /usr
        --symlink usr/lib /lib
        --symlink usr/lib /lib64
        --dir /tmp
        --dir /workspace
        --ro-bind "$TC06_ROOT/client.py" /workspace/client.py
    )

    # Pre-vuelo: comprobar que el sandbox arranca con el namespace de red.
    printf '%s\n' '[+] Pre-vuelo: ejecutando Python dentro del sandbox.'

    if smoke_output="$(
        "$bwrap_bin" "${bwrap_args[@]}" -- \
            /usr/bin/python3 -I -S -c \
            'print("LOGOS_TC06_SMOKE_OK")' \
            2>"$TC06_ROOT/smoke.stderr"
    )"; then
        smoke_rc=0
    else
        smoke_rc=$?
    fi

    if [[ "$smoke_rc" -ne 0 ||
          "$smoke_output" != "LOGOS_TC06_SMOKE_OK" ||
          -s "$TC06_ROOT/smoke.stderr" ]]; then
        [[ ! -s "$TC06_ROOT/smoke.stderr" ]] ||
            cat "$TC06_ROOT/smoke.stderr" >&2
        tc06_infra_error 'El pre-vuelo no pudo certificar el arranque.'
    fi

    printf '%s\n' '[+] Pre-vuelo superado.'

    # TC-06: intentar conectar al loopback del host desde la red aislada.
    if net_output="$(
        "$bwrap_bin" "${bwrap_args[@]}" -- \
            /usr/bin/python3 -I -S /workspace/client.py "$port" \
            2>"$TC06_ROOT/network.stderr"
    )"; then
        net_rc=0
    else
        net_rc=$?
    fi

    # El control positivo debe seguir vivo: de lo contrario, resultado ambiguo.
    kill -0 "$TC06_SERVER_PID" 2>/dev/null ||
        tc06_infra_error 'El servidor de control terminó durante la prueba.'

    # Control positivo posterior: el servidor debe seguir respondiendo.
    if ! host_output="$(
        /usr/bin/python3 -S - "$port" <<'PY_HOST_POST'
import socket
import sys

port = int(sys.argv[1])
with socket.create_connection(("127.0.0.1", port), timeout=2.0) as conn:
    conn.settimeout(2.0)
    data = conn.recv(128).decode("ascii").strip()

print(data)
PY_HOST_POST
    )"; then
        tc06_infra_error 'El servidor no respondió al control positivo posterior.'
    fi

    [[ "$host_output" == "LOGOS_TC06_HOST_OK" ]] ||
        tc06_infra_error 'El control positivo posterior devolvió una respuesta inesperada.'

    printf '%s\\n' '[+] Control positivo posterior: el servidor sigue respondiendo.'

    if [[ "$net_rc" -eq 0 && "$net_output" == BLOCKED:* ]]; then
        printf '[+] Aislamiento observado: %s\n' "$net_output"
        printf '%s\n' \
          '=== TC-06: SUPERADA PARA ESTE SERVIDOR Y PERFIL ==='
        return 0
    fi

    if [[ "$net_rc" -eq 41 && "$net_output" == REACHED:* ]]; then
        printf '%s\n' \
          '[FALLO_CONTENCION] El sandbox alcanzó el servidor del host.'
        return 1
    fi

    printf '%s\n' \
      '[RESULTADO_NO_ATRIBUIBLE] La prueba no produjo el bloqueo esperado.' >&2
    printf 'Código del cliente: %s\nSalida: %s\n' \
      "$net_rc" "$net_output" >&2

    [[ ! -s "$TC06_ROOT/network.stderr" ]] ||
        cat "$TC06_ROOT/network.stderr" >&2

    return 2
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    tc06_main "$@"
else
    printf '%s\n' 'TC-06 cargado como texto/source; no se ejecutó.'
fi
