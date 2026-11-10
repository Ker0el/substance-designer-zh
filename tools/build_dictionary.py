#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Merge manual translations and pattern rules into the plugin dictionary."""
import argparse
import json
import os
import re
from collections import OrderedDict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RULES = [
    (re.compile(r"^Input (\d+)$"), r"输入 \1"),
    (re.compile(r"^Output (\d+)$"), r"输出 \1"),
    (re.compile(r"^Material ?(\d+)$"), r"材质 \1"),
    (re.compile(r"^Value (\d+)$"), r"数值 \1"),
    (re.compile(r"^Pattern input(?: (\d+))?$"), lambda m: "图案输入" + (f" {m.group(1)}" if m.group(1) else "")),
    (re.compile(r"^Pattern (\d+)$"), r"图案 \1"),
    (re.compile(r"^Point (\d+)$"), r"点 \1"),
    (re.compile(r"^Spline (\d+)$"), r"样条 \1"),
    (re.compile(r"^SDF (\d+)$"), r"SDF \1"),
    (re.compile(r"^spline_(\d+)$"), r"样条 \1"),
    (re.compile(r"^Range: \[(.*)\]$"), r"范围：[\1]"),
    (re.compile(r"^Cells (\d+)$"), r"细胞 \1"),
    (re.compile(r"^Clouds (\d+)$"), r"云 \1"),
    (re.compile(r"^Crystals? (\d+)$"), r"水晶 \1"),
    (re.compile(r"^Fractal sum (\d+)$"), r"分形叠加 \1"),
    (re.compile(r"^Fractal Sum (\d+)$"), r"分形叠加 \1"),
    (re.compile(r"^Gaussian spots (\d+)$"), r"高斯斑点 \1"),
    (re.compile(r"^Dirt (\d+)$"), r"污垢 \1"),
    (re.compile(r"^Dir (\d+)$"), r"方向 \1"),
    (re.compile(r"^Directional noise (\d+)$"), r"定向噪声 \1"),
    (re.compile(r"^Splatter data (\d+)$"), r"散布数据 \1"),
    (re.compile(r"^Spline coords #(\d+)$"), r"样条坐标 #\1"),
    (re.compile(r"^Spline data #(\d+)$"), r"样条数据 #\1"),
    (re.compile(r"^Spline amount #(\d+)$"), r"样条数量 #\1"),
    (re.compile(r"^Preview #(\d+)$"), r"预览 #\1"),
    (re.compile(r"^Tiles (\d+) Color$"), r"瓷砖 \1 颜色"),
    (re.compile(r"^Material (\d+) color$"), r"材质 \1 颜色"),
    (re.compile(r"^Material (\d+) (diffuse|specular|height) (black|red|green|blue)$"),
     lambda m: f"材质 {m.group(1)} {COMPONENTS[m.group(2)]} {COMPONENTS[m.group(3)]}"),
    (re.compile(r"^Grunge map (\d+)$"), r"脏迹贴图 \1"),
    (re.compile(r"^P(\d+) properties$"), r"P\1 属性"),
    (re.compile(r"^Pattern input #(\d+)$"), r"图案输入 #\1"),
    (re.compile(r"^Input ([XYZ])$"), r"输入 \1"),
    (re.compile(r"^Random offset ([XYZ])$"), r"随机偏移 \1"),
    (re.compile(r"^Enable material #(\d+)$"), r"启用材质 #\1"),
    (re.compile(r"^Material #(\d+)$"), r"材质 #\1"),
    (re.compile(r"^Float(\d) value$"), r"浮点\1 值"),
    (re.compile(r"^Integer(\d) value$"), r"整数\1 值"),
    (re.compile(r"^Equality (Float\d|boolean)$"), r"等于 \1"),
    (re.compile(r"^Not equal (Float\d|boolean)$"), r"不等于 \1"),
    (re.compile(r"^Merge Float(\d)$"), r"合并 Float\1"),
    (re.compile(r"^Distance Float(\d)$"), r"距离 Float\1"),
    (re.compile(r"^Length Float(\d)$"), r"长度 Float\1"),
    (re.compile(r"^Base color (\d+) inputs$"), r"基础颜色 \1 输入"),
    (re.compile(r"^Mesh material blender (\d+) inputs$"), r"网格材质混合器 \1 输入"),
    (re.compile(r"^Noise upscale (\d+)$"), r"噪声放大 \1"),
    (re.compile(r"^Material (\d+) (diffuse|specular|height) (yellow|magenta|cyan)$"),
     lambda m: f"材质 {m.group(1)} {COMPONENTS[m.group(2)]} {COMPONENTS[m.group(3)]}"),
    (re.compile(r"^Input (\d+) \((Color|Grayscale)\)$"),
     lambda m: f"输入 {m.group(1)}（{'颜色' if m.group(2) == 'Color' else '灰度'}）"),
    (re.compile(r"^Color #(\d+)$"), r"颜色 #\1"),
    (re.compile(r"^(\d+) samples$"), r"\1 采样"),
    (re.compile(r"^([XYZ]) only$"), r"仅 \1"),
    (re.compile(r"^([XYZ]) up$"), r"\1 向上"),
    (re.compile(r"^Size ([XY])$"), r"\1 大小"),
    (re.compile(r"^Mirror axis ([XY])$"), r"镜像轴 \1"),
    (re.compile(r"^Switch (Float|Integer)(\d) (\d+) inputs$"),
     lambda m: f"切换 {m.group(1)}{m.group(2)} {m.group(3)} 输入"),
    (re.compile(r"^Average Float(\d)$"), lambda m: f"平均值 Float{m.group(1)}"),
    (re.compile(r"^Normalize (Vec|Float)(\d)$"),
     lambda m: f"归一化 {m.group(1)}{m.group(2)}"),
    (re.compile(r"^Saturate (Float|Vec)(\d)$"),
     lambda m: f"饱和 {m.group(1)}{m.group(2)}"),
    (re.compile(r"^Truncate Float(\d)$"), lambda m: f"截断 Float{m.group(1)}"),
    (re.compile(r"^Round Float(\d)$"), lambda m: f"四舍五入 Float{m.group(1)}"),
    (re.compile(r"^Hash (\d+)$"), r"哈希 \1"),
    (re.compile(r"^Fur (\d+) \(Legacy\)$"), r"毛发 \1（旧版）"),
    (re.compile(r"^Gaussian (\d+) \(Legacy\)$"), r"高斯 \1（旧版）"),
    (re.compile(r"^Gaussian spots (\d+) \(Legacy\)$"), r"高斯斑点 \1（旧版）"),
    (re.compile(r"^Gauss spots (\d+) \(Legacy\)$"), r"高斯斑点 \1（旧版）"),
    (re.compile(r"^The grayscale image input #(\d+)\.$"), r"第 \1 个灰度图像输入。"),
    (re.compile(r"^The color image input #(\d+)\.$"), r"第 \1 个颜色图像输入。"),
    (re.compile(r"^The output grayscale grid atlas\.$"), "输出的灰度网格图集。"),
]

EASE = {
    "sine": "正弦", "quad": "二次", "cubic": "三次", "quart": "四次",
    "quint": "五次", "expo": "指数", "circ": "圆形",
}


def ease_rule(source):
    match = re.match(r"^Ease in out (sine|quad|cubic|quart|quint|expo|circ)$", source)
    if match:
        return f"缓入缓出{EASE[match.group(1)]}"
    match = re.match(r"^Ease in (sine|quad|cubic|quart|quint|expo|circ)$", source)
    if match:
        return f"缓入{EASE[match.group(1)]}"
    match = re.match(r"^Ease out (sine|quad|cubic|quart|quint|expo|circ)$", source)
    if match:
        return f"缓出{EASE[match.group(1)]}"
    return None

COMPONENTS = {    "color": "颜色",
    "diffuse": "漫反射",
    "specular": "高光",
    "height": "高度",
    "black": "黑",
    "red": "红",
    "green": "绿",
    "blue": "蓝",
    "yellow": "黄",
    "magenta": "品红",
    "cyan": "青",
    "levels": "级别",
    "intensity": "强度",
    "mask": "遮罩",
    "input": "输入",
    "output": "输出",
    "multiplier": "倍增",
    "random": "随机",
    "scale": "缩放",
    "rotation": "旋转",
    "position": "位置",
    "offset": "偏移",
    "amount": "数量",
    "opacity": "不透明度",
    "format": "格式",
    "mode": "模式",
    "size": "大小",
    "angle": "角度",
}

WORD_GLOSSARY = {
    "grunge": "脏迹", "map": "贴图", "maps": "贴图", "leaks": "渗漏",
    "leaky": "流", "paint": "油漆", "concrete": "混凝土", "damas": "大马士革",
    "galvanic": "电镀", "large": "大", "small": "小", "medium": "中",
    "rough": "粗糙", "dirty": "污浊", "rust": "锈", "fine": "细",
    "scratches": "划痕", "scratch": "划痕", "shavings": "碎屑",
    "splashes": "飞溅", "dusty": "灰尘", "spots": "斑点", "spot": "斑点",
    "liquid": "液体", "moisture": "湿气", "noise": "噪声", "noises": "噪声",
    "plasma": "等离子", "waveform": "波形", "caustics": "焦散",
    "voronoi": "沃罗诺伊", "fractal": "分形", "white": "白", "black": "黑",
    "perlin": "柏林", "worley": "沃利", "cells": "细胞", "cell": "细胞",
    "clouds": "云", "cloud": "云", "crystals": "水晶", "crystal": "水晶",
    "dirt": "污垢", "gradient": "渐变", "fur": "毛发", "fibers": "纤维",
    "fiber": "纤维", "messy": "杂乱", "cracks": "裂纹", "crack": "裂纹",
    "moss": "苔藓", "ice": "冰", "snow": "雪", "water": "水", "rock": "岩石",
    "metal": "金属", "metallic": "金属", "leather": "皮革", "fabric": "布料",
    "brick": "砖", "bricks": "砖", "tiles": "瓷砖", "tile": "瓷砖",
    "peeling": "剥落", "verdigris": "铜绿", "drips": "滴落", "dust": "灰尘",
    "sand": "沙", "stone": "石头", "wood": "木材", "marble": "大理石",
    "granite": "花岗岩", "mosaic": "马赛克", "pattern": "图案",
    "patterns": "图案", "line": "线", "lines": "线条", "wave": "波",
    "waves": "波浪", "ring": "环", "rings": "环", "spiral": "螺旋",
    "scatter": "散布", "splatter": "散布", "shape": "形状",
    "shapes": "形状", "mask": "遮罩", "masks": "遮罩", "normal": "法线",
    "height": "高度", "color": "颜色", "base": "基础", "ambient": "环境",
    "occlusion": "遮蔽", "specular": "高光", "diffuse": "漫反射",
    "roughness": "粗糙度", "metallic": "金属度", "glossiness": "光泽度",
    "opacity": "不透明度", "emissive": "自发光", "displacement": "置换",
    "edge": "边缘", "edges": "边缘", "wear": "磨损", "worn": "磨损",
    "weathering": "风化", "old": "旧", "new": "新", "light": "光",
    "dark": "暗", "soft": "柔", "hard": "硬", "sharp": "锐",
    "smooth": "平滑", "blur": "模糊", "blurs": "模糊", "anisotropic": "各向异性",
    "directional": "定向", "blue": "蓝", "fast": "快速", "bnw": "黑白",
    "red": "红", "green": "绿", "thick": "厚", "thin": "薄", "high": "高",
    "low": "低", "deep": "深", "flat": "平", "round": "圆", "square": "方",
    "hex": "六边形", "triangle": "三角形", "cone": "圆锥", "sphere": "球体",
    "torus": "圆环", "plane": "平面", "box": "盒", "cylinder": "圆柱",
    "pyramid": "金字塔", "prism": "棱柱", "cliff": "悬崖", "cave": "洞穴",
    "ground": "地面", "floor": "地面", "wall": "墙", "surface": "表面",
    "material": "材质", "materials": "材质", "filter": "滤镜",
    "filters": "滤镜", "generator": "生成器", "generators": "生成器",
    "cracks": "裂纹", "scrape": "刮痕", "scrapes": "刮痕", "peel": "剥落",
    "dents": "凹痕", "bumps": "凸起", "pits": "凹坑", "stains": "污渍",
    "streaks": "条纹", "smudges": "污痕", "grime": "污垢", "soot": "烟灰",
    "brush": "笔刷", "brushes": "笔刷", "alpha": "Alpha", "alphas": "Alpha",
    "preset": "预设", "presets": "预设", "intensity": "强度",
    "random": "随机", "scale": "缩放", "material": "材质",
    "input": "输入", "fabric": "布料", "pattern": "图案",
    "roughness": "粗糙度", "offset": "偏移", "legacy": "旧版",
    "shape": "形状", "normal": "法线", "mask": "遮罩", "spline": "样条",
    "size": "大小", "amount": "数量", "height": "高度", "paint": "油漆",
    "position": "位置", "mode": "模式", "rotation": "旋转",
    "grayscale": "灰度", "map": "贴图", "border": "边框",
    "variation": "变化", "width": "宽度", "custom": "自定义",
    "gradient": "渐变", "density": "密度", "circle": "圆形",
    "stitch": "针脚", "italic": "斜体", "bold": "粗体", "metallic": "金属",
    "wood": "木材", "use": "使用", "plastic": "塑料", "dirt": "污垢",
    "edges": "边缘", "line": "线", "base": "基础", "light": "光",
    "angle": "角度", "contrast": "对比度", "start": "起点",
    "specular": "高光", "pbr": "PBR", "metal": "金属", "cross": "十字",
    "end": "终点", "sign": "标记", "thickness": "厚度", "leather": "皮革",
    "hexagon": "六边形", "skin": "皮肤", "triangle": "三角形",
    "distance": "距离", "soft": "柔", "invert": "反转", "concept": "概念",
    "warp": "扭曲", "square": "方形", "round": "圆形", "user": "用户",
    "noise": "噪声", "from": "从", "corner": "角落",
    "opacity": "不透明度", "spread": "扩散", "details": "细节",
    "paper": "纸张", "fibers": "纤维", "small": "小", "mono": "单色",
    "enable": "启用", "level": "级别", "range": "范围",
    "vertical": "垂直", "steel": "钢", "strokes": "笔触", "point": "点",
    "multiplier": "倍增", "arrow": "箭头", "double": "双",
    "cracks": "裂纹", "in": "在", "length": "长度", "number": "编号",
    "center": "中心", "flip": "翻转", "type": "类型",
    "scratches": "划痕", "image": "图像", "watercolor": "水彩",
    "deprecated": "已弃用", "diffuse": "漫反射", "cut": "切割",
    "bevel": "倒角", "blur": "模糊", "dots": "点", "left": "左",
    "horizontal": "水平", "rough": "粗糙", "top": "顶部", "right": "右",
    "split": "分离", "smoothness": "平滑度", "blending": "混合",
    "mesh": "网格",
}
LATIN_KEEP = {
    "3d", "2d", "uv", "uvs", "pbr", "sdf", "ao", "rgb", "rgba", "hsl",
    "hsv", "hcl", "hsi", "f0", "ior", "ibd", "ibl", "hdri", "gpu", "id",
    "mip", "mips", "fxaa", "aces", "agx", "hejl", "rt", "svg", "sbs",
}


def compositional(source):
    """Translate short asset-name phrases word by word; skip sentences."""
    if any(ch in source for ch in ".,:;!?()[]{}\"'") or len(source) > 48:
        return None
    tokens = source.split()
    if not tokens or len(tokens) > 6:
        return None
    parts = []
    for token in tokens:
        low = token.lower()
        if token.isdigit():
            parts.append(token)
        elif low in LATIN_KEEP:
            parts.append(token)
        elif low in WORD_GLOSSARY:
            parts.append(WORD_GLOSSARY[low])
        else:
            return None
    # Chinese output: no spaces between Chinese words; keep a space before digits.
    out = ""
    for part in parts:
        if part.isdigit() or (part and part[0].isascii() and part[0].isalnum()):
            if out:
                out += " "
        out += part
    return out or None


def translate_candidate(source, manual, depth=0):
    if source in manual:
        return manual[source]
    if source.lower() in COMPONENTS and depth > 0:
        return COMPONENTS[source.lower()]
    eased = ease_rule(source)
    if eased:
        return eased
    for pattern, replacement in RULES:
        match = pattern.match(source)
        if match:
            return replacement(match) if callable(replacement) else match.expand(replacement)
    composed = compositional(source)
    if composed:
        return composed
    if depth < 2:
        main_prefix = re.match(r"^\((?:Main|主要)\)\s*(.+)$", source)
        if main_prefix:
            rest = translate_candidate(main_prefix.group(1), manual, depth + 1)
            if rest:
                return f"（主要）{rest}"
        legacy = re.match(r"^(.+) \(Legacy\)$", source)
        if legacy:
            rest = translate_candidate(legacy.group(1), manual, depth + 1)
            if rest:
                return f"{rest}（旧版）"
        deprecated = re.match(r"^(.+) \(Deprecated\)$", source)
        if deprecated:
            rest = translate_candidate(deprecated.group(1), manual, depth + 1)
            if rest:
                return f"{rest}（已弃用）"
    if depth >= 3:
        return None
    match = re.match(r"^#(\d+) (.+)$", source)
    if match:
        rest = translate_candidate(match.group(2), manual, depth + 1)
        if rest:
            return f"#{match.group(1)} {rest}"
    match = re.match(r"^Material (\d+) (.+)$", source)
    if match:
        rest = translate_candidate(match.group(2), manual, depth + 1)
        if rest:
            return f"材质 {match.group(1)} {rest}"
    match = re.match(r"^(.+) (\d+)$", source)
    if match and depth < 2:
        rest = translate_candidate(match.group(1), manual, depth + 1)
        if rest:
            return f"{rest} {match.group(2)}"
    return None


def load_manual(directory):
    merged = OrderedDict()
    for name in sorted(os.listdir(directory)):
        if not re.match(r"^manual_.*_zh\.json$", name):
            continue
        path = os.path.join(directory, name)
        with open(path, encoding="utf-8-sig") as handle:
            data = json.load(handle)
        entries = data.get("translations", data)
        for source, target in entries.items():
            if source.strip() and isinstance(target, str) and target.strip():
                merged[source] = target
    return merged


def apply_rules(source):
    for pattern, replacement in RULES:
        match = pattern.match(source)
        if match:
            return replacement(match) if callable(replacement) else match.expand(replacement)
    return None


def format_target(text):
    """在拉丁缩写与中文之间补空格，避免出现 Alpha随机/SVG遮罩 这种排版。"""
    text = re.sub(r"(?<=[A-Za-z0-9])(?=[一-鿿])", " ", text)
    text = re.sub(r"(?<=[一-鿿])(?=[A-Za-z0-9])", " ", text)
    return text


def write_package(name, entries):
    payload = {
        "$schema": "xingkong-translation-v1",
        "id": name,
        "language": "zh-CN",
        "description": "星空汉化词库",
        "translations": {k: format_target(v) for k, v in entries.items()},
    }
    with open(os.path.join(OUTPUT_DIR, f"{name}_zh.json"), "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=1)


def main():
    global OUTPUT_DIR
    parser = argparse.ArgumentParser()
    parser.add_argument("--translations", default=os.path.join(ROOT, "translations"))
    parser.add_argument("--inventory",
                        default=os.path.join(ROOT, "translations", "inventory_all.json"))
    parser.add_argument("--output", default=os.path.join(ROOT, "source", "translations"))
    args = parser.parse_args()
    OUTPUT_DIR = args.output
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    manual_all = load_manual(args.translations)
    manual_ui = {}
    ui_path = os.path.join(args.translations, "manual_ui_zh.json")
    if os.path.isfile(ui_path):
        with open(ui_path, encoding="utf-8-sig") as handle:
            manual_ui = json.load(handle).get("translations", {})

    candidates = []
    if os.path.isfile(args.inventory):
        with open(args.inventory, encoding="utf-8") as handle:
            candidates = [item[0] for item in json.load(handle)]

    generated = OrderedDict()
    for source in candidates:
        if source in manual_all:
            continue
        target = translate_candidate(source, manual_all)
        if target:
            generated[source] = target

    assets = OrderedDict((k, v) for k, v in manual_all.items() if k not in manual_ui)
    assets.update(generated)

    write_package("ui", manual_ui)
    write_package("assets", assets)
    write_package("control_ids", {})

    covered = len(assets) + len(manual_ui)
    print(f"ui={len(manual_ui)} assets={len(assets)} generated={len(generated)} total={covered}")
    print(f"candidates={len(candidates)} untranslated={max(0, len(candidates) - len(assets))}")
    print(f"output={OUTPUT_DIR}")


if __name__ == "__main__":
    main()
