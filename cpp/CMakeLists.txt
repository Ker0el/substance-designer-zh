cmake_minimum_required(VERSION 3.21)
project(xingkong_zh_native LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(_default_qt_root "${CMAKE_CURRENT_SOURCE_DIR}/../_ThirdParty/Qt/6.8.3/msvc2022_64")
if(DEFINED ENV{QT_ROOT} AND NOT "$ENV{QT_ROOT}" STREQUAL "")
    set(_default_qt_root "$ENV{QT_ROOT}")
endif()
set(QT_ROOT "${_default_qt_root}" CACHE PATH "Qt6 SDK root (or set the QT_ROOT env var)")
if(NOT EXISTS "${QT_ROOT}/lib/Qt6Widgets.lib")
    message(FATAL_ERROR "Qt6 SDK is missing: ${QT_ROOT}")
endif()

add_library(xingkong_zh_qt6 SHARED xingkong_zh.cpp)
target_include_directories(xingkong_zh_qt6 PRIVATE
    "${QT_ROOT}/include"
    "${QT_ROOT}/include/QtCore"
    "${QT_ROOT}/include/QtGui"
    "${QT_ROOT}/include/QtWidgets"
    "${QT_ROOT}/mkspecs/win32-msvc"
)
target_link_libraries(xingkong_zh_qt6 PRIVATE
    "${QT_ROOT}/lib/Qt6Core.lib"
    "${QT_ROOT}/lib/Qt6Gui.lib"
    "${QT_ROOT}/lib/Qt6Widgets.lib"
    version.lib
    psapi.lib
    dbghelp.lib
)
target_compile_definitions(xingkong_zh_qt6 PRIVATE
    QT_CORE_LIB QT_GUI_LIB QT_WIDGETS_LIB UNICODE _UNICODE NOMINMAX WIN32_LEAN_AND_MEAN)
if(MSVC)
    target_compile_options(xingkong_zh_qt6 PRIVATE /W4 /utf-8 /permissive- /Zc:__cplusplus)
endif()
set_target_properties(xingkong_zh_qt6 PROPERTIES
    OUTPUT_NAME "xingkong_zh_qt6"
    PREFIX ""
)
