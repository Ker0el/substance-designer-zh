# -*- coding: utf-8 -*-
"""Standalone UI smoke test for the native engine.

Run with Designer's bundled python.exe so the Qt version matches the host.
Captures the real screen before/after enabling translation.
"""
import ctypes
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 可用 SD_INSTALL 指定 Designer 安装目录（非默认路径时）
SD_INSTALL = os.environ.get("SD_INSTALL", r"C:\Program Files\Adobe\Adobe Substance 3D Designer")
os.add_dll_directory(SD_INSTALL)
os.add_dll_directory(os.path.join(SD_INSTALL, "plugins", "pythonsdk"))

from PySide6 import QtCore, QtGui, QtWidgets
from shiboken6 import getCppPointer

DLL = os.environ.get(
    "XK_DLL", os.path.join(ROOT, "source", "native", "xingkong_zh_qt6.dll"))
OUT = os.path.join(ROOT, "tests")


def load_dll():
    dll = ctypes.CDLL(DLL)
    dll.xk_api_version.restype = ctypes.c_int
    dll.xk_add_translation.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p]
    dll.xk_install.argtypes = [ctypes.c_void_p]
    dll.xk_install.restype = ctypes.c_int
    dll.xk_uninstall.restype = ctypes.c_int
    dll.xk_translation_count.restype = ctypes.c_int
    dll.xk_set_enabled.argtypes = [ctypes.c_int]
    dll.xk_set_enabled.restype = None
    print("api:", dll.xk_api_version())
    return dll


def capture(widget, name):
    screen = QtGui.QGuiApplication.primaryScreen()
    pixmap = screen.grabWindow(int(widget.winId()))
    pixmap.save(os.path.join(OUT, name))
    print("saved", name, pixmap.size())


def build_window():
    window = QtWidgets.QMainWindow()
    window.setWindowTitle("XingKong Smoke Test")
    central = QtWidgets.QWidget()
    layout = QtWidgets.QVBoxLayout(central)

    label = QtWidgets.QLabel("Material")
    button = QtWidgets.QPushButton("Open")
    combo = QtWidgets.QComboBox()
    combo.addItems(["Base Color", "Roughness", "Metallic"])
    window._combo = combo

    model = QtGui.QStandardItemModel()
    for text in ["Height", "Normal", "Ambient Occlusion"]:
        model.appendRow(QtGui.QStandardItem(text))
    tree = QtWidgets.QTreeView()
    tree.setModel(model)

    layout.addWidget(label)
    layout.addWidget(button)
    layout.addWidget(combo)
    layout.addWidget(tree)
    window.setCentralWidget(central)

    menu = window.menuBar().addMenu("File")
    menu.addAction("Open")
    menu.addAction("Save As")
    window.resize(420, 320)
    window.move(120, 120)
    return window


def main():
    app = QtWidgets.QApplication(sys.argv)
    window = build_window()
    window.show()
    app.processEvents()

    dll = load_dll()
    for src, dst in [
        ("Material", "材质"), ("Open", "打开"), ("File", "文件"),
        ("Save As", "另存为"), ("Base Color", "基础颜色"),
        ("Roughness", "粗糙度"), ("Metallic", "金属度"),
        ("Height", "高度"), ("Normal", "法线"),
        ("Ambient Occlusion", "环境光遮蔽"),
    ]:
        dll.xk_add_translation(src, dst)
    print("count:", dll.xk_translation_count())

    pointer = getCppPointer(app)[0]
    print("install:", dll.xk_install(ctypes.c_void_p(pointer)))
    dll.xk_set_enabled(1)
    window.update()
    app.processEvents()

    def finish():
        capture(window, "smoke_enabled.png")
        combo = window._combo
        combo.showPopup()
        loop = QtCore.QEventLoop()
        QtCore.QTimer.singleShot(400, loop.quit)
        loop.exec()
        app.processEvents()
        capture(combo.view().window(), "smoke_combo.png")
        combo.hidePopup()
        print("uninstall:", dll.xk_uninstall())
        window.update()
        app.processEvents()
        capture(window, "smoke_disabled.png")
        app.quit()

    QtCore.QTimer.singleShot(800, finish)
    app.exec()


if __name__ == "__main__":
    main()
