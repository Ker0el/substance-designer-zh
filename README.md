# 星空汉化 · Substance 3D Designer 中文插件

面向 Windows 版 **Adobe Substance 3D Designer 14 及以上（本机实测 16.0.7）** 的显示层中文补全插件。
只翻译“画出来的那一刻”，不修改控件原文、模型数据、输入内容或工程文件。

> English: a display-only Chinese localization plugin for Adobe Substance 3D Designer on Windows.
> Text is translated at paint time; project data and inputs are never modified.

下载：[Releases](https://github.com/Ker0el/substance-designer-zh/releases)。

## 安装

**方式一：安装包（推荐）**

1. 完全退出 Substance 3D Designer。
2. 运行 `xingkong_zh_v0.1.2_setup.exe`（本地构建产物同名文件为 `星空汉化_SD插件_v0.1.2_安装包.exe`），按提示下一步。
3. 启动 Designer，打开 **工具 → 插件管理器（Tools → Plugin Manager）**，启用 `xingkong_zh`。
4. 菜单栏出现 **星空汉化** 即安装成功。

默认安装目录：
`%USERPROFILE%\Documents\Adobe\Adobe Substance 3D Designer\python\sduserplugins\xingkong_zh`

**方式二：手动复制**

1. 完全退出 Designer。
2. 把本目录复制到上面的默认安装目录。
3. 启动 Designer，在插件管理器中启用 `xingkong_zh`。


## 使用

- `F1`：中英文显示切换（默认开启）。
- 菜单栏 **星空汉化 → 星空汉化 · B站主页**：打开 B 站主页。
- 菜单栏 **星空汉化 → 星空汉化设置**：总开关、模糊匹配、词条数量、版本。
- 关闭插件或按 `F1` 后，界面完全恢复原样（包括 Adobe 官方中文）。

## 范围（V1）

- 菜单、按钮、参数标签、标签页、下拉框、列表/树/表格、资源架、tooltip。
- 资源架搜索支持中文和英文：中文查询由插件过滤，英文查询保持宿主原生搜索。
- 词库 4719 条（界面 276 + 资源/节点 4443），持续扩充中。
- 节点图标题/端口翻译：已接入，受节点宽度限制，长文本会自动缩小字号。
- 不覆盖 Adobe 官方中文；官方已翻译的文本保持官方译法。

## 已知限制

- 节点图由 `QGraphicsItem` 自绘，超长译名可能被节点宽度裁切；遇到请反馈具体节点。
- 少部分控件因宿主自绘/自定义 delegate，可能仍显示英文；会随词库和钩子覆盖逐步补齐。
- 下拉框、参数面板的宽度仍按英文测量，极少数长译名可能显示不全。

## 卸载

- 安装包版本：设置 → 应用 → 已安装的应用 → 卸载 **星空汉化 · SD 中文插件**。
- 手动安装版本：退出 Designer，删除 `sduserplugins\xingkong_zh` 目录。

卸载只删除插件自己的文件，不影响 Designer 本体、工程和官方中文。

## 构建（开发）

环境要求：Windows、Visual Studio（含 C++ 桌面工作负载与 CMake/Ninja）、
Qt 6.8.3 msvc2022_64（aqtinstall 安装 `qtbase` 与 `qttools`）。
默认从 `_ThirdParty/Qt/6.8.3/msvc2022_64` 查找 Qt；可用环境变量覆盖：
`QT_ROOT`、`VS_VCVARS`、`CMAKE_EXE`、`ISCC`。

```bat
:: 1. 编译原生引擎（输出 cpp\build\xingkong_zh_qt6.dll）
build.bat

:: 2. 重新生成词库
python tools\build_dictionary.py

:: 3. 同步到插件目录后重启 Designer（测试）
::    native\xingkong_zh_qt6.dll
::    xingkong_zh\__init__.py

:: 4. 编译 Inno 安装包（输出到 dist）
installer\build.bat
```

源码结构：

```
source/pluginInfo.json             Designer 插件元数据
source/__init__.py                 入口垫片
source/xingkong_zh/__init__.py     Python 主体（生命周期/词库/菜单/F1/设置）
cpp/xingkong_zh.cpp                自研 Qt6 显示引擎（delegate + drawText IAT hook）
cpp/CMakeLists.txt                 构建脚本
tools/extract_sbs.py               从 resources/packages/*.sbs 提取英文候选
tools/build_dictionary.py          合并人工词库与规则
translations/manual_*_zh.json      人工翻译源文件
installer/build.iss                Inno 安装包脚本
installer/安装说明.txt             安装包首屏说明
```

## 许可证

MIT License，见 [LICENSE](LICENSE)。

## 声明

- 本插件完全免费，开源分享。
- B 站：https://space.bilibili.com/177308205
