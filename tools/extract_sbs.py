#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extract English UI candidates from Substance Designer .sbs packages.

Outputs a frequency-sorted JSON inventory. Nothing is written back to the host.
"""
import argparse
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter

HAN = re.compile(r"[㐀-䶿一-鿿豈-﫿]")
BAD = re.compile(r"(://|^https?:|\\|/|[{}<>]|%[0-9])")
INTERNAL = {
    "default", "min", "max", "clamp", "step", "slider", "bool", "int", "float",
    "string", "enum", "color", "gradient", "curve", "label0", "label1",
    "label2", "label3", "name", "value", "identifier", "uid", "false", "true",
}


def good(text):
    if not isinstance(text, str):
        return False
    text = text.strip()
    if not (2 <= len(text) <= 80):
        return False
    if text.lower() in INTERNAL:
        return False
    if re.fullmatch(r"[a-z0-9_]+", text):
        return False
    if "_" in text or text.startswith("$") or "[" in text or "]" in text:
        return False
    if " " not in text and re.search(r"[a-z][A-Z]", text):
        return False
    if HAN.search(text) or BAD.search(text):
        return False
    if not re.search(r"[A-Za-z]", text):
        return False
    if re.fullmatch(r"[0-9A-Fa-fxX .:%+\-]+", text):
        return False
    return True


def walk(path, counter):
    try:
        tree = ET.parse(path)
    except Exception:
        return
    for elem in tree.iter():
        tag = elem.tag.rsplit("}", 1)[-1]
        if tag in {"label", "description", "category", "title"}:
            value = elem.get("v")
            if good(value):
                counter[value.strip()] += 1
        elif tag == "value":
            # 下拉选项常编码为 "0;0;Euclidean;1;Manhattan;2;Chebyshev"
            value = elem.get("v")
            if value:
                if ";" in value:
                    for part in value.split(";"):
                        if good(part):
                            counter[part.strip()] += 1
                elif good(value):
                    counter[value.strip()] += 1
        elif tag == "group":
            value = elem.get("v")
            if value:
                for part in value.split("/"):
                    if good(part):
                        counter[part.strip()] += 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", help="resources/packages directory")
    parser.add_argument("output", help="output JSON inventory")
    args = parser.parse_args()

    counter = Counter()
    count = 0
    for root, _dirs, files in os.walk(args.source):
        for name in files:
            if name.lower().endswith(".sbs"):
                count += 1
                walk(os.path.join(root, name), counter)
                if count % 500 == 0:
                    print(f"scanned {count} packages, {len(counter)} candidates", file=sys.stderr)

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(counter.most_common(), handle, ensure_ascii=False, indent=1)
    print(f"packages={count} candidates={len(counter)} -> {args.output}")


if __name__ == "__main__":
    main()
