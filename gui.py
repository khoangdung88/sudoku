import json
import os
import threading
import tkinter as tk
import uuid
import traceback
from datetime import datetime
from tkinter import filedialog, messagebox, simpledialog, ttk
from tkinter import font as tkfont

from sudoku.batch import BatchConfig, BatchManager
from sudoku.lessons import LessonMode
from sudoku.pool import PuzzlePool


class AppState:
    def __init__(self) -> None:
        self.is_running = False


def run_app() -> None:
    root = tk.Tk()
    root.title("Sudoku KDP Generator")
    root.geometry("720x520")

    state = AppState()

    nb = ttk.Notebook(root)
    nb.pack(fill="both", expand=True)

    tab_pool = ttk.Frame(nb, padding=14)
    tab_book = ttk.Frame(nb, padding=14)
    tab_pdf = ttk.Frame(nb, padding=14)
    nb.add(tab_pool, text="Puzzle Pool")
    nb.add(tab_book, text="Create Book")
    nb.add(tab_pdf, text="Settings")

    output_base_dir = os.path.join(os.getcwd(), "output")
    book_output_dir_var = tk.StringVar(value=output_base_dir)

    lesson_mode_var = tk.StringVar(value=LessonMode.A_PLUS_B.value)
    total_var = tk.IntVar(value=100)

    easy_pct = tk.IntVar(value=34)
    med_pct = tk.IntVar(value=33)
    hard_pct = tk.IntVar(value=33)

    seed_enabled = tk.BooleanVar(value=False)
    seed_value = tk.StringVar(value="")
    grid_size_var = tk.IntVar(value=9)  # 4, 6, 9, 12, 16

    # Pool generation - multi-size and per-difficulty counts
    pool_gen_easy_count_var = tk.IntVar(value=10)
    pool_gen_med_count_var = tk.IntVar(value=10)
    pool_gen_hard_count_var = tk.IntVar(value=10)
    pool_gen_seed_enabled = tk.BooleanVar(value=False)
    pool_gen_seed_value = tk.StringVar(value="")
    pool_progress_var = tk.IntVar(value=0)
    pool_status_var = tk.StringVar(value="Idle")
    
    # Book-related variables
    book_easy_count_var = tk.IntVar(value=10)
    book_med_count_var = tk.IntVar(value=10)
    book_hard_count_var = tk.IntVar(value=10)
    book_size_var = tk.IntVar(value=9)
    book_title_var = tk.StringVar(value="Sudoku Book")
    book_progress_var = tk.IntVar(value=0)
    book_status_var = tk.StringVar(value="Idle")

    progress_var = tk.IntVar(value=0)
    status_var = tk.StringVar(value="Idle")

    pdf_trim_preset_var = tk.StringVar(value="8.5x11")
    pdf_orientation_var = tk.StringVar(value="portrait")
    pdf_margin_in_var = tk.DoubleVar(value=0.5)
    pdf_puzzles_per_page_var = tk.IntVar(value=4)
    pdf_answers_per_page_var = tk.IntVar(value=6)
    pdf_show_level_var = tk.BooleanVar(value=True)

    pdf_label_font_var = tk.StringVar(value="Helvetica")
    pdf_label_font_size_var = tk.IntVar(value=10)
    pdf_digit_font_var = tk.StringVar(value="Helvetica")
    pdf_digit_font_size_var = tk.IntVar(value=12)
    pdf_grid_line_width_var = tk.DoubleVar(value=0.6)
    pdf_subgrid_line_width_var = tk.DoubleVar(value=1.4)

    pdf_header_enabled_var = tk.BooleanVar(value=True)
    pdf_header_height_in_var = tk.DoubleVar(value=0.35)
    pdf_header_font_var = tk.StringVar(value="Helvetica")
    pdf_header_font_size_var = tk.IntVar(value=10)
    pdf_header_show_page_number_var = tk.BooleanVar(value=True)

    pdf_header_icon_path_var = tk.StringVar(value="")
    pdf_header_icon_height_in_var = tk.DoubleVar(value=0.22)

    pdf_custom_fonts: list[dict[str, str]] = []

    pdf_text_color_var = tk.StringVar(value="#000000")
    pdf_grid_color_var = tk.StringVar(value="#000000")
    pdf_header_line_color_var = tk.StringVar(value="#000000")

    pdf_title_var = tk.StringVar(value="Sudoku")
    pdf_author_var = tk.StringVar(value="")
    pdf_subject_var = tk.StringVar(value="")
    pdf_keywords_var = tk.StringVar(value="sudoku, puzzle")

    template_cover_enabled_var = tk.BooleanVar(value=False)
    template_cover_image_path_var = tk.StringVar(value="")

    template_title_enabled_var = tk.BooleanVar(value=True)
    template_title_title_var = tk.StringVar(value="Sudoku")
    template_title_image_path_var = tk.StringVar(value="")

    template_copyright_enabled_var = tk.BooleanVar(value=False)
    template_copyright_title_var = tk.StringVar(value="Copyright")
    template_copyright_image_path_var = tk.StringVar(value="")

    template_how_enabled_var = tk.BooleanVar(value=True)
    template_how_title_var = tk.StringVar(value="How to Play")
    template_how_image_path_var = tk.StringVar(value="")

    template_notes_enabled_var = tk.BooleanVar(value=False)
    template_notes_title_var = tk.StringVar(value="Notes / CTA")
    template_notes_image_path_var = tk.StringVar(value="")

    template_section_dividers_enabled_var = tk.BooleanVar(value=True)
    template_section_dividers_include_lesson_var = tk.BooleanVar(value=True)

    template_section_easy_title_var = tk.StringVar(value="Puzzle Section: Easy")
    template_section_easy_image_path_var = tk.StringVar(value="")
    template_section_medium_title_var = tk.StringVar(value="Puzzle Section: Medium")
    template_section_medium_image_path_var = tk.StringVar(value="")
    template_section_hard_title_var = tk.StringVar(value="Puzzle Section: Hard")
    template_section_hard_image_path_var = tk.StringVar(value="")

    pdf_template_data: dict[str, object] = {}
    template_widgets: dict[str, tk.Text] = {}

    pdf_progress_var = tk.IntVar(value=0)
    pdf_status_var = tk.StringVar(value="Idle")

    def pdf_settings_path() -> str:
        return os.path.join(os.getcwd(), "pdf_settings.json")

    def load_pdf_settings_into_vars() -> None:
        path = pdf_settings_path()
        if not os.path.exists(path):
            pdf_status_var.set(f"No settings file: {path}")
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                d = json.load(f)

            pdf_trim_preset_var.set(str(d.get("trim_size", pdf_trim_preset_var.get())))
            pdf_orientation_var.set(str(d.get("orientation", pdf_orientation_var.get())))
            pdf_margin_in_var.set(float(d.get("margin_in", float(pdf_margin_in_var.get()))))
            pdf_puzzles_per_page_var.set(int(d.get("puzzles_per_page", int(pdf_puzzles_per_page_var.get()))))
            pdf_answers_per_page_var.set(int(d.get("answers_per_page", int(pdf_answers_per_page_var.get()))))
            pdf_show_level_var.set(bool(d.get("show_level", bool(pdf_show_level_var.get()))))

            pdf_label_font_var.set(str(d.get("label_font", pdf_label_font_var.get())))
            pdf_label_font_size_var.set(int(d.get("label_font_size", int(pdf_label_font_size_var.get()))))
            pdf_digit_font_var.set(str(d.get("digit_font", pdf_digit_font_var.get())))
            pdf_digit_font_size_var.set(int(d.get("digit_font_size", int(pdf_digit_font_size_var.get()))))
            pdf_grid_line_width_var.set(float(d.get("grid_line_width", float(pdf_grid_line_width_var.get()))))
            pdf_subgrid_line_width_var.set(
                float(d.get("subgrid_line_width", float(pdf_subgrid_line_width_var.get())))
            )

            pdf_header_enabled_var.set(bool(d.get("header_enabled", bool(pdf_header_enabled_var.get()))))
            pdf_header_height_in_var.set(float(d.get("header_height_in", float(pdf_header_height_in_var.get()))))
            pdf_header_font_var.set(str(d.get("header_font", pdf_header_font_var.get())))
            pdf_header_font_size_var.set(int(d.get("header_font_size", int(pdf_header_font_size_var.get()))))
            pdf_header_show_page_number_var.set(
                bool(d.get("header_show_page_number", bool(pdf_header_show_page_number_var.get())))
            )

            pdf_header_icon_path_var.set(str(d.get("header_icon_path", pdf_header_icon_path_var.get())))
            pdf_header_icon_height_in_var.set(
                float(d.get("header_icon_height_in", float(pdf_header_icon_height_in_var.get())))
            )

            nonlocal pdf_custom_fonts
            raw_fonts = d.get("custom_fonts", [])
            if isinstance(raw_fonts, list):
                pdf_custom_fonts = [x for x in raw_fonts if isinstance(x, dict) and "name" in x and "path" in x]
            else:
                pdf_custom_fonts = []

            pdf_text_color_var.set(str(d.get("text_color", pdf_text_color_var.get())))
            pdf_grid_color_var.set(str(d.get("grid_color", pdf_grid_color_var.get())))
            pdf_header_line_color_var.set(str(d.get("header_line_color", pdf_header_line_color_var.get())))

            pdf_title_var.set(str(d.get("pdf_title", pdf_title_var.get())))
            pdf_author_var.set(str(d.get("pdf_author", pdf_author_var.get())))
            pdf_subject_var.set(str(d.get("pdf_subject", pdf_subject_var.get())))
            pdf_keywords_var.set(str(d.get("pdf_keywords", pdf_keywords_var.get())))

            nonlocal pdf_template_data
            t = d.get("template", {})
            pdf_template_data = dict(t) if isinstance(t, dict) else {}

            pdf_status_var.set("Settings loaded")
        except Exception as e:
            pdf_status_var.set("Error")
            messagebox.showerror("Error", f"Failed to load PDF settings: {e}")

    def clamp_pcts() -> None:
        e = max(0, min(100, easy_pct.get()))
        m = max(0, min(100, med_pct.get()))
        h = max(0, min(100, hard_pct.get()))
        s = e + m + h
        if s == 0:
            e, m, h = 34, 33, 33
            s = 100
        if s != 100:
            scale = 100 / s
            e = int(round(e * scale))
            m = int(round(m * scale))
            h = 100 - e - m
        easy_pct.set(e)
        med_pct.set(m)
        hard_pct.set(h)

    def ask_pdf_input_json() -> str:
        path = filedialog.askopenfilename(
            title="Choose sudoku batch JSON",
            filetypes=[("JSON", "*.json")],
        )
        return path or ""

    def make_timestamp_folder_name() -> str:
        now = datetime.now()
        return f"{now.second:02d}_{now.minute:02d}_{now.hour:02d}_{now.day:02d}_{now.month:02d}"

    def lesson_mode_name(mode: LessonMode) -> str:
        if mode == LessonMode.A:
            return "A - Theo kỹ thuật giải"
        if mode == LessonMode.B:
            return "B - Theo cấp độ (Easy/Medium/Hard)"
        return "A + B - Kết hợp kỹ thuật + cấp độ"

    def set_running(running: bool) -> None:
        state.is_running = running
        gen_btn["state"] = "disabled" if running else "normal"
        stop_btn["state"] = "normal" if running else "disabled"

    def set_pdf_running(running: bool) -> None:
        pdf_export_btn["state"] = "disabled" if running else "normal"

    stop_flag = {"stop": False}

    def stop() -> None:
        stop_flag["stop"] = True
        status_var.set("Stopping...")

    def generate_in_thread() -> None:
        if state.is_running:
            return

        clamp_pcts()

        total = total_var.get()
        if total <= 0:
            messagebox.showerror("Invalid", "Total puzzles must be > 0")
            return

        out_base = output_base_dir

        seed = None
        if seed_enabled.get():
            sv = seed_value.get().strip()
            if not sv:
                messagebox.showerror("Invalid", "Seed enabled but seed is empty")
                return
            try:
                seed = int(sv)
            except ValueError:
                messagebox.showerror("Invalid", "Seed must be an integer")
                return

        mode = LessonMode(lesson_mode_var.get())

        config = BatchConfig(
            total=total,
            easy_percent=easy_pct.get(),
            medium_percent=med_pct.get(),
            hard_percent=hard_pct.get(),
            seed=seed,
            lesson_mode=mode,
            grid_size=grid_size_var.get(),
        )

        stop_flag["stop"] = False
        progress_var.set(0)
        status_var.set("Generating...")
        set_running(True)

        def on_progress(done: int, total_n: int, msg: str) -> None:
            def _update() -> None:
                if total_n > 0:
                    progress_var.set(int(done * 100 / total_n))
                status_var.set(msg)

            root.after(0, _update)

        def worker() -> None:
            try:
                mgr = BatchManager()
                batch = mgr.generate(config, on_progress=on_progress, stop_flag=stop_flag)

                ts_folder = make_timestamp_folder_name()
                out_dir = os.path.join(out_base, ts_folder)
                os.makedirs(out_dir, exist_ok=True)

                seed_part = "noseed" if config.seed is None else f"seed{config.seed}"
                safe_mode = config.lesson_mode.value.replace("+", "plus")
                out_path = os.path.join(out_dir, f"sudoku_{config.total}_{safe_mode}_{seed_part}.json")

                payload = {
                    "config": {
                        "total": config.total,
                        "grid_size": config.grid_size,
                        "easy_percent": config.easy_percent,
                        "medium_percent": config.medium_percent,
                        "hard_percent": config.hard_percent,
                        "seed": config.seed,
                        "lesson_mode": config.lesson_mode.value,
                        "lesson_mode_name": lesson_mode_name(config.lesson_mode),
                    },
                    "items": [item.to_dict() for item in batch],
                }
                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump(payload, f, ensure_ascii=False, indent=2)

                pdf_path = os.path.join(out_dir, "sudoku_book.pdf")
                pdf_settings_file = pdf_settings_path()
                if not os.path.exists(pdf_settings_file):
                    raise RuntimeError(
                        f"PDF settings not found: {pdf_settings_file}. Please open Export PDF tab and click Save Settings once."
                    )

                with open(pdf_settings_file, "r", encoding="utf-8") as pf:
                    s = json.load(pf)

                page_w, page_h = get_trim_size(str(s.get("trim_size", "8.5x11")))
                cfg_dict = {
                    "page_width_in": page_w,
                    "page_height_in": page_h,
                    "orientation": str(s.get("orientation", "portrait")),
                    "margin_in": float(s.get("margin_in", 0.5)),
                    "puzzles_per_page": int(s.get("puzzles_per_page", 4)),
                    "show_level": bool(s.get("show_level", True)),
                    "level_field": "difficulty",
                    "title": str(s.get("pdf_title", "Sudoku")),
                    "answer_key_title": "Answer Key",
                    "answers_per_page": int(s.get("answers_per_page", 6)),
                    "label_font": str(s.get("label_font", "Helvetica")),
                    "label_font_size": int(s.get("label_font_size", 10)),
                    "digit_font": str(s.get("digit_font", "Helvetica")),
                    "digit_font_size": int(s.get("digit_font_size", 12)),
                    "grid_line_width": float(s.get("grid_line_width", 0.6)),
                    "subgrid_line_width": float(s.get("subgrid_line_width", 1.4)),
                    "header_enabled": bool(s.get("header_enabled", True)),
                    "header_height_in": float(s.get("header_height_in", 0.35)),
                    "header_font": str(s.get("header_font", "Helvetica")),
                    "header_font_size": int(s.get("header_font_size", 10)),
                    "header_show_page_number": bool(s.get("header_show_page_number", True)),
                    "header_icon_path": str(s.get("header_icon_path", "")),
                    "header_icon_height_in": float(s.get("header_icon_height_in", 0.22)),
                    "custom_fonts": list(s.get("custom_fonts", [])) if isinstance(s.get("custom_fonts", []), list) else [],
                    "text_color": str(s.get("text_color", "#000000")),
                    "grid_color": str(s.get("grid_color", "#000000")),
                    "header_line_color": str(s.get("header_line_color", "#000000")),
                    "pdf_title": str(s.get("pdf_title", "Sudoku")),
                    "pdf_author": str(s.get("pdf_author", "")),
                    "pdf_subject": str(s.get("pdf_subject", "")),
                    "pdf_keywords": str(s.get("pdf_keywords", "sudoku, puzzle")),
                    "template": dict(s.get("template", {})) if isinstance(s.get("template", {}), dict) else {},
                }

                from sudoku.pdf_export import ExportConfig, export_sudoku_json_to_pdf

                export_sudoku_json_to_pdf(out_path, pdf_path, ExportConfig.from_dict(cfg_dict))

                def _done_ok() -> None:
                    set_running(False)
                    progress_var.set(100)
                    status_var.set(f"Done: {len(batch)} puzzles")
                    messagebox.showinfo(
                        "Done",
                        f"Generated {len(batch)} puzzles\nSaved JSON: {out_path}\nSaved PDF: {pdf_path}",
                    )

                root.after(0, _done_ok)
            except Exception as e:
                def _done_err() -> None:
                    set_running(False)
                    status_var.set("Error")
                    messagebox.showerror("Error", str(e))

                root.after(0, _done_err)

        threading.Thread(target=worker, daemon=True).start()

    def get_trim_size(preset: str) -> tuple[float, float]:
        p = preset.strip().lower().replace(" ", "")
        if p == "6x9":
            return 6.0, 9.0
        if p == "8.5x11" or p == "8.5x11.0":
            return 8.5, 11.0
        if "x" in p:
            a, b = p.split("x", 1)
            return float(a), float(b)
        raise ValueError("Invalid trim size preset")

    def export_pdf_in_thread() -> None:
        in_json = ask_pdf_input_json()
        if not in_json:
            return
        if not os.path.exists(in_json):
            messagebox.showerror("Missing input", "Input sudoku JSON not found")
            return

        out_base = output_base_dir

        try:
            page_w, page_h = get_trim_size(pdf_trim_preset_var.get())
        except Exception as e:
            messagebox.showerror("Invalid", str(e))
            return

        cfg_dict = {
            "page_width_in": page_w,
            "page_height_in": page_h,
            "orientation": pdf_orientation_var.get().strip() or "portrait",
            "margin_in": float(pdf_margin_in_var.get()),
            "puzzles_per_page": int(pdf_puzzles_per_page_var.get()),
            "show_level": bool(pdf_show_level_var.get()),
            "level_field": "difficulty",
            "title": pdf_title_var.get().strip() or "Sudoku",
            "answer_key_title": "Answer Key",
            "answers_per_page": int(pdf_answers_per_page_var.get()),
            "label_font": pdf_label_font_var.get().strip() or "Helvetica",
            "label_font_size": int(pdf_label_font_size_var.get()),
            "digit_font": pdf_digit_font_var.get().strip() or "Helvetica",
            "digit_font_size": int(pdf_digit_font_size_var.get()),
            "grid_line_width": float(pdf_grid_line_width_var.get()),
            "subgrid_line_width": float(pdf_subgrid_line_width_var.get()),
            "header_enabled": bool(pdf_header_enabled_var.get()),
            "header_height_in": float(pdf_header_height_in_var.get()),
            "header_font": pdf_header_font_var.get().strip() or "Helvetica",
            "header_font_size": int(pdf_header_font_size_var.get()),
            "header_show_page_number": bool(pdf_header_show_page_number_var.get()),
            "header_icon_path": pdf_header_icon_path_var.get().strip(),
            "header_icon_height_in": float(pdf_header_icon_height_in_var.get()),
            "custom_fonts": pdf_custom_fonts,
            "text_color": pdf_text_color_var.get().strip() or "#000000",
            "grid_color": pdf_grid_color_var.get().strip() or "#000000",
            "header_line_color": pdf_header_line_color_var.get().strip() or "#000000",
            "pdf_title": pdf_title_var.get().strip() or "Sudoku",
            "pdf_author": pdf_author_var.get().strip(),
            "pdf_subject": pdf_subject_var.get().strip(),
            "pdf_keywords": pdf_keywords_var.get().strip(),
            "template": {
                "cover": {
                    "enabled": bool(template_cover_enabled_var.get()),
                    "image_path": template_cover_image_path_var.get().strip(),
                },
                "title_page": {
                    "enabled": bool(template_title_enabled_var.get()),
                    "title": template_title_title_var.get().strip() or pdf_title_var.get().strip() or "Sudoku",
                    "image_path": template_title_image_path_var.get().strip(),
                    "body": template_widgets.get("title_body").get("1.0", "end").rstrip("\n") if template_widgets.get("title_body") else "",
                },
                "copyright": {
                    "enabled": bool(template_copyright_enabled_var.get()),
                    "title": template_copyright_title_var.get().strip() or "Copyright",
                    "image_path": template_copyright_image_path_var.get().strip(),
                    "body": template_widgets.get("copyright_body").get("1.0", "end").rstrip("\n") if template_widgets.get("copyright_body") else "",
                },
                "how_to_play": {
                    "enabled": bool(template_how_enabled_var.get()),
                    "title": template_how_title_var.get().strip() or "How to Play",
                    "image_path": template_how_image_path_var.get().strip(),
                    "body": template_widgets.get("how_body").get("1.0", "end").rstrip("\n") if template_widgets.get("how_body") else "",
                },
                "notes_cta": {
                    "enabled": bool(template_notes_enabled_var.get()),
                    "title": template_notes_title_var.get().strip() or "Notes / CTA",
                    "image_path": template_notes_image_path_var.get().strip(),
                    "body": template_widgets.get("notes_body").get("1.0", "end").rstrip("\n") if template_widgets.get("notes_body") else "",
                },
                "section_dividers": {
                    "enabled": bool(template_section_dividers_enabled_var.get()),
                    "include_level_lesson": bool(template_section_dividers_include_lesson_var.get()),
                    "easy": {
                        "title": template_section_easy_title_var.get().strip() or "Puzzle Section: Easy",
                        "body": template_widgets.get("section_easy_body").get("1.0", "end").rstrip("\n")
                        if template_widgets.get("section_easy_body")
                        else "",
                        "image_path": template_section_easy_image_path_var.get().strip(),
                    },
                    "medium": {
                        "title": template_section_medium_title_var.get().strip() or "Puzzle Section: Medium",
                        "body": template_widgets.get("section_medium_body").get("1.0", "end").rstrip("\n")
                        if template_widgets.get("section_medium_body")
                        else "",
                        "image_path": template_section_medium_image_path_var.get().strip(),
                    },
                    "hard": {
                        "title": template_section_hard_title_var.get().strip() or "Puzzle Section: Hard",
                        "body": template_widgets.get("section_hard_body").get("1.0", "end").rstrip("\n")
                        if template_widgets.get("section_hard_body")
                        else "",
                        "image_path": template_section_hard_image_path_var.get().strip(),
                    },
                },
            },
        }

        pdf_progress_var.set(0)
        pdf_status_var.set("Exporting...")
        set_pdf_running(True)

        def worker() -> None:
            try:
                from sudoku.pdf_export import ExportConfig, export_sudoku_json_to_pdf

                ts_folder = make_timestamp_folder_name()
                out_dir = os.path.join(out_base, ts_folder)
                os.makedirs(out_dir, exist_ok=True)
                out_path = os.path.join(out_dir, "sudoku_book.pdf")

                cfg = ExportConfig.from_dict(cfg_dict)
                export_sudoku_json_to_pdf(in_json, out_path, cfg)

                def _done_ok() -> None:
                    set_pdf_running(False)
                    pdf_progress_var.set(100)
                    pdf_status_var.set(f"Done: {out_path}")
                    messagebox.showinfo("Done", f"Exported PDF\nSaved: {out_path}")

                root.after(0, _done_ok)
            except Exception as e:
                def _done_err() -> None:
                    set_pdf_running(False)
                    pdf_status_var.set("Error")
                    messagebox.showerror("Error", str(e))

                root.after(0, _done_err)

        threading.Thread(target=worker, daemon=True).start()

    # Puzzle Pool functions
    pool_stop_flag = {"stop": False}

    def stop_pool_gen() -> None:
        pool_stop_flag["stop"] = True
        pool_status_var.set("Stopping...")

    def generate_pool_in_thread() -> None:
        if state.is_running:
            return

        # Get selected sizes
        selected_indices = size_listbox.curselection()
        if not selected_indices:
            messagebox.showerror("Invalid", "Please select at least one grid size")
            return
        
        sizes = [[4, 9][i] for i in selected_indices]
        
        # Get counts per difficulty
        easy_count = pool_gen_easy_count_var.get()
        med_count = pool_gen_med_count_var.get()
        hard_count = pool_gen_hard_count_var.get()
        
        total_per_size = easy_count + med_count + hard_count
        if total_per_size <= 0:
            messagebox.showerror("Invalid", "Total puzzles per size must be > 0")
            return
        
        # Build generation plan: [(size, difficulty, count), ...]
        plan = []
        for size in sizes:
            if easy_count > 0:
                plan.append((size, "easy", easy_count))
            if med_count > 0:
                plan.append((size, "medium", med_count))
            if hard_count > 0:
                plan.append((size, "hard", hard_count))
        
        total_to_generate = sum(count for _, _, count in plan)

        seed = None
        if pool_gen_seed_enabled.get():
            sv = pool_gen_seed_value.get().strip()
            if not sv:
                messagebox.showerror("Invalid", "Seed enabled but seed is empty")
                return
            try:
                seed = int(sv)
            except ValueError:
                messagebox.showerror("Invalid", "Seed must be an integer")
                return

        mode = LessonMode(lesson_mode_var.get())
        pool_stop_flag["stop"] = False
        pool_progress_var.set(0)
        pool_status_var.set(f"Generating {total_to_generate} puzzles for {len(sizes)} size(s)...")
        state.is_running = True
        gen_btn["state"] = "disabled"
        stop_btn["state"] = "normal"

        def on_progress(done: int, total_n: int, msg: str) -> None:
            def _update() -> None:
                if total_n > 0:
                    pool_progress_var.set(int(done * 100 / total_n))
                pool_status_var.set(msg)
            root.after(0, _update)

        def worker() -> None:
            try:
                pool = PuzzlePool()
                total_added = 0
                current = 0
                
                for size, difficulty, count in plan:
                    if pool_stop_flag.get("stop"):
                        break
                    
                    size_tag_map = {4: "2x2", 9: "3x3"}
                    added = pool.generate_to_pool(
                        size=size,
                        difficulty=difficulty,
                        count=count,
                        seed=seed,
                        lesson_mode=mode,
                        on_progress=lambda done, total, msg: on_progress(
                            current + done, total_to_generate, 
                            f"{size_tag_map.get(size, str(size))} {difficulty}: {done}/{count}"
                        ),
                        stop_flag=pool_stop_flag,
                    )
                    total_added += added
                    current += count

                def _done_ok() -> None:
                    state.is_running = False
                    gen_btn["state"] = "normal"
                    stop_btn["state"] = "disabled"
                    pool_progress_var.set(100)
                    pool_status_var.set(f"Done: Added {total_added} puzzles to pool")
                    messagebox.showinfo("Done", f"Added {total_added} puzzles to pool ({len(sizes)} size(s))")
                    refresh_pool_status()

                root.after(0, _done_ok)
            except Exception as e:
                tb = traceback.format_exc()

                def _done_err(err: Exception = e, err_tb: str = tb) -> None:
                    state.is_running = False
                    gen_btn["state"] = "normal"
                    stop_btn["state"] = "disabled"
                    pool_status_var.set("Error")
                    messagebox.showerror("Error", f"{err}\n\n{err_tb}")

                root.after(0, _done_err)

        threading.Thread(target=worker, daemon=True).start()

    def create_book_in_thread() -> None:
        if state.is_running:
            return

        e_n = max(0, book_easy_count_var.get())
        m_n = max(0, book_med_count_var.get())
        h_n = max(0, book_hard_count_var.get())
        total = e_n + m_n + h_n
        if total <= 0:
            messagebox.showerror("Invalid", "Total puzzles must be > 0")
            return

        size = book_size_var.get()
        size_tag_map = {4: "2x2", 9: "3x3"}
        size_tag = size_tag_map.get(size, f"{size}x{size}")
        
        # Check pool availability
        pool = PuzzlePool()
        counts = pool.get_counts()
        size_counts = counts.get(str(size), {})
        
        available_easy = size_counts.get("easy", 0)
        available_med = size_counts.get("medium", 0)
        available_hard = size_counts.get("hard", 0)
        
        warnings = []
        if e_n > available_easy:
            warnings.append(f"Need {e_n} easy, only {available_easy} available")
        if m_n > available_med:
            warnings.append(f"Need {m_n} medium, only {available_med} available")
        if h_n > available_hard:
            warnings.append(f"Need {h_n} hard, only {available_hard} available")
        
        if warnings:
            message = "Insufficient puzzles in pool:\n" + "\n".join(warnings)
            message += "\n\nPlease generate more puzzles in the Puzzle Pool tab first."
            messagebox.showerror("Insufficient Pool", message)
            return

        book_progress_var.set(0)
        book_status_var.set("Creating book...")
        state.is_running = True
        create_book_btn["state"] = "disabled"

        def worker() -> None:
            try:
                out_base = book_output_dir_var.get().strip() or output_base_dir
                ts_folder = make_timestamp_folder_name()
                out_dir = os.path.join(out_base, ts_folder)
                os.makedirs(out_dir, exist_ok=True)

                # Get puzzles from pool
                book_id = f"book_{ts_folder}_{uuid.uuid4().hex[:8]}"
                puzzles = []
                
                if e_n > 0:
                    easy_items = pool.get_available(size, "easy", e_n, mark_used=True, book_id=book_id)
                    puzzles.extend([item.to_dict() for item in easy_items])
                if m_n > 0:
                    med_items = pool.get_available(size, "medium", m_n, mark_used=True, book_id=book_id)
                    puzzles.extend([item.to_dict() for item in med_items])
                if h_n > 0:
                    hard_items = pool.get_available(size, "hard", h_n, mark_used=True, book_id=book_id)
                    puzzles.extend([item.to_dict() for item in hard_items])

                # Save JSON
                json_path = os.path.join(out_dir, f"book_{size_tag}_{total}.json")
                payload = {
                    "config": {
                        "total": len(puzzles),
                        "grid_size": size,
                        "easy_count": e_n,
                        "medium_count": m_n,
                        "hard_count": h_n,
                        "book_id": book_id,
                    },
                    "items": puzzles,
                }
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(payload, f, ensure_ascii=False, indent=2)

                # Generate PDF
                pdf_path = os.path.join(out_dir, f"book_{size_tag}_{total}.pdf")
                pdf_settings_file = pdf_settings_path()
                
                with open(pdf_settings_file, "r", encoding="utf-8") as pf:
                    s = json.load(pf)

                page_w, page_h = get_trim_size(str(s.get("trim_size", "8.5x11")))
                cfg_dict = {
                    "page_width_in": page_w,
                    "page_height_in": page_h,
                    "orientation": str(s.get("orientation", "portrait")),
                    "margin_in": float(s.get("margin_in", 0.5)),
                    "puzzles_per_page": int(s.get("puzzles_per_page", 4)),
                    "show_level": bool(s.get("show_level", True)),
                    "level_field": "difficulty",
                    "title": book_title_var.get() or "Sudoku Book",
                    "answer_key_title": "Answer Key",
                    "answers_per_page": int(s.get("answers_per_page", 6)),
                    "label_font": str(s.get("label_font", "Helvetica")),
                    "label_font_size": int(s.get("label_font_size", 10)),
                    "digit_font": str(s.get("digit_font", "Helvetica")),
                    "digit_font_size": int(s.get("digit_font_size", 12)),
                    "grid_line_width": float(s.get("grid_line_width", 0.6)),
                    "subgrid_line_width": float(s.get("subgrid_line_width", 1.4)),
                    "header_enabled": bool(s.get("header_enabled", True)),
                    "header_height_in": float(s.get("header_height_in", 0.35)),
                    "header_font": str(s.get("header_font", "Helvetica")),
                    "header_font_size": int(s.get("header_font_size", 10)),
                    "header_show_page_number": bool(s.get("header_show_page_number", True)),
                    "header_icon_path": str(s.get("header_icon_path", "")),
                    "header_icon_height_in": float(s.get("header_icon_height_in", 0.22)),
                    "custom_fonts": list(s.get("custom_fonts", [])) if isinstance(s.get("custom_fonts", []), list) else [],
                    "text_color": str(s.get("text_color", "#000000")),
                    "grid_color": str(s.get("grid_color", "#000000")),
                    "header_line_color": str(s.get("header_line_color", "#000000")),
                    "pdf_title": book_title_var.get() or "Sudoku Book",
                    "pdf_author": str(s.get("pdf_author", "")),
                    "pdf_subject": str(s.get("pdf_subject", "")),
                    "pdf_keywords": str(s.get("pdf_keywords", "sudoku, puzzle")),
                    "template": dict(s.get("template", {})) if isinstance(s.get("template", {}), dict) else {},
                }

                from sudoku.pdf_export import ExportConfig, export_sudoku_json_to_pdf
                export_sudoku_json_to_pdf(json_path, pdf_path, ExportConfig.from_dict(cfg_dict))

                def _done_ok() -> None:
                    state.is_running = False
                    create_book_btn["state"] = "normal"
                    book_progress_var.set(100)
                    book_status_var.set(f"Done: {len(puzzles)} puzzles")
                    refresh_pool_status()
                    messagebox.showinfo(
                        "Done",
                        f"Created book ({size_tag}) with {len(puzzles)} puzzles\nJSON: {json_path}\nPDF: {pdf_path}",
                    )
                    try:
                        os.startfile(pdf_path)
                    except Exception:
                        pass

                root.after(0, _done_ok)
            except Exception as e:
                tb = traceback.format_exc()

                def _done_err(err: Exception = e, err_tb: str = tb) -> None:
                    state.is_running = False
                    create_book_btn["state"] = "normal"
                    book_status_var.set("Error")
                    messagebox.showerror("Error", f"{err}\n\n{err_tb}")

                root.after(0, _done_err)

        threading.Thread(target=worker, daemon=True).start()

    frm = ttk.Frame(tab_pool)
    frm.pack(fill="both", expand=True)

    title = ttk.Label(frm, text="Puzzle Pool - Generate Sudoku to Pool", font=("Segoe UI", 16, "bold"))
    title.pack(anchor="w")

    ttk.Separator(frm).pack(fill="x", pady=10)

    grid = ttk.Frame(frm)
    grid.pack(fill="x")

    # Grid sizes - multi select with subgrid labels
    ttk.Label(grid, text="Grid sizes (Ctrl+Click multi-select)").grid(row=0, column=0, sticky="nw", padx=2, pady=6)
    size_listbox = tk.Listbox(grid, height=7, selectmode="multiple", exportselection=False)
    size_listbox.grid(row=0, column=1, sticky="w", pady=6)
    # Format: (display_label, actual_size)
    size_options = [
        ("2x2 (4 cells)", 4),
        ("3x3 (9 cells)", 9),
    ]
    for label, size in size_options:
        size_listbox.insert(tk.END, label)
    # Select 2x2 by default
    size_listbox.selection_set(0)

    # Count per difficulty
    ttk.Label(grid, text="Count per difficulty").grid(row=1, column=0, sticky="w", padx=2, pady=6)
    diff_frame = ttk.Frame(grid)
    diff_frame.grid(row=1, column=1, sticky="w", pady=6)
    
    ttk.Label(diff_frame, text="Easy:").pack(side="left")
    ttk.Entry(diff_frame, textvariable=pool_gen_easy_count_var, width=6).pack(side="left", padx=4)
    ttk.Label(diff_frame, text="Medium:").pack(side="left", padx=(10, 0))
    ttk.Entry(diff_frame, textvariable=pool_gen_med_count_var, width=6).pack(side="left", padx=4)
    ttk.Label(diff_frame, text="Hard:").pack(side="left", padx=(10, 0))
    ttk.Entry(diff_frame, textvariable=pool_gen_hard_count_var, width=6).pack(side="left", padx=4)

    ttk.Label(grid, text="Seed (optional)").grid(row=2, column=0, sticky="w", padx=2, pady=6)
    seed_row = ttk.Frame(grid)
    seed_row.grid(row=2, column=1, sticky="w")
    ttk.Checkbutton(seed_row, text="Enable", variable=pool_gen_seed_enabled).pack(side="left")
    ttk.Entry(seed_row, textvariable=pool_gen_seed_value, width=16).pack(side="left", padx=8)

    ttk.Label(grid, text="Lesson mode").grid(row=3, column=0, sticky="w", padx=2, pady=6)
    lesson_box = ttk.Frame(grid)
    lesson_box.grid(row=3, column=1, sticky="w")
    ttk.Radiobutton(lesson_box, text="A (kỹ thuật)", variable=lesson_mode_var, value=LessonMode.A.value).pack(side="left", padx=6)
    ttk.Radiobutton(lesson_box, text="B (cấp độ)", variable=lesson_mode_var, value=LessonMode.B.value).pack(side="left", padx=6)
    ttk.Radiobutton(lesson_box, text="A + B (kết hợp)", variable=lesson_mode_var, value=LessonMode.A_PLUS_B.value).pack(side="left", padx=6)

    ttk.Separator(frm).pack(fill="x", pady=12)

    btns = ttk.Frame(frm)
    btns.pack(fill="x")
    gen_btn = ttk.Button(btns, text="Generate to Pool", command=generate_pool_in_thread)
    gen_btn.pack(side="left")
    stop_btn = ttk.Button(btns, text="Stop", command=stop_pool_gen)
    stop_btn.pack(side="left", padx=10)
    stop_btn["state"] = "disabled"

    prog = ttk.Progressbar(frm, orient="horizontal", maximum=100, variable=pool_progress_var)
    prog.pack(fill="x", pady=12)

    status = ttk.Label(frm, textvariable=pool_status_var)
    status.pack(anchor="w")

    # Create Book Tab with scrolling canvas
    book_canvas = tk.Canvas(tab_book)
    book_scroll = ttk.Scrollbar(tab_book, orient="vertical", command=book_canvas.yview)
    book_frm = ttk.Frame(book_canvas)
    
    book_frm.bind(
        "<Configure>",
        lambda e: book_canvas.configure(scrollregion=book_canvas.bbox("all"))
    )
    
    book_canvas.create_window((0, 0), window=book_frm, anchor="nw")
    book_canvas.configure(yscrollcommand=book_scroll.set)
    
    book_canvas.pack(side="left", fill="both", expand=True)
    book_scroll.pack(side="right", fill="y")

    book_title_lbl = ttk.Label(book_frm, text="Create Book from Pool", font=("Segoe UI", 16, "bold"))
    book_title_lbl.pack(anchor="w")

    ttk.Separator(book_frm).pack(fill="x", pady=10)

    # Pool status display with scrollbar
    pool_status_frame = ttk.LabelFrame(book_frm, text="Pool Status (Available Puzzles)")
    pool_status_frame.pack(fill="x", pady=(0, 10))
    
    pool_status_scroll = ttk.Scrollbar(pool_status_frame)
    pool_status_scroll.pack(side="right", fill="y")
    
    pool_status_text = tk.Text(pool_status_frame, height=6, wrap="word", yscrollcommand=pool_status_scroll.set)
    pool_status_text.pack(fill="x", padx=5, pady=5)
    pool_status_text.config(state="disabled")
    pool_status_scroll.config(command=pool_status_text.yview)

    def refresh_pool_status():
        pool = PuzzlePool()
        counts = pool.get_counts()
        stats = pool.get_stats()
        
        # Size to subgrid label mapping
        size_labels = {
            4: "2x2 (4 cells)",
            9: "3x3 (9 cells)",
        }
        
        lines = [f"Total in pool: {stats['total']} | Used: {stats['used']} | Available: {stats['unused']}", ""]
        lines.append("Available by size and difficulty:")
        
        for size in [4, 9]:
            size_key = str(size)
            data = counts.get(size_key, {})
            total = data.get("total", 0)
            if total > 0:
                easy = data.get("easy", 0)
                medium = data.get("medium", 0)
                hard = data.get("hard", 0)
                label = size_labels.get(size, f"{size}x{size}")
                lines.append(f"  {label}: {total} total (Easy: {easy}, Medium: {medium}, Hard: {hard})")
        
        pool_status_text.config(state="normal")
        pool_status_text.delete("1.0", "end")
        pool_status_text.insert("1.0", "\n".join(lines))
        pool_status_text.config(state="disabled")

    ttk.Button(pool_status_frame, text="Refresh", command=refresh_pool_status).pack(anchor="w", padx=5, pady=(0, 5))

    # Created Books List with scrollbar
    books_frame = ttk.LabelFrame(book_frm, text="Created Books (Select to Regenerate)")
    books_frame.pack(fill="x", pady=(0, 10))

    books_scroll = ttk.Scrollbar(books_frame)
    books_scroll.pack(side="right", fill="y")

    books_listbox = tk.Listbox(books_frame, height=5, yscrollcommand=books_scroll.set)
    books_listbox.pack(fill="x", padx=5, pady=5)
    books_scroll.config(command=books_listbox.yview)

    selected_book_id_var = tk.StringVar(value="")

    def refresh_books_list():
        books_listbox.delete(0, tk.END)
        pool = PuzzlePool()
        books = pool.get_books()
        for book in books:
            book_id = book["book_id"]
            created_at = book["created_at"][:16] if book["created_at"] else "unknown"  # trim to minutes
            total = book["total"]
            sizes = ", ".join([f"{k}:{v}" for k, v in book["by_size"].items()])
            display = f"{book_id} | {created_at} | {total} puzzles ({sizes})"
            books_listbox.insert(tk.END, display)

    def on_book_select(event=None):
        sel = books_listbox.curselection()
        if sel:
            idx = sel[0]
            pool = PuzzlePool()
            books = pool.get_books()
            if idx < len(books):
                selected_book_id_var.set(books[idx]["book_id"])

    books_listbox.bind("<<ListboxSelect>>", on_book_select)

    books_btn_frame = ttk.Frame(books_frame)
    books_btn_frame.pack(fill="x", padx=5, pady=(0, 5))
    
    ttk.Button(books_btn_frame, text="Refresh List", command=refresh_books_list).pack(side="left", padx=(0, 5))
    
    def regenerate_selected_book():
        book_id = selected_book_id_var.get()
        if not book_id:
            messagebox.showerror("No Selection", "Please select a book from the list to regenerate")
            return
        
        # Confirm with user
        if not messagebox.askyesno("Confirm", f"Regenerate book '{book_id}'?\nThis will reuse the same Sudoku puzzles with new PDF template settings."):
            return
        
        book_progress_var.set(0)
        book_status_var.set("Regenerating book...")
        state.is_running = True
        create_book_btn["state"] = "disabled"
        
        def worker():
            try:
                pool = PuzzlePool()
                
                # Reset puzzles for this book so they can be reused
                puzzles = pool.recreate_book(book_id)
                
                if not puzzles:
                    raise RuntimeError("No puzzles found for this book")
                
                # Get puzzles as dicts
                puzzle_dicts = [p.to_dict() for p in puzzles]
                
                # Create output
                out_base = output_base_dir
                ts_folder = make_timestamp_folder_name()
                out_dir = os.path.join(out_base, ts_folder)
                os.makedirs(out_dir, exist_ok=True)
                
                # Save JSON
                size = puzzles[0].size if puzzles else 9
                json_path = os.path.join(out_dir, f"book_{book_id}_regenerated.json")
                payload = {
                    "config": {
                        "total": len(puzzles),
                        "grid_size": size,
                        "book_id": book_id,
                        "regenerated": True,
                    },
                    "items": puzzle_dicts,
                }
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(payload, f, ensure_ascii=False, indent=2)
                
                # Generate PDF
                pdf_path = os.path.join(out_dir, f"book_{book_id}_regenerated.pdf")
                pdf_settings_file = pdf_settings_path()
                
                with open(pdf_settings_file, "r", encoding="utf-8") as pf:
                    s = json.load(pf)
                
                page_w, page_h = get_trim_size(str(s.get("trim_size", "8.5x11")))
                cfg_dict = {
                    "page_width_in": page_w,
                    "page_height_in": page_h,
                    "orientation": str(s.get("orientation", "portrait")),
                    "margin_in": float(s.get("margin_in", 0.5)),
                    "puzzles_per_page": int(s.get("puzzles_per_page", 4)),
                    "show_level": bool(s.get("show_level", True)),
                    "level_field": "difficulty",
                    "title": book_title_var.get() or f"Book {book_id}",
                    "answer_key_title": "Answer Key",
                    "answers_per_page": int(s.get("answers_per_page", 6)),
                    "label_font": str(s.get("label_font", "Helvetica")),
                    "label_font_size": int(s.get("label_font_size", 10)),
                    "digit_font": str(s.get("digit_font", "Helvetica")),
                    "digit_font_size": int(s.get("digit_font_size", 12)),
                    "grid_line_width": float(s.get("grid_line_width", 0.6)),
                    "subgrid_line_width": float(s.get("subgrid_line_width", 1.4)),
                    "header_enabled": bool(s.get("header_enabled", True)),
                    "header_height_in": float(s.get("header_height_in", 0.35)),
                    "header_font": str(s.get("header_font", "Helvetica")),
                    "header_font_size": int(s.get("header_font_size", 10)),
                    "header_show_page_number": bool(s.get("header_show_page_number", True)),
                    "header_icon_path": str(s.get("header_icon_path", "")),
                    "header_icon_height_in": float(s.get("header_icon_height_in", 0.22)),
                    "custom_fonts": list(s.get("custom_fonts", [])) if isinstance(s.get("custom_fonts", []), list) else [],
                    "text_color": str(s.get("text_color", "#000000")),
                    "grid_color": str(s.get("grid_color", "#000000")),
                    "header_line_color": str(s.get("header_line_color", "#000000")),
                    "pdf_title": book_title_var.get() or "Sudoku Book",
                    "pdf_author": str(s.get("pdf_author", "")),
                    "pdf_subject": str(s.get("pdf_subject", "")),
                    "pdf_keywords": str(s.get("pdf_keywords", "sudoku, puzzle")),
                    "template": dict(s.get("template", {})) if isinstance(s.get("template", {}), dict) else {},
                }
                
                from sudoku.pdf_export import ExportConfig, export_sudoku_json_to_pdf
                export_sudoku_json_to_pdf(json_path, pdf_path, ExportConfig.from_dict(cfg_dict))
                
                # Mark puzzles as used again
                for p in puzzles:
                    p.used = True
                    p.used_in_book = book_id
                    p.used_at = datetime.now().isoformat()
                pool._save()
                
                def _done_ok():
                    state.is_running = False
                    create_book_btn["state"] = "normal"
                    book_progress_var.set(100)
                    book_status_var.set(f"Regenerated: {len(puzzles)} puzzles")
                    refresh_pool_status()
                    refresh_books_list()
                    messagebox.showinfo(
                        "Done",
                        f"Regenerated book with {len(puzzles)} puzzles\nJSON: {json_path}\nPDF: {pdf_path}",
                    )
                    try:
                        os.startfile(pdf_path)
                    except Exception:
                        pass
                
                root.after(0, _done_ok)
            except Exception as e:
                tb = traceback.format_exc()

                def _done_err(err: Exception = e, err_tb: str = tb):
                    state.is_running = False
                    create_book_btn["state"] = "normal"
                    book_status_var.set("Error")
                    messagebox.showerror("Error", f"{err}\n\n{err_tb}")
                
                root.after(0, _done_err)
        
        threading.Thread(target=worker, daemon=True).start()
    
    ttk.Button(books_btn_frame, text="Regenerate Selected", command=regenerate_selected_book).pack(side="left")

    # Book configuration
    book_grid = ttk.Frame(book_frm)
    book_grid.pack(fill="x", pady=10)

    ttk.Label(book_grid, text="Book Title").grid(row=0, column=0, sticky="w", padx=2, pady=6)
    ttk.Entry(book_grid, textvariable=book_title_var, width=40).grid(row=0, column=1, sticky="w", pady=6)

    ttk.Label(book_grid, text="Output Folder").grid(row=1, column=0, sticky="w", padx=2, pady=6)
    ttk.Entry(book_grid, textvariable=book_output_dir_var, width=40).grid(row=1, column=1, sticky="w", pady=6)

    def choose_book_output_dir() -> None:
        d = filedialog.askdirectory(title="Choose output folder")
        if d:
            book_output_dir_var.set(d)

    ttk.Button(book_grid, text="Browse...", command=choose_book_output_dir).grid(row=1, column=2, sticky="w", padx=6, pady=6)

    ttk.Label(book_grid, text="Grid Size").grid(row=2, column=0, sticky="w", padx=2, pady=6)
    ttk.Combobox(book_grid, textvariable=book_size_var, values=[4, 9], width=10, state="readonly").grid(row=2, column=1, sticky="w", pady=6)

    ttk.Label(book_grid, text="Puzzles by difficulty").grid(row=3, column=0, sticky="w", padx=2, pady=6)
    book_counts = ttk.Frame(book_grid)
    book_counts.grid(row=3, column=1, sticky="w")

    ttk.Label(book_counts, text="Easy").grid(row=0, column=0, sticky="w")
    ttk.Entry(book_counts, textvariable=book_easy_count_var, width=6).grid(row=0, column=1, padx=6)
    ttk.Label(book_counts, text="Medium").grid(row=0, column=2, sticky="w")
    ttk.Entry(book_counts, textvariable=book_med_count_var, width=6).grid(row=0, column=3, padx=6)
    ttk.Label(book_counts, text="Hard").grid(row=0, column=4, sticky="w")
    ttk.Entry(book_counts, textvariable=book_hard_count_var, width=6).grid(row=0, column=5, padx=6)

    ttk.Separator(book_frm).pack(fill="x", pady=12)

    book_btns = ttk.Frame(book_frm)
    book_btns.pack(fill="x")
    create_book_btn = ttk.Button(book_btns, text="Create Book", command=create_book_in_thread)
    create_book_btn.pack(side="left")

    book_prog = ttk.Progressbar(book_frm, orient="horizontal", maximum=100, variable=book_progress_var)
    book_prog.pack(fill="x", pady=12)

    book_status = ttk.Label(book_frm, textvariable=book_status_var)
    book_status.pack(anchor="w")

    # Initial pool status refresh and books list
    refresh_pool_status()
    refresh_books_list()

    # Settings Tab with scrolling canvas
    pdf_canvas = tk.Canvas(tab_pdf)
    pdf_scroll = ttk.Scrollbar(tab_pdf, orient="vertical", command=pdf_canvas.yview)
    pdf_frm = ttk.Frame(pdf_canvas)

    pdf_frm.bind(
        "<Configure>",
        lambda e: pdf_canvas.configure(scrollregion=pdf_canvas.bbox("all")),
    )

    pdf_canvas_win = pdf_canvas.create_window((0, 0), window=pdf_frm, anchor="nw")

    def _sync_pdf_frame_width(event) -> None:
        pdf_canvas.itemconfigure(pdf_canvas_win, width=event.width)

    pdf_canvas.bind("<Configure>", _sync_pdf_frame_width)
    pdf_canvas.configure(yscrollcommand=pdf_scroll.set)

    pdf_canvas.pack(side="left", fill="both", expand=True)
    pdf_scroll.pack(side="right", fill="y")

    pdf_title = ttk.Label(pdf_frm, text="Settings (Paperback PDF)", font=("Segoe UI", 16, "bold"))
    pdf_title.pack(anchor="w")

    ttk.Separator(pdf_frm).pack(fill="x", pady=10)

    settings_body = ttk.Panedwindow(pdf_frm, orient="horizontal")
    settings_body.pack(fill="both", expand=True)

    left = ttk.Frame(settings_body)
    right = ttk.Frame(settings_body)
    settings_body.add(left, weight=1)
    settings_body.add(right, weight=6)

    ttk.Label(left, text="Pages", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 6))
    page_list = tk.Listbox(left, height=16)
    page_list.pack(fill="both", expand=True)

    panels: dict[str, ttk.Frame] = {}

    def add_panel(name: str) -> ttk.Frame:
        page_list.insert(tk.END, name)
        f = ttk.Frame(right)
        f.grid(row=0, column=0, sticky="nsew")
        panels[name] = f
        return f

    right.rowconfigure(0, weight=1)
    right.columnconfigure(0, weight=1)

    panel_book = add_panel("Book Settings")
    panel_cover = add_panel("Cover")
    panel_title = add_panel("Title Page")
    panel_copyright = add_panel("Copyright")
    panel_how = add_panel("How to Play")
    panel_puzzles = add_panel("Puzzle Section")
    panel_notes = add_panel("Notes / CTA")
    panel_style = add_panel("PDF Style")
    panel_actions = add_panel("Actions")

    def show_panel(name: str) -> None:
        p = panels.get(name)
        if p:
            p.tkraise()

    def _on_page_select(_event=None) -> None:
        sel = page_list.curselection()
        if not sel:
            return
        show_panel(str(page_list.get(int(sel[0]))))

    page_list.bind("<<ListboxSelect>>", _on_page_select)

    # Autosave settings (debounced)
    autosave_job: dict[str, object] = {"id": None}

    def build_pdf_settings_dict() -> dict:
        def tget(key: str) -> str:
            w = template_widgets.get(key)
            return w.get("1.0", "end").rstrip("\n") if w else ""

        return {
            "trim_size": pdf_trim_preset_var.get().strip(),
            "orientation": pdf_orientation_var.get().strip() or "portrait",
            "margin_in": float(pdf_margin_in_var.get()),
            "puzzles_per_page": int(pdf_puzzles_per_page_var.get()),
            "answers_per_page": int(pdf_answers_per_page_var.get()),
            "show_level": bool(pdf_show_level_var.get()),
            "label_font": pdf_label_font_var.get().strip() or "Helvetica",
            "label_font_size": int(pdf_label_font_size_var.get()),
            "digit_font": pdf_digit_font_var.get().strip() or "Helvetica",
            "digit_font_size": int(pdf_digit_font_size_var.get()),
            "grid_line_width": float(pdf_grid_line_width_var.get()),
            "subgrid_line_width": float(pdf_subgrid_line_width_var.get()),
            "header_enabled": bool(pdf_header_enabled_var.get()),
            "header_height_in": float(pdf_header_height_in_var.get()),
            "header_font": pdf_header_font_var.get().strip() or "Helvetica",
            "header_font_size": int(pdf_header_font_size_var.get()),
            "header_show_page_number": bool(pdf_header_show_page_number_var.get()),
            "header_icon_path": pdf_header_icon_path_var.get().strip(),
            "header_icon_height_in": float(pdf_header_icon_height_in_var.get()),
            "custom_fonts": pdf_custom_fonts,
            "text_color": pdf_text_color_var.get().strip() or "#000000",
            "grid_color": pdf_grid_color_var.get().strip() or "#000000",
            "header_line_color": pdf_header_line_color_var.get().strip() or "#000000",
            "pdf_title": pdf_title_var.get().strip() or "Sudoku",
            "pdf_author": pdf_author_var.get().strip(),
            "pdf_subject": pdf_subject_var.get().strip(),
            "pdf_keywords": pdf_keywords_var.get().strip(),
            "template": {
                "cover": {
                    "enabled": bool(template_cover_enabled_var.get()),
                    "image_path": template_cover_image_path_var.get().strip(),
                },
                "title_page": {
                    "enabled": bool(template_title_enabled_var.get()),
                    "title": template_title_title_var.get().strip() or pdf_title_var.get().strip() or "Sudoku",
                    "image_path": template_title_image_path_var.get().strip(),
                    "body": tget("title_body"),
                },
                "copyright": {
                    "enabled": bool(template_copyright_enabled_var.get()),
                    "title": template_copyright_title_var.get().strip() or "Copyright",
                    "image_path": template_copyright_image_path_var.get().strip(),
                    "body": tget("copyright_body"),
                },
                "how_to_play": {
                    "enabled": bool(template_how_enabled_var.get()),
                    "title": template_how_title_var.get().strip() or "How to Play",
                    "image_path": template_how_image_path_var.get().strip(),
                    "body": tget("how_body"),
                },
                "notes_cta": {
                    "enabled": bool(template_notes_enabled_var.get()),
                    "title": template_notes_title_var.get().strip() or "Notes / CTA",
                    "image_path": template_notes_image_path_var.get().strip(),
                    "body": tget("notes_body"),
                },
                "section_dividers": {
                    "enabled": bool(template_section_dividers_enabled_var.get()),
                    "include_level_lesson": bool(template_section_dividers_include_lesson_var.get()),
                    "easy": {
                        "title": template_section_easy_title_var.get().strip() or "Puzzle Section: Easy",
                        "image_path": template_section_easy_image_path_var.get().strip(),
                        "body": tget("section_easy_body"),
                    },
                    "medium": {
                        "title": template_section_medium_title_var.get().strip() or "Puzzle Section: Medium",
                        "image_path": template_section_medium_image_path_var.get().strip(),
                        "body": tget("section_medium_body"),
                    },
                    "hard": {
                        "title": template_section_hard_title_var.get().strip() or "Puzzle Section: Hard",
                        "image_path": template_section_hard_image_path_var.get().strip(),
                        "body": tget("section_hard_body"),
                    },
                },
            },
        }

    def write_pdf_settings() -> None:
        path = pdf_settings_path()
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(build_pdf_settings_dict(), f, ensure_ascii=False, indent=2)
            pdf_status_var.set(f"Auto-saved: {path}")
        except Exception as e:
            pdf_status_var.set("Error")
            messagebox.showerror("Error", f"Failed to save PDF settings: {e}")

    def schedule_autosave() -> None:
        if autosave_job.get("id") is not None:
            try:
                root.after_cancel(autosave_job["id"])  # type: ignore[arg-type]
            except Exception:
                pass
        autosave_job["id"] = root.after(600, write_pdf_settings)
    def bind_text_autosave(w: tk.Text) -> None:
        def _on_modified(_event=None) -> None:
            try:
                if w.edit_modified():
                    w.edit_modified(False)
                    schedule_autosave()
            except Exception:
                return

        w.bind("<<Modified>>", _on_modified)

    def bind_var_autosave(var: tk.Variable) -> None:
        try:
            var.trace_add("write", lambda *_: schedule_autosave())
        except Exception:
            return

    # Ensure settings file exists early
    if not os.path.exists(pdf_settings_path()):
        write_pdf_settings()

    # Book Settings page
    ttk.Label(panel_book, text="Book Settings", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 10))
    ttk.Label(panel_book, text="Output").grid(row=1, column=0, sticky="w", padx=2, pady=6)
    output_row = ttk.Frame(panel_book)
    output_row.grid(row=1, column=1, sticky="w", padx=2, pady=6)
    ttk.Entry(output_row, textvariable=book_output_dir_var, width=40).pack(side="left")

    def choose_settings_output_dir() -> None:
        d = filedialog.askdirectory(title="Choose output folder")
        if d:
            book_output_dir_var.set(d)

    ttk.Button(output_row, text="Browse...", command=choose_settings_output_dir).pack(side="left", padx=6)

    ttk.Label(panel_book, text="Trim size").grid(row=2, column=0, sticky="w", padx=2, pady=6)
    ttk.Combobox(panel_book, textvariable=pdf_trim_preset_var, values=["6x9", "8.5x11"], width=12).grid(
        row=2, column=1, sticky="w", pady=6
    )
    ttk.Label(panel_book, text="Orientation").grid(row=3, column=0, sticky="w", padx=2, pady=6)
    ttk.Combobox(panel_book, textvariable=pdf_orientation_var, values=["portrait", "landscape"], width=12).grid(
        row=3, column=1, sticky="w", pady=6
    )
    ttk.Label(panel_book, text="Margin (inch)").grid(row=4, column=0, sticky="w", padx=2, pady=6)
    ttk.Entry(panel_book, textvariable=pdf_margin_in_var, width=10).grid(row=4, column=1, sticky="w", pady=6)

    ttk.Label(panel_book, text="PDF Title").grid(row=5, column=0, sticky="w", padx=2, pady=6)
    ttk.Entry(panel_book, textvariable=pdf_title_var, width=40).grid(row=5, column=1, sticky="w", pady=6)
    ttk.Label(panel_book, text="Author").grid(row=6, column=0, sticky="w", padx=2, pady=6)
    ttk.Entry(panel_book, textvariable=pdf_author_var, width=40).grid(row=6, column=1, sticky="w", pady=6)
    ttk.Label(panel_book, text="Subject").grid(row=7, column=0, sticky="w", padx=2, pady=6)
    ttk.Entry(panel_book, textvariable=pdf_subject_var, width=40).grid(row=7, column=1, sticky="w", pady=6)
    ttk.Label(panel_book, text="Keywords").grid(row=8, column=0, sticky="w", padx=2, pady=6)
    ttk.Entry(panel_book, textvariable=pdf_keywords_var, width=40).grid(row=8, column=1, sticky="w", pady=6)

    # Cover page
    ttk.Label(panel_cover, text="Cover", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 10))
    ttk.Checkbutton(panel_cover, text="Include cover page (interior)", variable=template_cover_enabled_var).grid(
        row=1, column=0, sticky="w", padx=2, pady=6
    )
    cover_row = ttk.Frame(panel_cover)
    cover_row.grid(row=2, column=0, sticky="we", padx=2, pady=6)
    ttk.Entry(cover_row, textvariable=template_cover_image_path_var, width=46).pack(side="left", fill="x", expand=True)

    def pick_cover_image() -> None:
        path = filedialog.askopenfilename(
            title="Choose cover image",
            filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.bmp;*.gif")],
        )
        if path:
            template_cover_image_path_var.set(path)

    ttk.Button(cover_row, text="Browse...", command=pick_cover_image).pack(side="left", padx=8)

    # Title page
    ttk.Label(panel_title, text="Title Page", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 10))
    ttk.Checkbutton(panel_title, text="Include Title Page", variable=template_title_enabled_var).grid(
        row=1, column=0, sticky="w", padx=2, pady=6
    )
    ttk.Label(panel_title, text="Title").grid(row=2, column=0, sticky="w", padx=2)
    ttk.Entry(panel_title, textvariable=template_title_title_var, width=50).grid(row=3, column=0, sticky="we", padx=2, pady=(0, 6))
    
    # Image row for Title Page
    ttk.Label(panel_title, text="Image (optional - overrides text content)").grid(row=4, column=0, sticky="w", padx=2, pady=(6, 2))
    title_img_row = ttk.Frame(panel_title)
    title_img_row.grid(row=5, column=0, sticky="we", padx=2, pady=(0, 6))
    ttk.Entry(title_img_row, textvariable=template_title_image_path_var, width=46).pack(side="left", fill="x", expand=True)
    def pick_title_image() -> None:
        path = filedialog.askopenfilename(
            title="Choose title page image",
            filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.bmp;*.gif")],
        )
        if path:
            template_title_image_path_var.set(path)
    ttk.Button(title_img_row, text="Browse...", command=pick_title_image).pack(side="left", padx=8)
    
    # Text content (used when no image)
    ttk.Label(panel_title, text="Text content (used if no image)").grid(row=6, column=0, sticky="w", padx=2, pady=(6, 2))
    title_body = tk.Text(panel_title, height=8)
    title_body.grid(row=7, column=0, sticky="nsew", padx=2)
    panel_title.rowconfigure(7, weight=1)
    panel_title.columnconfigure(0, weight=1)
    template_widgets["title_body"] = title_body

    def apply_min_title_page() -> None:
        template_title_title_var.set(template_title_title_var.get() or "Sudoku")
        title_body.delete("1.0", "end")
        title_body.insert(
            "1.0",
            "Welcome to this Sudoku book.\n\nIncludes puzzles from Easy to Hard.\nSolutions are provided at the end.",
        )

    ttk.Button(panel_title, text="Apply minimal", command=apply_min_title_page).grid(row=8, column=0, sticky="w", padx=2, pady=8)

    # Copyright page
    ttk.Label(panel_copyright, text="Copyright", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 10))
    ttk.Checkbutton(panel_copyright, text="Include Copyright", variable=template_copyright_enabled_var).grid(
        row=1, column=0, sticky="w", padx=2, pady=6
    )
    ttk.Label(panel_copyright, text="Title").grid(row=2, column=0, sticky="w", padx=2)
    ttk.Entry(panel_copyright, textvariable=template_copyright_title_var, width=50).grid(row=3, column=0, sticky="we", padx=2, pady=(0, 6))
    
    # Image row for Copyright
    ttk.Label(panel_copyright, text="Image (optional - overrides text content)").grid(row=4, column=0, sticky="w", padx=2, pady=(6, 2))
    copyright_img_row = ttk.Frame(panel_copyright)
    copyright_img_row.grid(row=5, column=0, sticky="we", padx=2, pady=(0, 6))
    ttk.Entry(copyright_img_row, textvariable=template_copyright_image_path_var, width=46).pack(side="left", fill="x", expand=True)
    def pick_copyright_image() -> None:
        path = filedialog.askopenfilename(
            title="Choose copyright page image",
            filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.bmp;*.gif")],
        )
        if path:
            template_copyright_image_path_var.set(path)
    ttk.Button(copyright_img_row, text="Browse...", command=pick_copyright_image).pack(side="left", padx=8)
    
    # Text content (used when no image)
    ttk.Label(panel_copyright, text="Text content (used if no image)").grid(row=6, column=0, sticky="w", padx=2, pady=(6, 2))
    copyright_body = tk.Text(panel_copyright, height=8)
    copyright_body.grid(row=7, column=0, sticky="nsew", padx=2)
    panel_copyright.rowconfigure(7, weight=1)
    panel_copyright.columnconfigure(0, weight=1)
    template_widgets["copyright_body"] = copyright_body

    def apply_min_copyright() -> None:
        template_copyright_title_var.set(template_copyright_title_var.get() or "Copyright")
        copyright_body.delete("1.0", "end")
        copyright_body.insert(
            "1.0",
            "Copyright © {YEAR} {AUTHOR}.\nAll rights reserved.\nNo part of this book may be reproduced without permission.",
        )

    ttk.Button(panel_copyright, text="Apply minimal", command=apply_min_copyright).grid(row=8, column=0, sticky="w", padx=2, pady=8)

    # How to Play page
    ttk.Label(panel_how, text="How to Play", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 10))
    ttk.Checkbutton(panel_how, text="Include How to Play", variable=template_how_enabled_var).grid(
        row=1, column=0, sticky="w", padx=2, pady=6
    )
    ttk.Label(panel_how, text="Title").grid(row=2, column=0, sticky="w", padx=2)
    ttk.Entry(panel_how, textvariable=template_how_title_var, width=50).grid(row=3, column=0, sticky="we", padx=2, pady=(0, 6))
    
    # Image row for How to Play
    ttk.Label(panel_how, text="Image (optional - overrides text content)").grid(row=4, column=0, sticky="w", padx=2, pady=(6, 2))
    how_img_row = ttk.Frame(panel_how)
    how_img_row.grid(row=5, column=0, sticky="we", padx=2, pady=(0, 6))
    ttk.Entry(how_img_row, textvariable=template_how_image_path_var, width=46).pack(side="left", fill="x", expand=True)
    def pick_how_image() -> None:
        path = filedialog.askopenfilename(
            title="Choose how to play page image",
            filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.bmp;*.gif")],
        )
        if path:
            template_how_image_path_var.set(path)
    ttk.Button(how_img_row, text="Browse...", command=pick_how_image).pack(side="left", padx=8)
    
    # Text content (used when no image)
    ttk.Label(panel_how, text="Text content (used if no image)").grid(row=6, column=0, sticky="w", padx=2, pady=(6, 2))
    how_body = tk.Text(panel_how, height=10)
    how_body.grid(row=7, column=0, sticky="nsew", padx=2)
    panel_how.rowconfigure(7, weight=1)
    panel_how.columnconfigure(0, weight=1)
    template_widgets["how_body"] = how_body

    def apply_min_how() -> None:
        template_how_title_var.set(template_how_title_var.get() or "How to Play")
        how_body.delete("1.0", "end")
        how_body.insert(
            "1.0",
            "Fill the grid so that each row, column, and 3×3 box contains the numbers 1–9 exactly once.\n\nTip: Start with Easy puzzles and look for cells with only one possible number.",
        )

    ttk.Button(panel_how, text="Apply minimal", command=apply_min_how).grid(row=8, column=0, sticky="w", padx=2, pady=8)

    # Puzzle Section page
    ttk.Label(panel_puzzles, text="Puzzle Section", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 10))
    ttk.Checkbutton(panel_puzzles, text="Show level label on puzzle", variable=pdf_show_level_var).grid(
        row=1, column=0, sticky="w", padx=2, pady=6
    )
    ttk.Checkbutton(
        panel_puzzles,
        text="Section divider pages (Easy/Medium/Hard)",
        variable=template_section_dividers_enabled_var,
    ).grid(row=2, column=0, sticky="w", padx=2, pady=6)
    ttk.Checkbutton(
        panel_puzzles,
        text="Divider includes level lesson text (Easy/Medium/Hard)",
        variable=template_section_dividers_include_lesson_var,
    ).grid(row=3, column=0, sticky="w", padx=2, pady=6)

    ttk.Separator(panel_puzzles).grid(row=8, column=0, sticky="we", pady=12)

    ttk.Label(panel_puzzles, text="Divider pages (optional image overrides text)", font=("Segoe UI", 10, "bold")).grid(
        row=9, column=0, sticky="w", padx=2, pady=(0, 6)
    )

    def _divider_block(parent, *, row0: int, level: str, title_var: tk.StringVar, img_var: tk.StringVar, body_key: str):
        ttk.Label(parent, text=f"{level.title()} divider title").grid(row=row0, column=0, sticky="w", padx=2)
        ttk.Entry(parent, textvariable=title_var, width=50).grid(row=row0 + 1, column=0, sticky="we", padx=2, pady=(0, 6))

        ttk.Label(parent, text="Image (optional - overrides text)").grid(row=row0 + 2, column=0, sticky="w", padx=2)
        img_row = ttk.Frame(parent)
        img_row.grid(row=row0 + 3, column=0, sticky="we", padx=2, pady=(0, 6))
        ttk.Entry(img_row, textvariable=img_var, width=60).pack(side="left", fill="x", expand=True)

        def _browse_img() -> None:
            p = filedialog.askopenfilename(title="Choose image", filetypes=[("Image", "*.png;*.jpg;*.jpeg;*.webp;*.bmp")])
            if p:
                img_var.set(p)

        ttk.Button(img_row, text="Browse...", command=_browse_img).pack(side="left", padx=6)

        ttk.Label(parent, text="Text content (used if no image)").grid(row=row0 + 4, column=0, sticky="w", padx=2, pady=(6, 2))
        body = tk.Text(parent, height=5)
        body.grid(row=row0 + 5, column=0, sticky="we", padx=2)
        template_widgets[body_key] = body
        ttk.Separator(parent).grid(row=row0 + 6, column=0, sticky="we", pady=10)
        return body

    panel_puzzles.columnconfigure(0, weight=1)
    easy_body = _divider_block(
        panel_puzzles,
        row0=10,
        level="easy",
        title_var=template_section_easy_title_var,
        img_var=template_section_easy_image_path_var,
        body_key="section_easy_body",
    )
    medium_body = _divider_block(
        panel_puzzles,
        row0=17,
        level="medium",
        title_var=template_section_medium_title_var,
        img_var=template_section_medium_image_path_var,
        body_key="section_medium_body",
    )
    hard_body = _divider_block(
        panel_puzzles,
        row0=24,
        level="hard",
        title_var=template_section_hard_title_var,
        img_var=template_section_hard_image_path_var,
        body_key="section_hard_body",
    )
    ttk.Label(panel_puzzles, text="Puzzles per page").grid(row=4, column=0, sticky="w", padx=2, pady=(14, 6))
    ttk.Combobox(panel_puzzles, textvariable=pdf_puzzles_per_page_var, values=[1, 2, 4, 6, 8, 9], width=10).grid(
        row=5, column=0, sticky="w", padx=2
    )
    ttk.Label(panel_puzzles, text="Answers per page").grid(row=6, column=0, sticky="w", padx=2, pady=(10, 6))
    ttk.Combobox(panel_puzzles, textvariable=pdf_answers_per_page_var, values=[4, 6, 8, 9, 12], width=10).grid(
        row=7, column=0, sticky="w", padx=2
    )

    # Notes / CTA
    ttk.Label(panel_notes, text="Notes / CTA", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 10))
    ttk.Checkbutton(panel_notes, text="Include Notes / CTA", variable=template_notes_enabled_var).grid(
        row=1, column=0, sticky="w", padx=2, pady=6
    )
    ttk.Label(panel_notes, text="Title").grid(row=2, column=0, sticky="w", padx=2)
    ttk.Entry(panel_notes, textvariable=template_notes_title_var, width=50).grid(row=3, column=0, sticky="we", padx=2, pady=(0, 6))

    ttk.Label(panel_notes, text="Image (optional - overrides text content)").grid(row=4, column=0, sticky="w", padx=2, pady=(6, 2))
    notes_img_row = ttk.Frame(panel_notes)
    notes_img_row.grid(row=5, column=0, sticky="we", padx=2, pady=(0, 6))
    ttk.Entry(notes_img_row, textvariable=template_notes_image_path_var, width=46).pack(side="left", fill="x", expand=True)

    def pick_notes_image() -> None:
        path = filedialog.askopenfilename(
            title="Choose notes page image",
            filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.bmp;*.gif")],
        )
        if path:
            template_notes_image_path_var.set(path)

    ttk.Button(notes_img_row, text="Browse...", command=pick_notes_image).pack(side="left", padx=8)

    notes_body = tk.Text(panel_notes, height=10)
    notes_body.grid(row=6, column=0, sticky="nsew", padx=2)
    panel_notes.rowconfigure(6, weight=1)
    panel_notes.columnconfigure(0, weight=1)
    template_widgets["notes_body"] = notes_body

    def apply_min_notes() -> None:
        template_notes_title_var.set(template_notes_title_var.get() or "Notes / CTA")
        notes_body.delete("1.0", "end")
        notes_body.insert(
            "1.0",
            "Thanks for playing!\nIf you enjoyed this book, please consider leaving a review.\nMore puzzle books: {LINK}",
        )

    ttk.Button(panel_notes, text="Apply minimal", command=apply_min_notes).grid(row=5, column=0, sticky="w", padx=2, pady=8)

    # PDF Style
    ttk.Label(panel_style, text="PDF Style", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 10))
    built_in_fonts = [
        "Helvetica",
        "Helvetica-Bold",
        "Times-Roman",
        "Times-Bold",
        "Courier",
        "Courier-Bold",
    ]
    try:
        sys_fonts = sorted(set(tkfont.families(root)))
    except Exception:
        sys_fonts = []
    all_fonts = sorted(set(built_in_fonts + sys_fonts))

    ttk.Label(panel_style, text="Label font").grid(row=1, column=0, sticky="w", padx=2, pady=4)
    ttk.Combobox(panel_style, textvariable=pdf_label_font_var, values=all_fonts, width=26).grid(row=2, column=0, sticky="w", padx=2)
    ttk.Label(panel_style, text="Label size").grid(row=1, column=1, sticky="w", padx=2, pady=4)
    ttk.Entry(panel_style, textvariable=pdf_label_font_size_var, width=6).grid(row=2, column=1, sticky="w")

    ttk.Label(panel_style, text="Digit font").grid(row=3, column=0, sticky="w", padx=2, pady=4)
    ttk.Combobox(panel_style, textvariable=pdf_digit_font_var, values=all_fonts, width=26).grid(row=4, column=0, sticky="w", padx=2)
    ttk.Label(panel_style, text="Digit size").grid(row=3, column=1, sticky="w", padx=2, pady=4)
    ttk.Entry(panel_style, textvariable=pdf_digit_font_size_var, width=6).grid(row=4, column=1, sticky="w")

    ttk.Label(panel_style, text="Grid line width").grid(row=5, column=0, sticky="w", padx=2, pady=4)
    ttk.Entry(panel_style, textvariable=pdf_grid_line_width_var, width=10).grid(row=6, column=0, sticky="w", padx=2)
    ttk.Label(panel_style, text="Subgrid line width").grid(row=5, column=1, sticky="w", padx=2, pady=4)
    ttk.Entry(panel_style, textvariable=pdf_subgrid_line_width_var, width=10).grid(row=6, column=1, sticky="w")

    ttk.Checkbutton(panel_style, text="Enable header", variable=pdf_header_enabled_var).grid(row=7, column=0, sticky="w", padx=2, pady=6)
    ttk.Checkbutton(panel_style, text="Show page number", variable=pdf_header_show_page_number_var).grid(row=7, column=1, sticky="w", padx=2, pady=6)
    ttk.Label(panel_style, text="Header height (inch)").grid(row=8, column=0, sticky="w", padx=2, pady=4)
    ttk.Entry(panel_style, textvariable=pdf_header_height_in_var, width=10).grid(row=9, column=0, sticky="w", padx=2)
    ttk.Label(panel_style, text="Header font").grid(row=8, column=1, sticky="w", padx=2, pady=4)
    ttk.Combobox(panel_style, textvariable=pdf_header_font_var, values=all_fonts, width=26).grid(row=9, column=1, sticky="w")
    ttk.Label(panel_style, text="Header size").grid(row=10, column=0, sticky="w", padx=2, pady=4)
    ttk.Entry(panel_style, textvariable=pdf_header_font_size_var, width=6).grid(row=11, column=0, sticky="w", padx=2)

    ttk.Label(panel_style, text="Header icon").grid(row=12, column=0, sticky="w", padx=2, pady=4)
    icon_row2 = ttk.Frame(panel_style)
    icon_row2.grid(row=13, column=0, columnspan=2, sticky="we", padx=2)
    ttk.Entry(icon_row2, textvariable=pdf_header_icon_path_var, width=46).pack(side="left", fill="x", expand=True)

    def pick_header_icon() -> None:
        path = filedialog.askopenfilename(
            title="Choose header icon",
            filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.bmp;*.gif")],
        )
        if path:
            pdf_header_icon_path_var.set(path)

    ttk.Button(icon_row2, text="Browse...", command=pick_header_icon).pack(side="left", padx=8)
    ttk.Label(panel_style, text="Icon height (inch)").grid(row=14, column=0, sticky="w", padx=2, pady=4)
    ttk.Entry(panel_style, textvariable=pdf_header_icon_height_in_var, width=10).grid(row=15, column=0, sticky="w", padx=2)

    ttk.Label(panel_style, text="Custom fonts (TTF)").grid(row=16, column=0, sticky="w", padx=2, pady=(14, 4))
    font_list = tk.Listbox(panel_style, height=4)
    font_list.grid(row=17, column=0, columnspan=2, sticky="we", padx=2)

    def refresh_custom_fonts_list() -> None:
        font_list.delete(0, tk.END)
        for f in pdf_custom_fonts:
            font_list.insert(tk.END, f"{f.get('name','')} -> {f.get('path','')}")

    def add_custom_font() -> None:
        path = filedialog.askopenfilename(title="Choose TTF font", filetypes=[("Font", "*.ttf")])
        if not path:
            return
        name = simpledialog.askstring("Font name", "Enter font name to use in PDF")
        if not name:
            return
        pdf_custom_fonts.append({"name": name.strip(), "path": path})
        refresh_custom_fonts_list()
        schedule_autosave()

    def remove_custom_font() -> None:
        sel = font_list.curselection()
        if not sel:
            return
        idx = int(sel[0])
        if 0 <= idx < len(pdf_custom_fonts):
            pdf_custom_fonts.pop(idx)
            refresh_custom_fonts_list()
            schedule_autosave()

    ttk.Button(panel_style, text="Add font...", command=add_custom_font).grid(row=18, column=0, sticky="w", padx=2, pady=6)
    ttk.Button(panel_style, text="Remove", command=remove_custom_font).grid(row=18, column=1, sticky="w", padx=2, pady=6)

    palette = {
        "Black": "#000000",
        "Dark Gray": "#333333",
        "Gray": "#666666",
        "Light Gray": "#AAAAAA",
        "Blue": "#0B57D0",
        "Navy": "#0A1F44",
        "Green": "#137333",
        "Red": "#B3261E",
    }
    text_color_name = tk.StringVar(value="Black")
    grid_color_name = tk.StringVar(value="Black")
    header_line_color_name = tk.StringVar(value="Black")

    def _sync_color_names_from_hex() -> None:
        inv = {v.lower(): k for k, v in palette.items()}
        text_color_name.set(inv.get(pdf_text_color_var.get().strip().lower(), "Black"))
        grid_color_name.set(inv.get(pdf_grid_color_var.get().strip().lower(), "Black"))
        header_line_color_name.set(inv.get(pdf_header_line_color_var.get().strip().lower(), "Black"))

    def _on_text_color_change(_event=None) -> None:
        pdf_text_color_var.set(palette.get(text_color_name.get(), "#000000"))

    def _on_grid_color_change(_event=None) -> None:
        pdf_grid_color_var.set(palette.get(grid_color_name.get(), "#000000"))

    def _on_header_line_color_change(_event=None) -> None:
        pdf_header_line_color_var.set(palette.get(header_line_color_name.get(), "#000000"))

    ttk.Label(panel_style, text="Text color").grid(row=19, column=0, sticky="w", padx=2, pady=(12, 4))
    cmb1 = ttk.Combobox(panel_style, textvariable=text_color_name, values=list(palette.keys()), width=18, state="readonly")
    cmb1.grid(row=20, column=0, sticky="w", padx=2)
    cmb1.bind("<<ComboboxSelected>>", _on_text_color_change)
    ttk.Label(panel_style, text="Grid color").grid(row=19, column=1, sticky="w", padx=2, pady=(12, 4))
    cmb2 = ttk.Combobox(panel_style, textvariable=grid_color_name, values=list(palette.keys()), width=18, state="readonly")
    cmb2.grid(row=20, column=1, sticky="w")
    cmb2.bind("<<ComboboxSelected>>", _on_grid_color_change)
    ttk.Label(panel_style, text="Header line color").grid(row=21, column=0, sticky="w", padx=2, pady=(12, 4))
    cmb3 = ttk.Combobox(panel_style, textvariable=header_line_color_name, values=list(palette.keys()), width=18, state="readonly")
    cmb3.grid(row=22, column=0, sticky="w", padx=2)
    cmb3.bind("<<ComboboxSelected>>", _on_header_line_color_change)

    # Actions
    ttk.Label(panel_actions, text="Actions", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 10))
    pdf_export_btn = ttk.Button(panel_actions, text="Export PDF (manual)", command=export_pdf_in_thread)
    pdf_export_btn.grid(row=1, column=0, sticky="w", padx=2, pady=6)

    pdf_prog = ttk.Progressbar(pdf_frm, orient="horizontal", maximum=100, variable=pdf_progress_var)
    pdf_prog.pack(fill="x", pady=12)

    pdf_status = ttk.Label(pdf_frm, textvariable=pdf_status_var)
    pdf_status.pack(anchor="w")

    # Load settings and apply to widgets
    load_pdf_settings_into_vars()
    refresh_custom_fonts_list()
    _sync_color_names_from_hex()

    def _apply_template_to_widgets() -> None:
        t = pdf_template_data
        if not isinstance(t, dict):
            return

        cover = t.get("cover", {})
        if isinstance(cover, dict):
            template_cover_enabled_var.set(bool(cover.get("enabled", False)))
            template_cover_image_path_var.set(str(cover.get("image_path", "")))

        tp = t.get("title_page", {})
        if isinstance(tp, dict):
            template_title_enabled_var.set(bool(tp.get("enabled", True)))
            template_title_title_var.set(str(tp.get("title", template_title_title_var.get())))
            template_title_image_path_var.set(str(tp.get("image_path", "")))
            title_body.delete("1.0", "end")
            title_body.insert("1.0", str(tp.get("body", "")))

        cp = t.get("copyright", {})
        if isinstance(cp, dict):
            template_copyright_enabled_var.set(bool(cp.get("enabled", False)))
            template_copyright_title_var.set(str(cp.get("title", template_copyright_title_var.get())))
            template_copyright_image_path_var.set(str(cp.get("image_path", "")))
            copyright_body.delete("1.0", "end")
            copyright_body.insert("1.0", str(cp.get("body", "")))

        hw = t.get("how_to_play", {})
        if isinstance(hw, dict):
            template_how_enabled_var.set(bool(hw.get("enabled", True)))
            template_how_title_var.set(str(hw.get("title", template_how_title_var.get())))
            template_how_image_path_var.set(str(hw.get("image_path", "")))
            how_body.delete("1.0", "end")
            how_body.insert("1.0", str(hw.get("body", "")))

        nt = t.get("notes_cta", {})
        if isinstance(nt, dict):
            template_notes_enabled_var.set(bool(nt.get("enabled", False)))
            template_notes_title_var.set(str(nt.get("title", template_notes_title_var.get())))
            template_notes_image_path_var.set(str(nt.get("image_path", "")))
            notes_body.delete("1.0", "end")
            notes_body.insert("1.0", str(nt.get("body", "")))

        sd = t.get("section_dividers", {})
        if isinstance(sd, dict):
            template_section_dividers_enabled_var.set(bool(sd.get("enabled", True)))
            template_section_dividers_include_lesson_var.set(bool(sd.get("include_level_lesson", True)))

            sd_easy = sd.get("easy", {})
            if isinstance(sd_easy, dict):
                template_section_easy_title_var.set(str(sd_easy.get("title", template_section_easy_title_var.get())))
                template_section_easy_image_path_var.set(str(sd_easy.get("image_path", "")))
                easy_body.delete("1.0", "end")
                easy_body.insert("1.0", str(sd_easy.get("body", "")))

            sd_med = sd.get("medium", {})
            if isinstance(sd_med, dict):
                template_section_medium_title_var.set(str(sd_med.get("title", template_section_medium_title_var.get())))
                template_section_medium_image_path_var.set(str(sd_med.get("image_path", "")))
                medium_body.delete("1.0", "end")
                medium_body.insert("1.0", str(sd_med.get("body", "")))

            sd_hard = sd.get("hard", {})
            if isinstance(sd_hard, dict):
                template_section_hard_title_var.set(str(sd_hard.get("title", template_section_hard_title_var.get())))
                template_section_hard_image_path_var.set(str(sd_hard.get("image_path", "")))
                hard_body.delete("1.0", "end")
                hard_body.insert("1.0", str(sd_hard.get("body", "")))

    _apply_template_to_widgets()

    # Bind autosave to variables and text widgets
    for v in [
        pdf_trim_preset_var,
        pdf_orientation_var,
        pdf_margin_in_var,
        pdf_puzzles_per_page_var,
        pdf_answers_per_page_var,
        pdf_show_level_var,
        pdf_label_font_var,
        pdf_label_font_size_var,
        pdf_digit_font_var,
        pdf_digit_font_size_var,
        pdf_grid_line_width_var,
        pdf_subgrid_line_width_var,
        pdf_header_enabled_var,
        pdf_header_height_in_var,
        pdf_header_font_var,
        pdf_header_font_size_var,
        pdf_header_show_page_number_var,
        pdf_header_icon_path_var,
        pdf_header_icon_height_in_var,
        pdf_text_color_var,
        pdf_grid_color_var,
        pdf_header_line_color_var,
        pdf_title_var,
        pdf_author_var,
        pdf_subject_var,
        pdf_keywords_var,
        template_cover_enabled_var,
        template_cover_image_path_var,
        template_title_enabled_var,
        template_title_title_var,
        template_title_image_path_var,
        template_copyright_enabled_var,
        template_copyright_title_var,
        template_copyright_image_path_var,
        template_how_enabled_var,
        template_how_title_var,
        template_how_image_path_var,
        template_notes_enabled_var,
        template_notes_title_var,
        template_notes_image_path_var,
        template_section_dividers_enabled_var,
        template_section_dividers_include_lesson_var,
        template_section_easy_title_var,
        template_section_easy_image_path_var,
        template_section_medium_title_var,
        template_section_medium_image_path_var,
        template_section_hard_title_var,
        template_section_hard_image_path_var,
    ]:
        bind_var_autosave(v)

    for tw in [title_body, copyright_body, how_body, notes_body, easy_body, medium_body, hard_body]:
        bind_text_autosave(tw)

    # Start at first page
    page_list.selection_set(0)
    show_panel(str(page_list.get(0)))
    root.mainloop()
