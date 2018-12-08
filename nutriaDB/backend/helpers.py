# -*- coding: utf-8 -*-
import re


def split_name(name_str):
    mao = re.match(
        "^\s*([\w \-\(\[\{\}\]\)\#\%\!\.\,\;\*]+)\s*:\s*([\w \-\(\[\{\}\]\)\#\%\!\.\,\;\*]+)\s*$",
        name_str)
    category_str = mao.groups()[0]
    name_addition = mao.groups()[1]
    return category_str, name_addition
