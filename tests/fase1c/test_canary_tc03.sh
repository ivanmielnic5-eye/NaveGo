#!/usr/bin/env bash
# LOGOS - Fase 1C / TC-03 / candidata v7
# Canario inocuo: acceso al archivo no expuesto desde Bubblewrap.
# No valida TC-06 (red) ni aislamiento universal del host.

# La carga mediante source o el pegado del contenido no inicia la prueba.
TC03_TEST_ROOT=""

tc03_remove_temp() {
    [[ -z "${TC03_TEST_ROOT:-}" ]] && return 0

    case "$TC03_TEST_ROOT" in
        /tmp/logos_tc03.*) ;;
        *)
            printf '%s\n' '[ERROR_LIMPIEZA] Ruta temporal no autorizada.' >&2
            return 1
            ;;
    esac

    if [[ -L "$TC03_TEST_ROOT" ]]; then
        printf '%s\n' '[ERROR_LIMPIEZA] La ruta temporal es un enlace simbólico.' >&2
        return 1
    fi

    if [[ ! -e "$TC03_TEST_ROOT" ]]; then
        TC03_TEST_ROOT=""
        return 0
    fi

    if [[ ! -d "$TC03_TEST_ROOT" ]]; then
        printf '%s\n' '[ERROR_LIMPIEZA] La ruta dejó de ser un directorio.' >&2
        return 1
    fi

    if rm -rf -- "$TC03_TEST_ROOT"; then
        TC03_TEST_ROOT=""
        return 0
    fi
    return 1
}

tc03_on_exit() {
    local rc=$?
    trap - EXIT
    if ! tc03_remove_temp; then
        printf '%s\n' '[ERROR_LIMPIEZA] No se pudo confirmar la limpieza.' >&2
        [[ "$rc" -ne 0 ]] || rc=3
    fi
    exit "$rc"
}

tc03_infra_error() {
    printf '[ERROR_INFRAESTRUCTURA] %s\n' "$*" >&2
    exit 2
}

tc03_main() {
    set -Eeuo pipefail
    umask 077
    trap tc03_on_exit EXIT
    trap 'exit 129' HUP
    trap 'exit 130' INT
    trap 'exit 143' TERM

    local cmd bwrap_bin test_result=2
    local canary_path control_dir control_path canary_token control_token
    local hash_line hash_initial hash_final smoke_output smoke_exit
    local canary_output canary_exit
    local -a bwrap_args

    for cmd in bwrap sha256sum od tr grep mktemp rm mkdir chmod cat; do
        command -v "$cmd" >/dev/null 2>&1 ||
            tc03_infra_error "Falta la herramienta requerida: $cmd"
    done

    [[ -x /usr/bin/cat ]] ||
        tc03_infra_error 'No existe /usr/bin/cat ejecutable.'
    bwrap_bin="$(command -v bwrap)"

    TC03_TEST_ROOT="$(mktemp -d /tmp/logos_tc03.XXXXXX)" ||
        tc03_infra_error 'No se pudo crear el directorio privado.'
    chmod 700 -- "$TC03_TEST_ROOT" ||
        tc03_infra_error 'No se pudieron fijar permisos.'

    control_dir="$TC03_TEST_ROOT/control"
    control_path="$control_dir/control.txt"
    canary_path="$TC03_TEST_ROOT/host_canary.txt"

    mkdir -m 700 -- "$control_dir" ||
        tc03_infra_error 'No se pudo crear el directorio de control.'

    canary_token="LOGOS_CANARY_$(od -An -N16 -tx1 /dev/urandom | tr -d '[:space:]')"
    control_token="LOGOS_CONTROL_$(od -An -N16 -tx1 /dev/urandom | tr -d '[:space:]')"

    [[ "${#canary_token}" -eq 45 && "${#control_token}" -eq 46 ]] ||
        tc03_infra_error 'Longitud inesperada de token aleatorio.'

    printf '%s\n' "$canary_token" > "$canary_path" ||
        tc03_infra_error 'No se pudo crear el canario.'
    printf '%s\n' "$control_token" > "$control_path" ||
        tc03_infra_error 'No se pudo crear el archivo de control.'
    chmod 600 -- "$canary_path" "$control_path" ||
        tc03_infra_error 'No se pudieron restringir los permisos.'

    hash_line="$(sha256sum -- "$canary_path")" ||
        tc03_infra_error 'No se pudo calcular el hash inicial.'
    hash_initial="${hash_line%% *}"

    printf '%s\n' '=== LOGOS TC-03 v7: INICIO ==='
    printf '[+] SHA-256 inicial: %s\n' "$hash_initial"

    # Raíz nueva. Se expone /usr en solo lectura y solamente
    # el directorio de control del host. El canario no se monta.
    bwrap_args=(
        --unshare-user
        --die-with-parent
        --new-session
        --clearenv
        --setenv LC_ALL C
        --setenv PATH /usr/bin
        --dir /usr
        --ro-bind /usr /usr
        --symlink usr/lib /lib
        --symlink usr/lib /lib64
        --dir /tmp
        --dir /workspace
        --dir /workspace/control
        --ro-bind "$control_dir" /workspace/control
    )

    # Pre-vuelo: cat debe leer el archivo autorizado.
    printf '%s\n' '[+] Pre-vuelo: comprobando la utilidad dentro del sandbox.'
    set +e
    smoke_output="$("$bwrap_bin" "${bwrap_args[@]}" -- \
        /usr/bin/cat /workspace/control/control.txt \
        2>"$TC03_TEST_ROOT/smoke.stderr")"
    smoke_exit=$?
    set -e

    if [[ "$smoke_exit" -ne 0 ||
          "$smoke_output" != "$control_token" ||
          -s "$TC03_TEST_ROOT/smoke.stderr" ]]; then
        printf '%s\n' \
            '[ERROR_INFRAESTRUCTURA] Pre-vuelo fallido; TC-03 no se evalúa.' >&2
        [[ ! -s "$TC03_TEST_ROOT/smoke.stderr" ]] ||
            cat -- "$TC03_TEST_ROOT/smoke.stderr" >&2
        test_result=2
    else
        printf '%s\n' '[+] Pre-vuelo superado.'
        printf '%s\n' '[+] Intentando leer el canario no expuesto.'

        set +e
        canary_output="$("$bwrap_bin" "${bwrap_args[@]}" -- \
            /usr/bin/cat "$canary_path" \
            2>"$TC03_TEST_ROOT/canary.stderr")"
        canary_exit=$?
        set -e

        if [[ "$canary_exit" -eq 0 ]]; then
            printf '%s\n' \
                '[FALLO_CONTENCION] El intento de lectura terminó con éxito.'
            test_result=1
        elif [[ -n "$canary_output" ]]; then
            printf '%s\n' \
                '[FALLO_CONTENCION] Hubo salida pese al error de lectura.'
            test_result=1
        elif grep -Fq -- "$canary_path: No such file or directory" \
                "$TC03_TEST_ROOT/canary.stderr" ||
             grep -Fq -- "$canary_path: Permission denied" \
                "$TC03_TEST_ROOT/canary.stderr"; then
            printf '%s\n' '[+] Rechazo de lectura observado en la ruta del canario.'
            test_result=0
        elif grep -q '^bwrap:' "$TC03_TEST_ROOT/canary.stderr"; then
            printf '%s\n' \
                '[ERROR_INFRAESTRUCTURA] Bubblewrap falló durante el intento.' >&2
            cat -- "$TC03_TEST_ROOT/canary.stderr" >&2
            test_result=2
        else
            printf '%s\n' \
                '[RESULTADO_NO_ATRIBUIBLE] Error distinto del esperado.' >&2
            cat -- "$TC03_TEST_ROOT/canary.stderr" >&2
            test_result=2
        fi
    fi

    # Integridad en el host, incluso si hubo un error previo.
    if [[ ! -f "$canary_path" ]]; then
        printf '%s\n' '[FALLO_INTEGRIDAD] El canario desapareció.' >&2
        test_result=1
    elif ! hash_line="$(sha256sum -- "$canary_path")"; then
        printf '%s\n' '[ERROR_INFRAESTRUCTURA] Falló el hash final.' >&2
        [[ "$test_result" -eq 1 ]] || test_result=2
    else
        hash_final="${hash_line%% *}"
        if [[ "$hash_initial" != "$hash_final" ]]; then
            printf '%s\n' '[FALLO_INTEGRIDAD] El hash cambió.' >&2
            test_result=1
        else
            printf '%s\n' '[+] Hash inicial y final idénticos.'
        fi
    fi

    # Limpiar antes del dictamen: una limpieza fallida nunca cuenta como éxito.
    if ! tc03_remove_temp; then
        printf '%s\n' '[ERROR_LIMPIEZA] No se pudo confirmar la limpieza.' >&2
        test_result=3
    fi
    trap - EXIT HUP INT TERM

    case "$test_result" in
        0)
            printf '%s\n' '=== TC-03: SUPERADA PARA ESTE CANARIO Y PERFIL ==='
            return 0
            ;;
        1)
            printf '%s\n' '=== TC-03: FALLO DE CONTENCIÓN O INTEGRIDAD ==='
            return 1
            ;;
        3)
            printf '%s\n' '=== TC-03: LIMPIEZA FALLIDA; RESULTADO NO CERTIFICABLE ==='
            return 3
            ;;
        *)
            printf '%s\n' '=== TC-03: INCONCLUSA; NO SE CERTIFICA CONTENCIÓN ==='
            return 2
            ;;
    esac
}

# Solo corre como programa independiente. Pegar o cargar este texto no ejecuta TC-03.
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    tc03_main "$@"
    tc03_rc=$?
    exit "$tc03_rc"
else
    printf '%s\n' 'TC-03 v7: cargada como texto/source; prueba no ejecutada.'
fi
