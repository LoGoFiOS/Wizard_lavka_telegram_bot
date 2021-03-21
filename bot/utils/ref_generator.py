import string

alphabet = '0123456789'
alphabet_string = string.ascii_uppercase
alphabet += alphabet_string
base = 36


def get_ref(id: int) -> str:
    result = ""
    while id > 0:
        result += alphabet[id % base]
        id //= base

    return result[::-1]