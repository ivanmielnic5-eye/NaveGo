#!/bin/bash
MODELO="qwen2.5-coder:1.5b"
for p in A:Ap:B A:B:Ap Ap:A:B Ap:B:A B:A:Ap B:Ap:A; do
    ollama stop "$MODELO" >/dev/null 2>&1
    sleep 0.5
    python3 runtime_probe_perm.py "$p"
done
