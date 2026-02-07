from django.core.exceptions import ValidationError
from itertools import cycle
import re

def validar_rut(value):
    """
    Valida que el RUT chileno sea correcto usando el algoritmo Módulo 11.
    Acepta formatos: 12.345.678-9, 12345678-9, 123456789
    """
    rut = str(value).upper().replace("-", "").replace(".", "")

    # 1. Validación de formato básico (Largo y caracteres)
    if not re.match(r'^\d{7,8}[0-9K]$', rut):
        raise ValidationError("El formato del RUT no es válido.")

    aux = rut[:-1]
    dv = rut[-1]

    # 2. Algoritmo Módulo 11
    revertido = map(int, reversed(str(aux)))
    factors = cycle(range(2, 8))
    s = sum(d * f for d, f in zip(revertido, factors))
    res = (-s) % 11

    if res == 10:
        dv_calc = "K"
    else:
        dv_calc = str(res)

    if dv != dv_calc:
        raise ValidationError("El RUT ingresado es incorrecto.")