# -*- coding: utf-8 -*-
"""星空汉化 · Substance 3D Designer 中文显示插件。

设计原则：只翻译“绘制那一刻”的文本，不修改宿主控件、模型、输入或工程数据。
关闭插件或按 F1 后，界面完全恢复原样（包括 Adobe 官方中文）。
"""

import ctypes
import json
import os
import re
import tempfile
import time

from PySide6 import QtCore, QtGui, QtWidgets
from shiboken6 import getCppPointer, isValid

try:
    import sd  # Substance 3D Designer
except Exception:  # pragma: no cover - 非 Designer 环境
    sd = None

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NATIVE_PATH = os.path.join(PLUGIN_ROOT, "native", "xingkong_zh_qt6.dll")
TRANSLATIONS_DIR = os.path.join(PLUGIN_ROOT, "translations")
BILIBILI_URL = "https://space.bilibili.com/177308205"
APP_VERSION = "0.1.2"
API_VERSION = 1

_state = {
    "dll": None,
    "window": None,
    "actions": [],
    "shortcut": None,
    "dialog": None,
    "enabled": True,
    "fuzzy": True,
    "dictionary": {},
    "control_ids": {},
    "started": False,
    "log_path": os.path.join(tempfile.gettempdir(), "xingkong_zh.log"),
}


def _log(*parts):
    try:
        with open(_state["log_path"], "a", encoding="utf-8") as handle:
            handle.write(time.strftime("%Y-%m-%d %H:%M:%S ") + " ".join(str(p) for p in parts) + "\n")
    except Exception:
        pass


def _settings():
    return QtCore.QSettings("XingKong", "xingkong_zh")


def _load_preferences():
    settings = _settings()
    _state["enabled"] = settings.value("enabled", True, type=bool)
    _state["fuzzy"] = settings.value("fuzzy", True, type=bool)


def _save_preferences():
    settings = _settings()
    settings.setValue("enabled", bool(_state["enabled"]))
    settings.setValue("fuzzy", bool(_state["fuzzy"]))


def _main_window():
    if sd is None:
        return None
    try:
        context = sd.getContext()
        application = context.getSDApplication()
        ui_manager = application.getQtForPythonUIMgr()
        return ui_manager.getMainWindow() if ui_manager else None
    except Exception as exc:
        _log("get main window failed:", exc)
        return None


def _load_control_ids():
    path = os.path.join(TRANSLATIONS_DIR, "control_ids_zh.json")
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8-sig") as handle:
            data = json.load(handle)
        entries = data.get("translations", data) if isinstance(data, dict) else {}
        return {k: v for k, v in entries.items()
                if isinstance(k, str) and isinstance(v, str) and k.strip() and v}
    except Exception as exc:
        _log("control ids failed:", exc)
        return {}


def _load_dictionary():
    merged = {}
    if not os.path.isdir(TRANSLATIONS_DIR):
        return merged
    for name in sorted(os.listdir(TRANSLATIONS_DIR)):
        if not name.endswith("_zh.json") or name.startswith("control_ids"):
            continue
        path = os.path.join(TRANSLATIONS_DIR, name)
        try:
            with open(path, "r", encoding="utf-8-sig") as handle:
                data = json.load(handle)
            entries = data.get("translations", data) if isinstance(data, dict) else {}
            count = 0
            for source, target in entries.items():
                if (isinstance(source, str) and isinstance(target, str)
                        and source.strip() and target.strip()
                        and not target.startswith("_")):
                    merged[source] = target
                    count += 1
            _log(f"dictionary {name}: {count} entries")
        except Exception as exc:
            _log(f"dictionary {name} failed:", exc)
    return merged


def _load_native():
    dll = _state["dll"]
    if dll is not None:
        return dll
    if not os.path.isfile(NATIVE_PATH):
        _log("native engine missing:", NATIVE_PATH)
        return None
    try:
        dll = ctypes.CDLL(NATIVE_PATH)
        dll.xk_api_version.argtypes = []
        dll.xk_api_version.restype = ctypes.c_int
        version = dll.xk_api_version()
        if version != API_VERSION:
            raise RuntimeError(f"native API mismatch: {version} != {API_VERSION}")

        dll.xk_build_id.argtypes = []
        dll.xk_build_id.restype = ctypes.c_wchar_p
        dll.xk_install.argtypes = [ctypes.c_void_p]
        dll.xk_install.restype = ctypes.c_int
        dll.xk_uninstall.argtypes = []
        dll.xk_uninstall.restype = ctypes.c_int
        dll.xk_set_enabled.argtypes = [ctypes.c_int]
        dll.xk_set_enabled.restype = None
        dll.xk_set_fuzzy.argtypes = [ctypes.c_int]
        dll.xk_set_fuzzy.restype = None
        dll.xk_set_graph_enabled.argtypes = [ctypes.c_int]
        dll.xk_set_graph_enabled.restype = None
        dll.xk_add_translation.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p]
        dll.xk_add_translation.restype = None
        dll.xk_add_id_translation.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p]
        dll.xk_add_id_translation.restype = None
        dll.xk_clear_translations.argtypes = []
        dll.xk_clear_translations.restype = None
        dll.xk_translation_count.argtypes = []
        dll.xk_translation_count.restype = ctypes.c_int
        dll.xk_hook_count.argtypes = []
        dll.xk_hook_count.restype = ctypes.c_int
        dll.xk_combo_count.argtypes = []
        dll.xk_combo_count.restype = ctypes.c_int
        dll.xk_combo_info.argtypes = []
        dll.xk_combo_info.restype = ctypes.c_char_p
        dll.xk_view_count.argtypes = []
        dll.xk_view_count.restype = ctypes.c_int
        dll.xk_view_info.argtypes = []
        dll.xk_view_info.restype = ctypes.c_char_p

        _state["dll"] = dll
        _log("native engine:", dll.xk_build_id())
        return dll
    except Exception as exc:
        _log("native load failed:", exc)
        _state["dll"] = None
        return None


def _push_dictionary(dll):
    dictionary = _state["dictionary"]
    dll.xk_clear_translations()
    pushed = 0
    for source, target in dictionary.items():
        dll.xk_add_translation(source, target)
        pushed += 1
    ids = _state["control_ids"]
    for control_id, target in ids.items():
        dll.xk_add_id_translation(control_id, target)
    _log(f"dictionary pushed: {pushed}, control ids: {len(ids)}")
    return pushed


def _install_native():
    dll = _load_native()
    if dll is None:
        return False
    app = QtWidgets.QApplication.instance()
    if app is None or not isValid(app):
        _log("QApplication unavailable")
        return False
    try:
        pointer = getCppPointer(app)[0]
        installed = dll.xk_install(ctypes.c_void_p(pointer)) == 1
        dll.xk_set_fuzzy(int(_state["fuzzy"]))
        dll.xk_set_graph_enabled(0)
        dll.xk_set_enabled(int(_state["enabled"]))
        # 钩子安装后强制重绘一次，菜单栏等启动时已绘制的文本才会走新钩子。
        for widget in QtWidgets.QApplication.allWidgets():
            try:
                widget.update()
            except Exception:
                pass
        app.processEvents()
        _log("native install:", installed, "hooks:", dll.xk_hook_count(),
             "combos:", dll.xk_combo_count(), "enabled:", _state["enabled"])
        try:
            info = dll.xk_combo_info()
            _log("combo delegates:", info.decode("utf-8", "replace") if info else "")
        except Exception as exc:
            _log("combo info failed:", exc)
        try:
            _log("custom views:", dll.xk_view_count())
            info = dll.xk_view_info()
            _log("custom view info:", info.decode("utf-8", "replace") if info else "")
        except Exception as exc:
            _log("view info failed:", exc)
        return installed
    except Exception as exc:
        _log("native install failed:", exc)
        return False


def _set_enabled(enabled):
    _state["enabled"] = bool(enabled)
    dll = _state["dll"]
    if dll is not None:
        try:
            dll.xk_set_enabled(int(_state["enabled"]))
        except Exception as exc:
            _log("set enabled failed:", exc)
    for widget in QtWidgets.QApplication.allWidgets():
        try:
            widget.update()
        except Exception:
            pass
    _save_preferences()
    _log("enabled:", _state["enabled"])


def _toggle_enabled():
    _set_enabled(not _state["enabled"])
    dialog = _state["dialog"]
    if dialog is not None and isValid(dialog):
        dialog.sync_state()


class SettingsDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("星空汉化 · 设置")
        self.setMinimumWidth(420)

        layout = QtWidgets.QVBoxLayout(self)
        title = QtWidgets.QLabel(
            f'<b style="font-size:15px;">星空汉化</b>'
            f'<span style="color:#888;"> · Substance 3D Designer {APP_VERSION}</span>'
        )
        layout.addWidget(title)

        self.enabled_box = QtWidgets.QCheckBox("启用中文显示（F1 切换）")
        self.enabled_box.setChecked(_state["enabled"])
        self.enabled_box.toggled.connect(_set_enabled)
        layout.addWidget(self.enabled_box)

        self.fuzzy_box = QtWidgets.QCheckBox("启用模糊匹配（大小写 / 下划线 / 空格）")
        self.fuzzy_box.setChecked(_state["fuzzy"])
        self.fuzzy_box.toggled.connect(self._on_fuzzy)
        layout.addWidget(self.fuzzy_box)

        self.count_label = QtWidgets.QLabel(self._count_text())
        layout.addWidget(self.count_label)

        link = QtWidgets.QLabel(
            f'<a href="{BILIBILI_URL}" style="color:#4da3ff;">{BILIBILI_URL}</a>'
        )
        link.setOpenExternalLinks(True)
        link.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextBrowserInteraction)
        layout.addWidget(link)

        note = QtWidgets.QLabel(
            "翻译只作用于显示层：输入框内容、资源原名和工程数据保持原文。"
        )
        note.setWordWrap(True)
        note.setStyleSheet("color:#888;")
        layout.addWidget(note)

        free_note = QtWidgets.QLabel("本插件完全免费，开源分享。")
        free_note.setWordWrap(True)
        free_note.setStyleSheet("color:#888;")
        layout.addWidget(free_note)

        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.close)
        layout.addWidget(buttons)

    def _count_text(self):
        return f"已加载词条：{len(_state['dictionary'])} 条"

    def _on_fuzzy(self, checked):
        _state["fuzzy"] = bool(checked)
        dll = _state["dll"]
        if dll is not None:
            try:
                dll.xk_set_fuzzy(int(_state["fuzzy"]))
            except Exception:
                pass
        _save_preferences()

    def sync_state(self):
        self.enabled_box.blockSignals(True)
        self.enabled_box.setChecked(_state["enabled"])
        self.enabled_box.blockSignals(False)
        self.count_label.setText(self._count_text())


def _collect_untranslated(show_message=True):
    """从 Designer API、可见模型和控件树采集未翻译英文（只读）。"""
    items = set()
    stats = {"definitions": 0, "packages": 0, "model_items": 0, "widgets": 0}

    def add(value):
        if not isinstance(value, str):
            return
        text = " ".join(value.replace("\r", " ").replace("\n", " ").split())
        if not (2 <= len(text) <= 160):
            return
        if any("㐀" <= ch <= "鿿" for ch in text):
            return
        if not any(ch.isalpha() for ch in text):
            return
        if text.endswith((":", "：")):
            return
        if " " not in text:
            if len(text) > 24:
                return
            if re.search(r"[a-z][A-Z]", text):
                return  # CamelCase 内部标识
            if any(word in text for word in (
                    "Manager", "Mgr", "Settings", "Path", "Event", "Args",
                    "Version", "Support", "Player", "Database", "Converter",
                    "Matrix", "Temp", "Url", "Internal", "License", "News",
                    "Bakers", "Translations", "Info")):
                return
        if "_" in text and " " not in text:
            return
        if text.islower() and " " not in text:
            return
        if any(token in text for token in ("://", "\\", "<", ">", "=", "*")):
            return
        if text in _state["dictionary"]:
            return
        items.add(text)

    # 1. 节点定义（资源库面板里的滤镜/生成器/节点名称）
    application = None
    try:
        application = sd.getContext().getSDApplication()
        graph_manager = application.getSDGraphDefinitionMgr()
        for module in graph_manager.getGraphDefinitions():
            try:
                definitions = module.getDefinitions()
            except Exception:
                continue
            for definition in definitions:
                try:
                    add(str(definition.getLabel()))
                except Exception:
                    pass
            stats["definitions"] += 1
        _log("collect definitions:", stats["definitions"])
    except Exception as exc:
        _log("collect definitions failed:", exc)

    # 2. 已加载资源包
    if application is not None:
        try:
            package_manager = application.getPackageMgr()
            for package in package_manager.getPackages():
                try:
                    resources = package.getChildrenResources(True)
                except Exception:
                    continue
                for resource in resources:
                    try:
                        add(str(resource.getIdentifier()))
                    except Exception:
                        pass
                stats["packages"] += 1
            _log("collect packages:", stats["packages"])
        except Exception as exc:
            _log("collect packages failed:", exc)

    # 3. 可见资源列表模型
    for widget in QtWidgets.QApplication.allWidgets():
        if isinstance(widget, QtWidgets.QAbstractItemView):
            model = widget.model()
            if model is not None:
                try:
                    for row in range(model.rowCount()):
                        add(model.index(row, 0).data(QtCore.Qt.ItemDataRole.DisplayRole))
                        stats["model_items"] += 1
                except Exception:
                    pass

    # 4. QAccessible 树（覆盖部分隐藏菜单、下拉项、分组标题）
    accessible_seen = set()

    def walk_accessible(iface, depth=0):
        if iface is None or depth > 16:
            return
        key = id(iface)
        if key in accessible_seen:
            return
        accessible_seen.add(key)
        try:
            for text_role in (
                    QtGui.QAccessible.Text.Name,
                    QtGui.QAccessible.Text.Description,
                    QtGui.QAccessible.Text.Value,
                    QtGui.QAccessible.Text.Help):
                add(iface.text(text_role))
        except Exception:
            pass
        try:
            count = iface.childCount()
        except Exception:
            return
        for index in range(count):
            try:
                walk_accessible(iface.child(index), depth + 1)
            except Exception:
                pass

    try:
        for window in QtWidgets.QApplication.topLevelWidgets():
            walk_accessible(QtGui.QAccessible.queryAccessibleInterface(window))
    except Exception as exc:
        _log("accessible walk failed:", exc)

    # 5. 控件文本、菜单、tooltip、下拉框选项
    for widget in QtWidgets.QApplication.allWidgets():
        stats["widgets"] += 1
        for attribute in ("windowTitle", "text", "placeholderText", "toolTip"):
            try:
                add(getattr(widget, attribute)())
            except Exception:
                pass
        try:
            for action in widget.actions():
                add(action.text())
                add(action.toolTip())
        except Exception:
            pass
        try:
            iface = QtGui.QAccessible.queryAccessibleInterface(widget)
            if iface is not None:
                for text_role in (
                        QtGui.QAccessible.Text.Name,
                        QtGui.QAccessible.Text.Description,
                        QtGui.QAccessible.Text.Value,
                        QtGui.QAccessible.Text.Help):
                    add(iface.text(text_role))
        except Exception:
            pass
        if isinstance(widget, QtWidgets.QComboBox):
            try:
                for index in range(widget.count()):
                    add(widget.itemText(index))
            except Exception:
                pass
        if isinstance(widget, QtWidgets.QMenu):
            try:
                for action in widget.actions():
                    add(action.text())
            except Exception:
                pass

    path = os.path.join(os.path.expanduser("~"), "Desktop", "xingkong_zh_untranslated.json")
    try:
        with open(path, "w", encoding="utf-8") as handle:
            json.dump({
                "metadata": stats,
                "translations": {text: "" for text in sorted(items, key=str.casefold)},
            }, handle, ensure_ascii=False, indent=1)
        _log(f"collected {len(items)} untranslated strings -> {path}")
        if show_message:
            QtWidgets.QMessageBox.information(
                _state["window"], "星空汉化",
                f"已采集 {len(items)} 条未翻译文本：\n{path}\n\n"
                f"节点模块 {stats['definitions']}，资源包 {stats['packages']}，"
                f"模型项 {stats['model_items']}，控件 {stats['widgets']}")
    except Exception as exc:
        _log("collect failed:", exc)


def _show_settings():
    window = _state["window"] or _main_window()
    dialog = _state["dialog"]
    if dialog is None or not isValid(dialog):
        dialog = SettingsDialog(window)
        _state["dialog"] = dialog
    dialog.sync_state()
    dialog.show()
    dialog.raise_()
    dialog.activateWindow()


def _add_actions(window):
    actions = []

    menu = QtWidgets.QMenu("星空汉化", window)
    link = QtWidgets.QWidgetAction(menu)
    label = QtWidgets.QLabel(
        f'<a href="{BILIBILI_URL}" style="color:#4da3ff;text-decoration:none;">星空汉化 · B站主页</a>'
    )
    label.setOpenExternalLinks(True)
    label.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextBrowserInteraction)
    label.setContentsMargins(10, 4, 10, 4)
    link.setDefaultWidget(label)
    menu.addAction(link)

    settings_action = QtGui.QAction("星空汉化设置", menu)
    settings_action.triggered.connect(_show_settings)
    menu.addAction(settings_action)

    window.menuBar().addMenu(menu)
    actions.append(menu.menuAction())

    shortcut = QtGui.QShortcut(QtGui.QKeySequence("F1"), window)
    shortcut.setContext(QtCore.Qt.ShortcutContext.ApplicationShortcut)
    shortcut.activated.connect(_toggle_enabled)
    _state["shortcut"] = shortcut

    _state["actions"] = actions
    _log("menu actions registered")


def _debug_autotest():
    """临时诊断：程序化打开下拉框/触发搜索，定位崩溃步骤（不控制鼠标）。"""
    path = os.path.join(tempfile.gettempdir(), "xingkong_autotest.log")
    def note(message):
        try:
            with open(path, "a", encoding="utf-8") as handle:
                handle.write(time.strftime("%H:%M:%S ") + message + "\n")
        except Exception:
            pass

    note("autotest start")
    combos = [w for w in QtWidgets.QApplication.allWidgets()
              if isinstance(w, QtWidgets.QComboBox)]
    note(f"combos={len(combos)}")
    for index, combo in enumerate(combos):
        try:
            note(f"combo {index} class={type(combo).__name__} count={combo.count()} visible={combo.isVisible()}")
            combo.showPopup()
            QtWidgets.QApplication.processEvents()
            note(f"combo {index} popup shown")
            combo.hidePopup()
            QtWidgets.QApplication.processEvents()
            note(f"combo {index} popup hidden")
        except Exception as exc:
            note(f"combo {index} error={exc!r}")

    for field in QtWidgets.QApplication.allWidgets():
        if isinstance(field, QtWidgets.QLineEdit) and field.objectName() == "globalSearch":
            try:
                note("search: set CJK")
                field.setFocus()
                field.setText("噪声")
                QtWidgets.QApplication.processEvents()
                note("search: cjk applied")
                field.setText("")
                QtWidgets.QApplication.processEvents()
                note("search: cleared")
            except Exception as exc:
                note(f"search error={exc!r}")
    note("autotest done")

    # 5. 模拟点击资源类别树（纹理生成器 → 噪点），复现切换分类崩溃
    try:
        from PySide6.QtTest import QTest
    except Exception as exc:
        note(f"QTest unavailable: {exc!r}")
        QTest = object()
    if QTest is not None:
        for view in QtWidgets.QApplication.allWidgets():
            if not isinstance(view, QtWidgets.QTreeView) or view.model() is None:
                continue
            model = view.model()

            def find_category(parent, depth=0):
                if depth > 3:
                    return None
                for row in range(model.rowCount(parent)):
                    index = model.index(row, 0, parent)
                    text = str(index.data(QtCore.Qt.ItemDataRole.DisplayRole) or "")
                    if text in ("噪点", "Noises", "噪声"):
                        return index
                    found = find_category(index, depth + 1)
                    if found is not None:
                        return found
                return None

            target = find_category(QtCore.QModelIndex())
            if target is not None:
                rect = view.visualRect(target)
                note(f"tree activate {target.data(QtCore.Qt.ItemDataRole.DisplayRole)} rect={rect}")
                view.setCurrentIndex(target)
                try:
                    view.clicked.emit(target)
                    note("tree clicked signal emitted")
                except Exception as exc:
                    note(f"tree clicked emit failed: {exc!r}")
                QtWidgets.QApplication.processEvents()
                note("tree click done")
                break

    note("collect start")
    _collect_untranslated(False)
    note("collect done")


def _start_engine():
    if _state["started"]:
        return
    window = _state["window"]
    if window is None or not isValid(window):
        window = _main_window()
        _state["window"] = window
    _state["dictionary"] = _load_dictionary()
    _state["control_ids"] = _load_control_ids()
    dll = _load_native()
    if dll is None:
        _log("engine start aborted: native missing")
        return
    _push_dictionary(dll)
    if _install_native():
        _state["started"] = True
        _log("engine started")
        flag = os.path.join(tempfile.gettempdir(), "xingkong_autotest.flag")
        if os.path.isfile(flag):
            QtCore.QTimer.singleShot(3000, _debug_autotest)
    else:
        _log("engine install failed")


def initializeSDPlugin():
    window = _main_window()
    if window is None or not isValid(window):
        raise RuntimeError("Designer 的 Qt 界面管理器不可用")
    _state["window"] = window
    _load_preferences()
    _add_actions(window)
    QtCore.QTimer.singleShot(2000, _start_engine)
    _log("plugin initialized, engine scheduled")


def uninitializeSDPlugin():
    dll = _state["dll"]
    try:
        if dll is not None:
            dll.xk_set_enabled(0)
            dll.xk_uninstall()
            dll.xk_clear_translations()
    except Exception as exc:
        _log("native uninstall failed:", exc)

    dialog = _state["dialog"]
    if dialog is not None and isValid(dialog):
        dialog.close()

    window = _state["window"]
    if window is not None and isValid(window):
        for action in _state["actions"]:
            try:
                window.menuBar().removeAction(action)
            except Exception:
                pass
    shortcut = _state["shortcut"]
    if shortcut is not None:
        try:
            shortcut.setEnabled(False)
            shortcut.deleteLater()
        except Exception:
            pass

    _state.update({
        "actions": [],
        "shortcut": None,
        "dialog": None,
        "dll": None,
        "dictionary": {},
        "control_ids": {},
        "started": False,
        "window": None,
    })
    _log("plugin uninitialized")


# 兼容 Painter 式入口（当前仅用于手动调用 / 测试）
def start_plugin():
    return initializeSDPlugin()


def close_plugin():
    return uninitializeSDPlugin()


def reload_plugin():
    close_plugin()
    return start_plugin()
