# Hướng dẫn đóng gói Sudoku KDP Generator thành file EXE

## Tóm tắt nhanh

### Cách 1: Chạy script tự động (Khuyến nghị)
```bash
# Chạy file batch
cd c:\Users\Admin\work\Develop\sudoku
build.bat
```

### Cách 2: Build thủ công
```bash
# 1. Kích hoạt virtual environment
venv\Scripts\activate

# 2. Cài đặt PyInstaller (nếu chưa có)
pip install pyinstaller

# 3. Build
pyinstaller --name=SudokuKDPGenerator --onefile --windowed --noconsole main.py
```

## Chi tiết đầy đủ

### Bước 1: Chuẩn bị môi trường

1. **Đảm bảo đã có virtual environment:**
   ```bash
   python -m venv venv
   ```

2. **Kích hoạt venv và cài dependencies:**
   ```bash
   venv\Scripts\activate
   pip install -r requirements.txt
   pip install pyinstaller pillow
   ```

### Bước 2: Build executable

**Cách đơn giản nhất:**
```bash
python build_exe.py
```

**Hoặc dùng PyInstaller trực tiếp với đầy đủ tham số:**
```bash
pyinstaller \
    --name=SudokuKDPGenerator \
    --onefile \
    --windowed \
    --noconsole \
    --clean \
    --hidden-import=reportlab \
    --hidden-import=reportlab.lib.colors \
    --hidden-import=reportlab.pdfgen.canvas \
    --hidden-import=reportlab.lib.pagesizes \
    --hidden-import=reportlab.lib.units \
    --hidden-import=reportlab.pdfbase.pdfmetrics \
    --hidden-import=reportlab.pdfbase.ttfonts \
    --hidden-import=PIL \
    --hidden-import=PIL.Image \
    --add-data="pdf_config.sample.json;." \
    --add-data="ic data;ic data" \
    --add-data="sudoku;sudoku" \
    main.py
```

### Bước 3: Kiểm tra và phân phối

Sau khi build xong:

1. **File exe nằm tại:** `dist\SudokuKDPGenerator.exe`

2. **Kiểm tra hoạt động:**
   ```bash
   cd dist
   SudokuKDPGenerator.exe
   ```

3. **Các file cần mang theo khi phân phối:**
   - `SudokuKDPGenerator.exe` (file chính)
   - `pdf_config.sample.json` (tùy chọn, để tham khảo)
   - Thư mục `ic data/` (nếu cần tài liệu tham khảo)

## Cấu trúc thư mục sau khi build

```
sudoku/
├── dist/
│   └── SudokuKDPGenerator.exe      <-- File chính để phân phối
├── build/                           (có thể xóa sau khi build)
├── venv/                            (không cần mang theo)
├── sudoku/                          (source code)
├── ic data/                         (tài liệu tham khảo)
├── pdf_config.sample.json           (file cấu hình mẫu)
├── main.py                          (entry point)
├── build_exe.py                     (script build)
├── build.bat                        (script build nhanh)
└── requirements.txt                 (dependencies)
```

## Lưu ý quan trọng

### 1. Dependencies bắt buộc
- `reportlab` - Tạo PDF
- `Pillow` (PIL) - Xử lý ảnh cho cover/icon
- `tkinter` - GUI (có sẵn trong Python Windows)

### 2. Vấn đề thường gặp

**Lỗi "No module named 'reportlab'":**
```bash
# Đảm bảo cài trong venv, không phải system Python
venv\Scripts\activate
pip install reportlab pillow
```

**File exe chạy không có GUI:**
- Đảm bảo dùng flag `--windowed` hoặc `--noconsole`

**Thiếu file data:**
- Kiểm tra `--add-data` đã include đúng path

### 3. File spec (nâng cao)

Nếu cần tùy chỉnh sâu, PyInstaller sẽ tạo file `.spec`. Bạn có thể:
```bash
pyinstaller sudoku.spec
```

## Phân phối cho người dùng khác

1. **Gói trong ZIP:**
   ```
   SudokuKDPGenerator-v1.0.zip
   ├── SudokuKDPGenerator.exe
   ├── pdf_config.sample.json
   └── README.txt
   ```

2. **Hướng dẫn người dùng:**
   - Giải nén vào thư mục
   - Chạy `SudokuKDPGenerator.exe`
   - Không cần cài Python
   - Có thể tạo shortcut ra desktop

3. **Antivirus false positive:**
   - Một số antivirus có thể cảnh báo với PyInstaller exe
   - Nên sign code nếu phân phối rộng rãi

## Nâng cao: Thêm icon

1. Tạo file icon `.ico` (kích thước: 256x256, 128x128, 64x64, 32x32, 16x16)
2. Thêm vào build command:
   ```bash
   --icon=icon.ico
   ```

## Build cho nhiều phiên bản

Script `build_all.bat`:
```batch
@echo off
for %%P in (3.9 3.10 3.11) do (
    echo Building for Python %%P...
    py -%%P -m venv venv%%P
    call venv%%P\Scripts\activate
    pip install -r requirements.txt pyinstaller
    pyinstaller --name=SudokuKDPGenerator-py%%P --onefile --windowed main.py
    deactivate
)
```
