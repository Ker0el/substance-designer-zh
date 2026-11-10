# Substance 3D Designer 星空汉化插件 · 设计

日期：2026-11-09
状态：已获用户口头批准（“按你推荐的来”）

## 1. 意图

为 Substance 3D Designer 16.0.7 制作“星空汉化”中文显示插件。

## 2. 目标

- 安装到 `%USERPROFILE%\Documents\Adobe\Adobe Substance 3D Designer\python\sduserplugins\xingkong_zh`，
  由 Designer 的 Plugin Manager 加载。
- 纯显示层翻译：菜单、按钮、参数标签、标签页、下拉框、列表/树/表格、资源架、tooltip。
- `F1` 开关中英文；关闭后界面完全恢复（包括 Adobe 官方中文）。
- 菜单栏提供蓝色“星空汉化”超链接，指向 B 站主页。
- 自带词库，由本项目从 Adobe 官方 `.qm` 与 `resources/packages` 提取后自行翻译。
- 不修改宿主文件、不注入进程、不写宿主工程数据；卸载即删除插件目录。

## 3. 非目标（V1 不做）

- Designer 节点图标题/端口翻译（V2，默认关闭，性能开销大）。
- Substance 3D Painter 支持（架构预留，V1 不打包 Qt5 DLL）。
- 在线更新、改译弹窗、Shift+` 采集（V2 候选）。
- 安装包（V1 交付免安装插件目录；Inno 安装包随后按通用 Inno Setup 规范制作）。

## 4. 约束

- 宿主：Designer 16.0.7，Qt 6.8.6，Python 3.13 + 内置 PySide6。
- 编译：MSVC 14.51（VS 18 Community），CMake/Ninja 由 VS 提供。
- Qt SDK：aqtinstall 下载 6.8.3 msvc2022_64（与 6.8.6 ABI 兼容），只取 qtbase + qttools。
- 许可：本项目为独立实现；不包含 GPL-3.0 代码或词库。参考实现仅用于理解行为与边界。
- 禁止：`setText/setWindowTitle` 改原文；翻译 QLineEdit 用户输入；翻译离屏
  `QImage/QPixmap/打印`；在 `DllMain` 操作 Qt；只钩绘制不钩测量。

## 5. 架构

```
xingkong_zh/
├── pluginInfo.json                  Designer 元数据（name=xingkong_zh）
├── __init__.py                      旧式兼容垫片
├── xingkong_zh/__init__.py          Python 主体：生命周期/词库/菜单/F1/设置
├── native/xingkong_zh_qt6.dll       自研 Qt6 显示引擎
└── translations/
    ├── ui_zh.json                   界面词条
    ├── assets_zh.json               资源/节点词条
    └── control_ids_zh.json          控件专项（_skip_/位点译法）
```

### 5.1 Python 层

- `initializeSDPlugin()` / `uninitializeSDPlugin()`；兼容 `start_plugin/close_plugin`。
- 通过 `sd.getContext().getSDApplication().getQtForPythonUIMgr().getMainWindow()` 取主窗口。
- 加载 `translations/*_zh.json`，按文件名排序覆盖；把词条通过 `xk_add_translation`
  逐条推给 C++（UTF-16），绘制热路径不回调 Python。
- 菜单栏：`星空汉化`（QWidgetAction + 富文本 `<a>`，蓝色，打开 B 站）、
  `星空汉化设置`（总开关、F1 提示、词库统计、版本）。
- `F1`：QAction 快捷键，切换 `xk_set_enabled`；状态写入 `QSettings`。

### 5.2 C++ 层（自研）

导出（`extern "C" __cdecl`）：

```
int  xk_api_version();                    // 1
int  xk_install(void* QApplication*);
int  xk_uninstall();
void xk_set_enabled(int);
void xk_add_translation(const wchar_t* src, const wchar_t* dst);
void xk_clear_translations();
void xk_set_fuzzy(int);
void xk_set_graph_enabled(int);
int  xk_translation_count();
```

实现：

1. `QHash<QString, QString>` 精确词典 + 归一化索引（空白/大小写/下划线/省略号/全半角）。
2. `TranslationFilter : QObject` 装在 QApplication：`ChildAdded/Polish/Show` 时给
   `QTreeView/QListView/QTableView/QComboBox` 安装 `XingKongDelegate`。
3. `XingKongDelegate : QStyledItemDelegate` 重写 `displayText()`；宿主自定义 delegate
   不替换（仅替换 `typeid` 恰为 `QStyledItemDelegate` 的实例）。
4. IAT hook：`GetProcAddress(Qt6Gui.dll, mangled)` 取 8 个 `QPainter::drawText`
   重载原地址；遍历全部模块导入表，把指向原地址的槽替换为本项目钩子。
5. 钩子内：`thread_local` 递归保护；仅当 `painter->device()` 是 `QWidget` 时翻译；
   命中词典才替换，否则原样调用；退出/卸载逐个还原槽。
6. 中文原文默认跳过；`_skip_` 控件 ID 优先。

## 6. 词库流水线

1. `tools/qm_extract.py`：用 Qt `lconvert` 把 `resources/translations/*_zh.qm` 转 `.ts`，
   解析 `source → translation`，产出 `translations/ui_zh.json` 的基础层。
2. `tools/extract_sbs.py`：扫描 `resources/packages/*.sbs`（XML）的
   `name/label/description/group`，产出英文候选 `inventory/`.
3. `tools/merge_dictionary.py`：合并候选、去重、过滤（长度、含汉字、URL、路径）。
4. 未覆盖候选由我分批翻译，写入 `assets_zh.json`；术语表固定（如 Base Color=基础颜色、
   Roughness=粗糙度、Metallic=金属度、Height=高度、Normal=法线）。
5. 运行时跳过含汉字文本，避免覆盖 Adobe 官方译文。

## 7. 交互与品牌

- 菜单栏左侧追加：`星空汉化`（超链接）、`星空汉化设置`。
- 设置窗口：总开关、F1 说明、词库条目数、版本、B 站链接。
- 默认启用；关闭插件或 F1 关闭后完全还原。

## 8. 验证

- 构建：CMake Release 生成 `xingkong_zh_qt6.dll`，导出符号齐全。
- 静态：`dumpbin /exports` 校验 8 个 hook 与 API。
- 运行：启动 Designer，确认菜单出现、F1 切换、列表/菜单翻译、关闭后恢复。
- 导出：导出贴图/节点图，确认导出内容无中文。
- 卸载：Plugin Manager 禁用，确认无崩溃、无残留。

## 9. 交付

- V1：`dist/xingkong_zh/`（插件目录，可直接拷贝安装）。
- 随后：Inno 安装包、使用说明、B 站链接、校验值。

## 10. 留给实现者的决定

- 是否在 V1 加入 `QProxyStyle`（菜单/按钮覆盖更稳，但可能改变宿主观感）——先不做，
  以 drawText 钩子 + delegate 为主，实测不足再加。
- 模糊匹配默认开启，归一化规则与词库侧保持一致。
- 词库规模：V1 先保证界面 + 常用节点/资源；全量 1.3 万条分批扩充。
