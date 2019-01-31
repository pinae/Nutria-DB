# -*- coding: utf-8 -*-


class NoDigitError(ValueError):
    pass


def convert_digits_to_bytes(digits):
    conversion_table = {
        "0": b'\x00',
        "1": b'\x01',
        "2": b'\x02',
        "3": b'\x03',
        "4": b'\x04',
        "5": b'\x05',
        "6": b'\x06',
        "7": b'\x07',
        "8": b'\x08',
        "9": b'\x09',
    }
    byte_string = b""
    for digit in digits:
        try:
            byte_string += conversion_table[digit]
        except KeyError:
            raise NoDigitError(digit)
    return byte_string
