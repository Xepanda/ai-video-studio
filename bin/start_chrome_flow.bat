@echo off
chcp 65001 >nul
echo ========================================================
echo   Google Flow 调试浏览器一键启动器 (Chrome CDP Remote Debug)
echo ========================================================
echo.
echo 正在检查本地 9222 端口状态...
netstat -ano | findstr 9222 >nul
if %errorlevel% equ 0 (
    echo [提示] 9222 调试端口已在运行中，无需重复启动！
    echo 浏览器已就绪，AI 脚本可直接接管操作。
    pause
    exit /b 0
)

echo 正在启动 Chrome 调试实例 (远程接管端口: 9222)...
set CHROME_PATH="C:\Program Files\Google\Chrome\Application\chrome.exe"
if not exist %CHROME_PATH% (
    set CHROME_PATH="C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
)
if not exist %CHROME_PATH% (
    set CHROME_PATH="%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"
)

start "" %CHROME_PATH% --remote-debugging-port=9222 --user-data-dir="%USERPROFILE%\.chrome-flow-profile" "https://flow.google.com"

echo.
echo [成功] 调试浏览器已启动！
echo 说明：
echo 1. 该窗口使用独立 profile，首次需要您正常完成一次 Google 账号登录 (支持2FA)；
echo 2. 登录状态会自动永久保存在本地，下次无需重复登录；
echo 3. 窗口打开后，AI 脚本 (如 batch_flow_generate.js) 即可 100%% 全自动接管上传、填词与下载！
echo.
pause
