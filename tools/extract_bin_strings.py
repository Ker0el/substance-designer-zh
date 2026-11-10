#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extract printable ASCII / UTF-16 strings from host binaries.

Read-only reconnaissance for the dictionary: nothing is modified.
"""
import argparse
import json
import os
import re
from collections import Counter

ASCII_RE = re.compile(rb"[\x20-\x7e]{3,160}")
UTF16_RE = re.compile(rb"(?:[\x20-\x7e]\x00){3,160}")
BAD = re.compile(
    r"(://|\\\\|\\[A-Za-z]|^[A-Za-z]:|^\.|\.(exe|dll|pyd|dylib|so|h|hpp|cpp|py|json|xml|qml|qss|png|jpg|ttf|otf|ini|log|txt|bin|sbs|sbsar)$)",
    re.IGNORECASE,
)
SYMBOL = re.compile(r"[{}<>\[\]|]|::|@[?]?|^[0-9A-Fa-fxX .:%+\-]+$|^[_$.]")
KEEP = re.compile(r"[A-Za-z]{2,}")


def good(text):
    text = text.strip()
    if not (2 <= len(text) <= 120):
        return False
    if BAD.search(text) or SYMBOL.search(text):
        return False
    if not KEEP.search(text):
        return False
    if text.startswith(("?", "!", "@", "#")):
        return False
    # Reject C/C++ identifier-like strings and dense camelCase symbols.
    if "_" in text and " " not in text:
        return False
    if sum(ch.isupper() for ch in text) > len(text) * 0.8 and len(text) > 6:
        return False
    return True


def scan_file(path, counter):
    try:
        data = open(path, "rb").read()
    except Exception:
        return
    for match in ASCII_RE.finditer(data):
        text = match.group().decode("ascii", "ignore")
        if good(text):
            counter[text] += 1
    for match in UTF16_RE.finditer(data):
        text = match.group().decode("utf-16le", "ignore")
        if good(text):
            counter[text] += 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("targets", nargs="+", help="files or directories")
    parser.add_argument("output")
    args = parser.parse_args()
    counter = Counter()
    files = []
    for target in args.targets:
        if os.path.isdir(target):
            for base, _dirs, names in os.walk(target):
                for name in names:
                    if name.lower().endswith((".exe", ".dll", ".pyd")):
                        files.append(os.path.join(base, name))
        elif os.path.isfile(target):
            files.append(target)
    for path in files:
        scan_file(path, counter)
        print("scanned", os.path.basename(path), len(counter), flush=True)
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(counter.most_common(), handle, ensure_ascii=False, indent=1)
    print(f"files={len(files)} strings={len(counter)} -> {args.output}")


if __name__ == "__main__":
    main()
