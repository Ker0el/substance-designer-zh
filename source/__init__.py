# -*- coding: utf-8 -*-
"""星空汉化 · Substance 3D Designer 插件入口垫片。"""


def initializeSDPlugin():
    from .xingkong_zh import initializeSDPlugin as _entry
    return _entry()


def uninitializeSDPlugin():
    from .xingkong_zh import uninitializeSDPlugin as _exit
    return _exit()


def start_plugin():
    return initializeSDPlugin()


def close_plugin():
    return uninitializeSDPlugin()


def reload_plugin():
    close_plugin()
    return start_plugin()
