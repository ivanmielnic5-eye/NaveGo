#!/usr/bin/env bash
set -u

REL="$(awk -F: '$1 == "0" {print $3}' /proc/self/cgroup)"
CG="/sys/fs/cgroup${REL}"

if [[ ! -d "$CG" ]]; then
    echo "TC11_ERROR: cgroup no encontrado"
    exit 20
fi

getval() {
    if [[ -r "$CG/$1" ]]; then
        cat "$CG/$1"
    else
        printf 'NA'
    fi
}

HIGH="$(getval memory.high)"
MAX="$(getval memory.max)"
SWAPMAX="$(getval memory.swap.max)"
PIDSMAX="$(getval pids.max)"

printf 'Cgroup: %s\n' "$CG"
printf 'memory.high=%s\n' "$HIGH"
printf 'memory.max=%s\n' "$MAX"
printf 'memory.swap.max=%s\n' "$SWAPMAX"
printf 'pids.max=%s\n' "$PIDSMAX"

if [[ "$HIGH" != "max" || "$MAX" != "100663296" || "$SWAPMAX" != "0" || "$PIDSMAX" != "16" ]]; then
    echo "TC11_ERROR: los límites efectivos no coinciden"
    exit 21
fi

if [[ -r "$CG/memory.events.local" ]]; then
    EVENTS="$CG/memory.events.local"
elif [[ -r "$CG/memory.events" ]]; then
    EVENTS="$CG/memory.events"
else
    echo "TC11_ERROR: no se pueden leer los eventos de memoria"
    exit 22
fi

eventval() {
    awk -v k="$1" '$1 == k {print $2; found=1} END {if (!found) print 0}' "$EVENTS"
}

OOM0="$(eventval oom_kill)"
MAX0="$(eventval max)"
OOMEV0="$(eventval oom)"

echo "Intentando asignar hasta 192 MiB; techo de memoria: 96 MiB."
set +e
timeout --signal=TERM --kill-after=2s 12s python3 -c 'import time; blocks=[bytearray(4*1024*1024) for _ in range(48)]; [b.__setitem__(p,1) for b in blocks for p in range(0,len(b),4096)]; print("WORKLOAD_COMPLETO: 192 MiB asignados",flush=True); time.sleep(0.2)'
CHILD_RC=$?
set -u

OOM1="$(eventval oom_kill)"
MAX1="$(eventval max)"
OOMEV1="$(eventval oom)"
SWAPCURRENT="$(getval memory.swap.current)"

DOOM=$((OOM1 - OOM0))
DMAX=$((MAX1 - MAX0))
DOOMEV=$((OOMEV1 - OOMEV0))

printf 'Proceso de carga: código %s\n' "$CHILD_RC"
printf 'Eventos max: antes=%s después=%s delta=%s\n' "$MAX0" "$MAX1" "$DMAX"
printf 'Eventos oom: antes=%s después=%s delta=%s\n' "$OOMEV0" "$OOMEV1" "$DOOMEV"
printf 'Eventos oom_kill: antes=%s después=%s delta=%s\n' "$OOM0" "$OOM1" "$DOOM"
printf 'memory.swap.current final=%s\n' "$SWAPCURRENT"

if (( DOOM > 0 && DMAX > 0 )) && [[ "$SWAPCURRENT" == "0" ]]; then
    echo "TC11_RESULT=PASS"
    exit 0
else
    echo "TC11_RESULT=NO_CONCLUYENTE"
    exit 30
fi
