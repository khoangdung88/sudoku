# Hướng dẫn sử dụng Sudoku KDP Generator

## 1) Tổng quan
Sudoku KDP Generator là ứng dụng desktop (Tkinter) giúp bạn:

- Tạo sẵn (pre-generate) **puzzle Sudoku** vào *Puzzle Pool*.
- Lấy puzzle từ Pool để **tạo sách Sudoku** (JSON + PDF) phục vụ xuất bản (ví dụ KDP).
- Tùy chỉnh **template PDF** (khổ giấy, margin, số puzzle/ trang, số đáp án/ trang, font, header, màu sắc…).
- **Regenerate** (tạo lại) sách đã tạo trước đó: dùng lại đúng các puzzle cũ, nhưng áp dụng template PDF hiện tại.

Dữ liệu Pool được lưu trong file `sudoku_pool.json` tại thư mục gốc project.

## 2) Khái niệm quan trọng: kích thước 2x2 và 3x3
Trong UI, lựa chọn kích thước thể hiện theo **kích thước khối con (subgrid/box)**:

- `2x2 (4 cells)` tương ứng **grid 4x4**.
- `3x3 (9 cells)` tương ứng **grid 9x9**.

Nói cách khác:

- 2x2 nghĩa là *mỗi box có 2 hàng x 2 cột*.
- 3x3 nghĩa là *mỗi box có 3 hàng x 3 cột*.

## 3) Tab "Puzzle Pool"
Dùng để tạo puzzle và lưu vào Pool để sau đó tạo sách nhanh hơn.

### 3.1 Chọn kích thước (multi-select)
- Bạn có thể chọn **nhiều kích thước** bằng:
  - Giữ `Ctrl` và click để chọn nhiều.

Hiện tại chương trình chỉ hỗ trợ 2 lựa chọn:

- `2x2 (4 cells)`
- `3x3 (9 cells)`

### 3.2 Count per difficulty
Bạn nhập số lượng puzzle muốn tạo cho từng độ khó:

- **Easy**
- **Medium**
- **Hard**

Ví dụ:

- Easy = 10, Medium = 10, Hard = 10
- Chọn `3x3`

=> Tạo tổng 30 puzzle 9x9 (10 easy + 10 medium + 10 hard) và lưu vào Pool.

### 3.3 Seed (tùy chọn)
- Tick **Enable** để bật seed.
- Nhập seed là số nguyên.

Seed giúp kết quả có tính lặp lại (useful khi bạn muốn debug hoặc tái tạo bộ puzzle tương tự).

### 3.4 Lesson mode
- **A (kỹ thuật)**: lesson theo kỹ thuật giải (ví dụ naked single, hidden single…)
- **B (cấp độ)**: lesson theo level (easy/medium/hard)
- **A + B**: kết hợp cả 2

### 3.5 Generate / Stop
- **Generate to Pool**: bắt đầu tạo puzzle theo cấu hình.
- **Stop**: dừng quá trình tạo.

Thanh progress và dòng trạng thái sẽ hiển thị tiến độ theo size + difficulty.

## 4) Tab "Create Book"
Dùng để lấy puzzle từ Pool và xuất ra file sách.

### 4.1 Pool Status (Available Puzzles)
Hiển thị:

- Tổng puzzle trong pool
- Đã dùng / còn dùng được
- Thống kê theo size & difficulty

Nút **Refresh** để cập nhật lại thống kê.

### 4.2 Created Books (Select to Regenerate)
Danh sách các sách đã tạo trước đó.

- Chọn 1 dòng trong list.
- Bấm **Regenerate Selected** để tạo lại PDF/JSON cho book đó.

Lưu ý:

- Book ID đã được làm unique (có uuid) để tránh 2 lần tạo gần nhau bị gộp thành 1.

### 4.3 Thiết lập tạo sách
- **Book Title**: tiêu đề sách (in vào PDF)
- **Grid Size**: chọn 4 hoặc 9 (tương ứng 2x2 hoặc 3x3)
- **Total Puzzles**: tổng số puzzle trong sách
- **Difficulty Mix (%)**: tỷ lệ % easy/medium/hard

Ví dụ:

- Total = 100
- Easy 34 / Medium 33 / Hard 33

=> chương trình sẽ cố lấy gần đúng tỉ lệ (có làm tròn).

### 4.4 Create Book
- Bấm **Create Book** để tạo:
  - File JSON (danh sách puzzle)
  - File PDF (sách puzzle + answer key)

Output được lưu trong thư mục:

- `output\<timestamp_folder>\...`

Tên file sẽ có tag theo box size (ví dụ `book_2x2_30.pdf`, `book_3x3_100.pdf`).

### 4.5 Lỗi thường gặp: Insufficient Pool
Nếu Pool không đủ puzzle theo mix bạn yêu cầu, chương trình sẽ báo:

- Cần X easy nhưng chỉ có Y
- Cần X medium nhưng chỉ có Y
...

Cách xử lý:

- Quay về tab **Puzzle Pool** và generate thêm đúng size + đúng difficulty.
- Hoặc chỉnh lại Difficulty Mix cho phù hợp với số puzzle đang có.

## 5) Tab "Settings (Paperback PDF)"
Dùng để cấu hình template PDF. Cài đặt sẽ được **auto-save** vào file settings JSON.

### 5.1 Pages bên trái
Chọn trang cấu hình:

- Book Settings
- Cover
- Title Page
- Copyright
- How to Play
- Puzzle Section
- Solutions
- Notes / CTA
- PDF Style
- Actions

### 5.2 Các setting quan trọng
- **Trim size** (khổ sách)
- **Orientation**
- **Margin**
- **Puzzles per page**
- **Answers per page**
- **Fonts** (label / digit)
- **Header** (bật/tắt, số trang, icon)
- **Colors**

### 5.3 Actions
- **Export PDF (manual)**: xuất PDF từ một JSON batch (khi bạn đã có JSON sẵn).

## 6) Regenerate (tạo lại) sách
Tính năng này dùng khi bạn muốn:

- Dùng lại đúng các puzzle của một sách đã tạo.
- Nhưng áp dụng **template PDF hiện tại**.

Cách dùng:

- Tab **Create Book**
- Trong **Created Books**, chọn 1 book
- Bấm **Regenerate Selected**

Kết quả:

- Tạo file `book_<book_id>_regenerated.json`
- Tạo file `book_<book_id>_regenerated.pdf`

## 7) Build ra file EXE (Windows)
Repo có `build.bat` để build EXE bằng PyInstaller.

Cách build:

1. Mở PowerShell tại thư mục project.
2. Chạy:

```bat
build.bat
```

Script sẽ:

- Tạo `venv` nếu chưa có
- Activate venv
- Cài dependencies: `pyinstaller reportlab pillow`
- Chạy `python build_exe.py`

Kết quả:

- File EXE ở: `dist\SudokuKDPGenerator.exe`

## 8) Files quan trọng
- `sudoku_pool.json`: lưu toàn bộ puzzle pool
- `output\...`: nơi chứa JSON/PDF đã xuất
- `pdf_config.sample.json` (nếu có): file mẫu settings

## 9) Checklist workflow nhanh
- Vào **Puzzle Pool**
  - Chọn `2x2` hoặc `3x3`
  - Nhập số lượng Easy/Medium/Hard
  - Generate
- Vào **Create Book**
  - Refresh Pool Status
  - Chọn Grid Size (4 hoặc 9)
  - Nhập Total + Mix
  - Create Book
- Vào **Settings**
  - Chỉnh template
  - Regenerate nếu cần áp template mới cho book cũ
