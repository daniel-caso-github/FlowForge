import random
import re


def reindent(xml: bytes) -> bytes:
    text = xml.decode("utf-8")
    text = re.sub(r">\s*<", ">\n  <", text)
    return text.encode("utf-8")


def swap_namespace_prefixes(xml: bytes) -> bytes:
    text = xml.decode("utf-8")
    declared = list(dict.fromkeys(re.findall(r"xmlns:([a-zA-Z0-9]+)=", text)))
    for i, prefix in enumerate(declared):
        if prefix == "ff":
            continue
        new_prefix = f"alt{i}"
        text = text.replace(f"<{prefix}:", f"<{new_prefix}:")
        text = text.replace(f"</{prefix}:", f"</{new_prefix}:")
        text = text.replace(f"xmlns:{prefix}=", f"xmlns:{new_prefix}=")
    return text.encode("utf-8")


def degrade(xml: bytes, rng: random.Random) -> bytes:
    result = xml
    if rng.random() < 0.5:
        result = reindent(result)
    if rng.random() < 0.5:
        result = swap_namespace_prefixes(result)
    return result
