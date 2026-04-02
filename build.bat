@echo off
chcp 65001 >nul
echo ============================================
echo Sudoku KDP Generator - Build Script
echo ============================================
echo.

:: Kiểm tra Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Khong tim thay Python. Hay cai dat Python truoc.
    pause
    exit /b 1
)

:: Kiểm tra virtual environment
echo [1/4] Kiem tra moi truong ao...
if not exist "venv" (
    echo         Tao virtual environment...
    python -m venv venv
)

:: Kích hoạt venv
echo [2/4] Kich hoat virtual environment...
call venv\Scripts\activate.bat

:: Cài đặt dependencies
echo [3/4] Cai dat dependencies...
pip install -q --upgrade pip
pip install -q pyinstaller reportlab pillow

:: Chạy build
echo [4/4] Build executable...
python build_exe.py

echo.
echo ============================================
echo Build hoan tat!
echo File exe: dist\SudokuKDPGenerator.exe
echo ============================================
pause
