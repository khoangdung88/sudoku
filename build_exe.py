# Build script for Sudoku KDP Generator
# Chạy script này để đóng gói thành file exe

import PyInstaller.__main__
import os
import sys
import shutil

def clean_build_dirs():
    """Xóa các thư mục build cũ"""
    dirs_to_remove = ['build', 'dist']
    for d in dirs_to_remove:
        if os.path.exists(d):
            print(f"Removing {d}...")
            shutil.rmtree(d)
    
    # Xóa file spec cũ
    for f in os.listdir('.'):
        if f.endswith('.spec') and f != 'sudoku.spec':
            print(f"Removing {f}...")
            os.remove(f)

def build_exe():
    """Build executable using PyInstaller"""
    
    # Đảm bảo đang ở đúng thư mục
    if not os.path.exists('main.py'):
        print("Error: Không tìm thấy main.py. Hãy chạy script này từ thư mục gốc của dự án.")
        sys.exit(1)
    
    # Dọn dẹp trước khi build
    clean_build_dirs()
    
    # Các file và thư mục cần include
    add_data = [
        # File cấu hình mẫu
        ('pdf_config.sample.json', '.'),
        # Thư mục ic data
        ('ic data', 'ic data'),
        # Thư mục sudoku package
        ('sudoku', 'sudoku'),
    ]
    
    # Build command arguments
    args = [
        'main.py',                           # Entry point
        '--name=SudokuKDPGenerator',         # Tên file exe
        '--onefile',                         # Đóng gói thành 1 file
        '--windowed',                        # GUI application (không hiện console)
        '--noconsole',                       # Ẩn console window
        '--clean',                           # Dọn dẹp trước khi build
        
        # Icon (nếu có)
        # '--icon=icon.ico',
        
        # Hidden imports
        '--hidden-import=reportlab',
        '--hidden-import=reportlab.lib.colors',
        '--hidden-import=reportlab.pdfgen.canvas',
        '--hidden-import=reportlab.lib.pagesizes',
        '--hidden-import=reportlab.lib.units',
        '--hidden-import=reportlab.pdfbase',
        '--hidden-import=reportlab.pdfbase.pdfmetrics',
        '--hidden-import=reportlab.pdfbase.ttfonts',
        '--hidden-import=PIL',
        '--hidden-import=PIL.Image',
        
        # Data files
        '--add-data=pdf_config.sample.json;.',
        '--add-data=ic data;ic data',
        '--add-data=sudoku;sudoku',
    ]
    
    print("Starting build...")
    print(f"Arguments: {args}")
    
    # Chạy PyInstaller
    PyInstaller.__main__.run(args)
    
    print("\n" + "="*60)
    print("BUILD COMPLETE!")
    print("="*60)
    print(f"\nFile exe nằm tại: dist\\SudokuKDPGenerator.exe")
    print("\nCác file cần mang theo khi phân phối:")
    print("  - dist\\SudokuKDPGenerator.exe")
    print("  - pdf_config.sample.json (optional)")
    print("  - ic data\\ (nếu cần tham khảo)")

if __name__ == '__main__':
    build_exe()
