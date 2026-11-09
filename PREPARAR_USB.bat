@echo off
chcp 65001 > nul
cls

echo =====================================================================
echo       CREADOR DE USB PORTABLE SADIGUA (CON MODELOS LLM)
echo =====================================================================
echo Este asistente copiara Sadigua, la memoria Obsidian y los 4.7 GB
echo del modelo Qwen local a tu memoria USB o disco externo.
echo =====================================================================
echo.

powershell -ExecutionPolicy Bypass -File .\scripts\export_to_usb.ps1

pause
