# -*- coding: utf-8 -*-
import hashlib
import random
import string


def generate_verification_code(length: int = 6) -> str:
    """
    Genera un codigo de verificacion alfanumerico.
    Mezcla numeros, letras mayusculas y minusculas.
    """
    characters = string.ascii_letters + string.digits
    return "".join(random.choice(characters) for _ in range(length))


def hash_verification_code(code: str) -> str:
    """
    Genera un hash SHA256 del codigo de verificacion.
    """
    return hashlib.sha256(code.encode()).hexdigest()
