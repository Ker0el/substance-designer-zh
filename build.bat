@echo off
setlocal
set "PROJECT_DIR=%~dp0"
if "%QT_ROOT%"=="" set "QT_ROOT=%PROJECT_DIR%_ThirdParty\Qt\6.8.3\msvc2022_64"
if "%VS_VCVARS%"=="" set "VS_VCVARS=D:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvars64.bat"
if "%CMAKE_EXE%"=="" set "CMAKE_EXE=D:\Program Files\Microsoft Visual Studio\18\Community\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe"
call "%VS_VCVARS%" >nul
if errorlevel 1 exit /b 1
"%CMAKE_EXE%" -S "%PROJECT_DIR%cpp" -B "%PROJECT_DIR%cpp\build" -G Ninja -DCMAKE_BUILD_TYPE=Release -DQT_ROOT="%QT_ROOT%"
if errorlevel 1 exit /b 1
"%CMAKE_EXE%" --build "%PROJECT_DIR%cpp\build" --config Release
if errorlevel 1 exit /b 1
echo BUILD OK
