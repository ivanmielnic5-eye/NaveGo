#!/usr/bin/env python3
"""test_mision_config.py - Tests del hash canonico (F0 bloqueante 2).

Correr:
  cd timonel && python3 test_mision_config.py
"""
from mision_config import hash_canonico


def test_15_igual_15_0():
    assert hash_canonico({"T": 15}) == hash_canonico({"T": 15.0}), \
        "15 y 15.0 deben dar el mismo hash"
    print("OK: 15 == 15.0")


def test_orden_no_importa():
    a = hash_canonico({"a": 1, "b": 2})
    b = hash_canonico({"b": 2, "a": 1})
    assert a == b, "orden de claves no debe afectar el hash"
    print("OK: orden de claves no importa")


def test_valores_distintos_hash_distinto():
    a = hash_canonico({"T": 15.0})
    b = hash_canonico({"T": 20.0})
    assert a != b, "valores distintos deben dar hashes distintos"
    print("OK: valores distintos -> hashes distintos")


def test_bool_no_es_int():
    a = hash_canonico({"flag": True})
    b = hash_canonico({"flag": 1})
    assert a != b, "True y 1 deben dar hashes distintos"
    print("OK: bool != int")


def test_lista_ordenada():
    a = hash_canonico({"lista": [1, 2, 3]})
    b = hash_canonico({"lista": [3, 2, 1]})
    assert a != b, "listas con distinto orden deben dar hashes distintos"
    print("OK: orden de lista importa")


def test_unicode():
    a = hash_canonico({"nombre": "navegacion"})
    b = hash_canonico({"nombre": "navegación"})
    assert a != b, "unicode debe distinguirse"
    print("OK: unicode funciona")


def test_anidado():
    obj1 = {"goal": {"T": 15, "v_max": 0.3}}
    obj2 = {"goal": {"T": 15.0, "v_max": 0.3}}
    assert hash_canonico(obj1) == hash_canonico(obj2), \
        "normalizacion debe ser recursiva"
    print("OK: normalizacion recursiva")


def main():
    tests = [
        test_15_igual_15_0,
        test_orden_no_importa,
        test_valores_distintos_hash_distinto,
        test_bool_no_es_int,
        test_lista_ordenada,
        test_unicode,
        test_anidado,
    ]
    fallos = 0
    for t in tests:
        try:
            t()
        except AssertionError as e:
            print("FALLA: " + t.__name__ + " -> " + str(e))
            fallos += 1
    print()
    if fallos == 0:
        print("TODOS LOS TESTS PASAN (" + str(len(tests)) + ")")
        return 0
    else:
        print(str(fallos) + " TESTS FALLARON")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
