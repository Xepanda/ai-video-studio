@echo off
chcp 65001 >nul
title GPT-SoVITS 本地专属音色推理服务 (9880)
echo =======================================================
echo 🎙️ 正在启动本地个人专属音色推理服务 (AMD CPU 模式)...
echo =======================================================
"C:\Users\ePanda\.workbuddy\binaries\python\envs\liveclip\Scripts\python.exe" "%~dp0start_local_sovits.py"
pause
