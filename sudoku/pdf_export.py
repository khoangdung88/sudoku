import json
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from .difficulty import Difficulty
from .lessons import LessonCatalog

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import landscape, portrait
    from reportlab.lib.units import inch
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen.canvas import Canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
except ImportError as e:  # pragma: no cover
    raise ImportError(
        "Missing dependency 'reportlab'. Install it with: pip install -r requirements.txt"
    ) from e


@dataclass(frozen=True)
class ExportConfig:
    page_width_in: float
    page_height_in: float
    orientation: str
    margin_in: float
    puzzles_per_page: int
    show_level: bool
    level_field: str
    title: str
    title_font: str
    title_font_size: int
    label_font: str
    label_font_size: int
    grid_line_width: float
    subgrid_line_width: float
    digit_font: str
    digit_font_size: int
    answer_key_title: str
    answers_per_page: int
    pdf_title: str
    pdf_author: str
    pdf_subject: str
    pdf_keywords: str
    header_enabled: bool
    header_height_in: float
    header_font: str
    header_font_size: int
    header_show_page_number: bool
    text_color: str
    grid_color: str
    header_line_color: str
    header_icon_path: str
    header_icon_height_in: float
    custom_fonts: List[Dict[str, str]]
    template: Dict[str, object]

    @staticmethod
    def from_dict(d: Dict[str, object]) -> "ExportConfig":
        return ExportConfig(
            page_width_in=float(d.get("page_width_in", 8.5)),
            page_height_in=float(d.get("page_height_in", 11.0)),
            orientation=str(d.get("orientation", "portrait")),
            margin_in=float(d.get("margin_in", 0.5)),
            puzzles_per_page=int(d.get("puzzles_per_page", 4)),
            show_level=bool(d.get("show_level", True)),
            level_field=str(d.get("level_field", "difficulty")),
            title=str(d.get("title", "Sudoku")),
            title_font=str(d.get("title_font", "Helvetica-Bold")),
            title_font_size=int(d.get("title_font_size", 18)),
            label_font=str(d.get("label_font", "Helvetica")),
            label_font_size=int(d.get("label_font_size", 10)),
            grid_line_width=float(d.get("grid_line_width", 0.6)),
            subgrid_line_width=float(d.get("subgrid_line_width", 1.4)),
            digit_font=str(d.get("digit_font", "Helvetica")),
            digit_font_size=int(d.get("digit_font_size", 12)),
            answer_key_title=str(d.get("answer_key_title", "Answer Key")),
            answers_per_page=int(d.get("answers_per_page", 6)),
            pdf_title=str(d.get("pdf_title", d.get("title", "Sudoku"))),
            pdf_author=str(d.get("pdf_author", "")),
            pdf_subject=str(d.get("pdf_subject", "")),
            pdf_keywords=str(d.get("pdf_keywords", "")),
            header_enabled=bool(d.get("header_enabled", True)),
            header_height_in=float(d.get("header_height_in", 0.35)),
            header_font=str(d.get("header_font", "Helvetica")),
            header_font_size=int(d.get("header_font_size", 10)),
            header_show_page_number=bool(d.get("header_show_page_number", True)),
            text_color=str(d.get("text_color", "#000000")),
            grid_color=str(d.get("grid_color", "#000000")),
            header_line_color=str(d.get("header_line_color", "#000000")),
            header_icon_path=str(d.get("header_icon_path", "")),
            header_icon_height_in=float(d.get("header_icon_height_in", 0.22)),
            custom_fonts=list(d.get("custom_fonts", [])) if isinstance(d.get("custom_fonts", []), list) else [],
            template=dict(d.get("template", {})) if isinstance(d.get("template", {}), dict) else {},
        )


def _hex_color(s: str):
    try:
        return colors.HexColor(str(s).strip())
    except Exception:
        return colors.black


def _register_custom_fonts(custom_fonts: List[Dict[str, str]]) -> None:
    for item in custom_fonts:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "")).strip()
        path = str(item.get("path", "")).strip()
        if not name or not path:
            continue
        try:
            pdfmetrics.getFont(name)
            continue
        except Exception:
            pass
        try:
            pdfmetrics.registerFont(TTFont(name, path))
        except Exception:
            continue


def _safe_set_font(c: Canvas, name: str, size: int) -> None:
    try:
        c.setFont(name, size)
    except Exception:
        c.setFont("Helvetica", size)


def export_sudoku_json_to_pdf(input_json_path: str, output_pdf_path: str, cfg: ExportConfig) -> None:
    with open(input_json_path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    items = payload.get("items", [])
    if not isinstance(items, list):
        raise ValueError("Invalid sudoku JSON: items must be a list")

    puzzles: List[Dict[str, object]] = []
    for it in items:
        if not isinstance(it, dict):
            continue
        puzzles.append(it)

    page_size = (cfg.page_width_in * inch, cfg.page_height_in * inch)
    if cfg.orientation.lower() == "landscape":
        page_size = landscape(page_size)
    else:
        page_size = portrait(page_size)

    c = Canvas(output_pdf_path, pagesize=page_size)
    if cfg.pdf_title:
        c.setTitle(cfg.pdf_title)
    if cfg.pdf_author:
        c.setAuthor(cfg.pdf_author)
    if cfg.pdf_subject:
        c.setSubject(cfg.pdf_subject)
    if cfg.pdf_keywords:
        c.setKeywords(cfg.pdf_keywords)

    _register_custom_fonts(cfg.custom_fonts)
    preferred_font: Optional[str] = None
    if cfg.custom_fonts:
        try:
            first = cfg.custom_fonts[0]
            if isinstance(first, dict):
                preferred_font = str(first.get("name", "")).strip() or None
        except Exception:
            preferred_font = None

    def _pick_font(primary: str) -> str:
        if preferred_font:
            return preferred_font
        return primary

    _register_custom_fonts(cfg.custom_fonts)
    width, height = page_size

    text_color = _hex_color(cfg.text_color)
    grid_color = _hex_color(cfg.grid_color)
    header_line_color = _hex_color(cfg.header_line_color)

    margin = cfg.margin_in * inch

    def _draw_image_cover(image_path: str, *, x: float, y: float, w: float, h: float) -> None:
        """Draw image to fully cover the target box (scale-to-fill + crop), no letterboxing."""
        img = ImageReader(image_path)
        iw, ih = img.getSize()
        if not iw or not ih:
            return
        scale = max(w / float(iw), h / float(ih))
        dw = float(iw) * scale
        dh = float(ih) * scale
        dx = x - (dw - w) / 2.0
        dy = y - (dh - h) / 2.0
        c.drawImage(img, dx, dy, width=dw, height=dh, mask='auto')

    def draw_header(*, page_title: str) -> float:
        if not cfg.header_enabled:
            return height - margin

        header_h = cfg.header_height_in * inch
        y_top = height - margin
        y_bottom = y_top - header_h

        c.setStrokeColor(header_line_color)
        c.setLineWidth(0.8)
        c.line(margin, y_bottom, width - margin, y_bottom)

        c.setFillColor(text_color)
        _safe_set_font(c, _pick_font(cfg.header_font), cfg.header_font_size)

        text_x = margin
        icon_path = (cfg.header_icon_path or "").strip()
        if icon_path:
            try:
                icon_h = max(0.05 * inch, cfg.header_icon_height_in * inch)
                icon_w = icon_h
                icon_y = y_bottom + (header_h - icon_h) / 2
                c.drawImage(icon_path, margin, icon_y, width=icon_w, height=icon_h, mask='auto', preserveAspectRatio=True)
                text_x = margin + icon_w + 8
            except Exception:
                text_x = margin

        c.drawString(text_x, y_bottom + header_h * 0.28, page_title)

        if cfg.header_show_page_number:
            c.drawRightString(width - margin, y_bottom + header_h * 0.28, str(c.getPageNumber()))

        content_pad = max(0.18 * inch, cfg.label_font_size * 1.0)
        return y_bottom - content_pad

    def _wrap_lines(text: str, *, font_name: str, font_size: int, max_width: float) -> List[str]:
        words = str(text).replace("\r\n", "\n").replace("\r", "\n").split()
        if not words:
            return []
        lines: List[str] = []
        cur = words[0]
        for w in words[1:]:
            trial = cur + " " + w
            try:
                w_trial = pdfmetrics.stringWidth(trial, font_name, font_size)
            except Exception:
                w_trial = pdfmetrics.stringWidth(trial, "Helvetica", font_size)
            if w_trial <= max_width:
                cur = trial
            else:
                lines.append(cur)
                cur = w
        lines.append(cur)
        return lines

    def draw_text_page(*, header_title: str, title: str, body: str, image_path: str = "") -> None:
        # If image provided, draw full-page image instead of text
        if image_path and os.path.exists(image_path):
            try:
                _draw_image_cover(image_path, x=0, y=0, w=width, h=height)
                c.showPage()
                return
            except Exception:
                pass  # Fallback to text if image fails
            
        # Text content rendering
        top = draw_header(page_title=header_title)
        x = margin
        y = top - cfg.title_font_size * 0.3
        c.setFillColor(text_color)
        _safe_set_font(c, _pick_font(cfg.title_font), cfg.title_font_size)
        c.drawString(x, y, title)
        y -= cfg.title_font_size * 1.6

        _safe_set_font(c, _pick_font(cfg.label_font), cfg.label_font_size)
        max_w = width - 2 * margin
        line_h = cfg.label_font_size * 1.35
        for raw_para in str(body).split("\n"):
            if raw_para.strip() == "":
                y -= line_h
                continue
            for line in _wrap_lines(raw_para, font_name=_pick_font(cfg.label_font), font_size=cfg.label_font_size, max_width=max_w):
                if y <= margin + line_h:
                    break
                c.drawString(x, y, line)
                y -= line_h
            y -= line_h * 0.4

        c.showPage()

    def draw_cover_page(image_path: str) -> None:
        if not image_path:
            return
        try:
            _draw_image_cover(image_path, x=0, y=0, w=width, h=height)
            c.showPage()
        except Exception:
            return

    def tget(key: str, default: object) -> object:
        return cfg.template.get(key, default)

    lesson_catalog = LessonCatalog()

    def level_lesson_body(level: str) -> str:
        lv = str(level).lower()
        try:
            if lv == "easy":
                return lesson_catalog._by_diff[Difficulty.EASY].body
            if lv == "medium":
                return lesson_catalog._by_diff[Difficulty.MEDIUM].body
            if lv == "hard":
                return lesson_catalog._by_diff[Difficulty.HARD].body
        except Exception:
            return ""
        return ""

    def layout_for(n: int) -> Tuple[int, int]:
        if n == 1:
            return 1, 1
        if n == 2:
            return 1, 2
        if n == 3:
            return 1, 3
        if n == 4:
            return 2, 2
        if n == 6:
            return 2, 3
        if n == 8:
            return 2, 4
        if n == 9:
            return 3, 3
        return 2, 2

    def parse_grid(s: str) -> Tuple[int, List[List[int]]]:
        """Parse grid string and return (size, grid)."""
        s = str(s).strip()
        # Determine size from string length
        length = len(s)
        size = int(length ** 0.5)
        if size * size != length:
            raise ValueError(f"Puzzle/solution string length {length} is not a perfect square")
        vals = [int(ch) for ch in s]
        return size, [vals[i * size : (i + 1) * size] for i in range(size)]

    def draw_grid(x: float, y: float, size_px: float, grid_data: Tuple[int, List[List[int]]], *, show_digits: bool) -> None:
        """Draw Sudoku grid with variable size."""
        size, grid = grid_data
        cell = size_px / size
        c.setStrokeColor(grid_color)

        # Determine subgrid dimensions based on grid size
        if size == 4:
            box_rows, box_cols = 2, 2
        elif size == 6:
            box_rows, box_cols = 2, 3
        elif size == 9:
            box_rows, box_cols = 3, 3
        elif size == 12:
            box_rows, box_cols = 3, 4
        elif size == 16:
            box_rows, box_cols = 4, 4
        else:
            box_rows = box_cols = int(size ** 0.5)

        # Draw thin lines
        c.setLineWidth(cfg.grid_line_width)
        for i in range(size + 1):
            c.line(x, y + i * cell, x + size_px, y + i * cell)
            c.line(x + i * cell, y, x + i * cell, y + size_px)

        # Draw thick subgrid lines
        c.setLineWidth(cfg.subgrid_line_width)
        for i in range(0, size + 1, box_rows):
            c.line(x, y + i * cell, x + size_px, y + i * cell)
        for i in range(0, size + 1, box_cols):
            c.line(x + i * cell, y, x + i * cell, y + size_px)

        if not show_digits:
            return

        c.setFillColor(text_color)
        # Adjust font size based on grid size
        digit_size = cfg.digit_font_size
        if size > 9:
            digit_size = int(digit_size * 0.7)  # Smaller digits for larger grids

        digit_font_name = cfg.digit_font
        try:
            c.setFont(digit_font_name, digit_size)
        except Exception:
            digit_font_name = "Helvetica"
            c.setFont(digit_font_name, digit_size)

        try:
            ascent = pdfmetrics.getAscent(digit_font_name) * digit_size / 1000.0
            descent = pdfmetrics.getDescent(digit_font_name) * digit_size / 1000.0
        except Exception:
            ascent = digit_size * 0.7
            descent = -digit_size * 0.2
        baseline_shift = (ascent + descent) / 2.0

        for r in range(size):
            for col in range(size):
                v = grid[r][col]
                if v == 0:
                    continue
                cx = x + (col + 0.5) * cell
                center_y = y + (size - 1 - r + 0.5) * cell
                cy = center_y - baseline_shift
                c.drawCentredString(cx, cy, str(v))

    def draw_label(x: float, y: float, text: str) -> None:
        c.setFillColor(text_color)
        _safe_set_font(c, cfg.label_font, cfg.label_font_size)
        c.drawString(x, y, text)

    template_cover = tget("cover", {})
    if isinstance(template_cover, dict) and bool(template_cover.get("enabled", False)):
        draw_cover_page(str(template_cover.get("image_path", "")))

    template_title = tget("title_page", {})
    if isinstance(template_title, dict) and bool(template_title.get("enabled", True)):
        tp_title = str(template_title.get("title", cfg.title))
        tp_body = str(template_title.get("body", ""))
        tp_image = str(template_title.get("image_path", ""))
        draw_text_page(header_title=cfg.title, title=tp_title, body=tp_body, image_path=tp_image)

    template_copyright = tget("copyright", {})
    if isinstance(template_copyright, dict) and bool(template_copyright.get("enabled", False)):
        draw_text_page(
            header_title=cfg.title,
            title=str(template_copyright.get("title", "Copyright")),
            body=str(template_copyright.get("body", "")),
            image_path=str(template_copyright.get("image_path", "")),
        )

    template_how = tget("how_to_play", {})
    if isinstance(template_how, dict) and bool(template_how.get("enabled", True)):
        draw_text_page(
            header_title=cfg.title,
            title=str(template_how.get("title", "How to Play")),
            body=str(template_how.get("body", "")),
            image_path=str(template_how.get("image_path", "")),
        )

    top_y = draw_header(page_title=cfg.title)

    rows, cols = layout_for(cfg.puzzles_per_page)
    usable_w = width - 2 * margin
    usable_h = top_y - margin

    slot_w = usable_w / cols
    slot_h = usable_h / rows

    grid_size = min(slot_w, slot_h) * 0.82

    def puzzle_page(page_items: List[Dict[str, object]], start_index: int, *, header_title: str) -> None:
        nonlocal top_y
        top_y = draw_header(page_title=header_title)
        for idx, it in enumerate(page_items):
            r = idx // cols
            col = idx % cols
            slot_x = margin + col * slot_w
            slot_top = top_y - r * slot_h
            gx = slot_x + (slot_w - grid_size) / 2
            gy = slot_top - grid_size - cfg.label_font_size * 1.8

            puzzle_str = it.get("puzzle", "")
            level = str(it.get(cfg.level_field, ""))

            if cfg.show_level:
                draw_label(gx, gy + grid_size + cfg.label_font_size * 0.6, f"#{start_index + idx}  Level: {level}")
            else:
                draw_label(gx, gy + grid_size + cfg.label_font_size * 0.6, f"#{start_index + idx}")

            grid_data = parse_grid(puzzle_str)
            draw_grid(gx, gy, grid_size, grid_data, show_digits=True)

        c.showPage()

    order = ["easy", "medium", "hard"]
    buckets: Dict[str, List[Dict[str, object]]] = {k: [] for k in order}
    other: List[Dict[str, object]] = []
    for it in puzzles:
        lv = str(it.get(cfg.level_field, "")).lower()
        if lv in buckets:
            buckets[lv].append(it)
        else:
            other.append(it)

    section_divider = tget("section_dividers", {})
    section_divider_enabled = bool(section_divider.get("enabled", True)) if isinstance(section_divider, dict) else True
    section_divider_include_lesson = (
        bool(section_divider.get("include_level_lesson", True)) if isinstance(section_divider, dict) else True
    )

    def _divider_cfg_for(level: str) -> Dict[str, object]:
        if isinstance(section_divider, dict):
            v = section_divider.get(level)
            if isinstance(v, dict):
                return v
        return {}

    def draw_section_divider(level: str) -> None:
        cfg_lv = _divider_cfg_for(level)
        title = str(cfg_lv.get("title", f"Puzzle Section: {level.title()}"))
        body = str(cfg_lv.get("body", ""))
        image_path = str(cfg_lv.get("image_path", ""))

        if section_divider_include_lesson:
            lesson = level_lesson_body(level)
            if lesson:
                body = (body + "\n\n" + lesson).strip() if body.strip() else lesson
        draw_text_page(header_title=cfg.title, title=title, body=body, image_path=image_path)

    per_page = cfg.puzzles_per_page
    page_start = 1
    for lv in ("easy", "medium", "hard"):
        items_lv = buckets[lv]
        if not items_lv:
            continue
        if section_divider_enabled:
            draw_section_divider(lv)

        buf: List[Dict[str, object]] = []
        header_title = f"{cfg.title} - {lv.title()}"
        for it in items_lv:
            buf.append(it)
            if len(buf) == per_page:
                puzzle_page(buf, page_start, header_title=header_title)
                page_start += len(buf)
                buf = []
        if buf:
            puzzle_page(buf, page_start, header_title=header_title)
            page_start += len(buf)

    if other:
        if section_divider_enabled:
            draw_text_page(header_title=cfg.title, title="Puzzle Section", body="")
        buf2: List[Dict[str, object]] = []
        for it in other:
            buf2.append(it)
            if len(buf2) == per_page:
                puzzle_page(buf2, page_start, header_title=cfg.title)
                page_start += len(buf2)
                buf2 = []
        if buf2:
            puzzle_page(buf2, page_start, header_title=cfg.title)
            page_start += len(buf2)

    def answer_key_pages() -> None:
        nonlocal top_y
        top_y = draw_header(page_title=cfg.answer_key_title)

        rows_a, cols_a = layout_for(cfg.answers_per_page)
        usable_w_a = width - 2 * margin
        usable_h_a = top_y - margin
        slot_w_a = usable_w_a / cols_a
        slot_h_a = usable_h_a / rows_a
        grid_size_a = min(slot_w_a, slot_h_a) * 0.78

        def draw_answer_page(page_items: List[Dict[str, object]], start_index: int) -> None:
            page_top = draw_header(page_title=cfg.answer_key_title)

            for idx, it in enumerate(page_items):
                r = idx // cols_a
                col = idx % cols_a
                slot_x = margin + col * slot_w_a
                slot_top = page_top - r * slot_h_a
                gx = slot_x + (slot_w_a - grid_size_a) / 2
                gy = slot_top - grid_size_a - cfg.label_font_size * 1.6

                sol_str = it.get("solution", "")
                grid_data = parse_grid(sol_str)
                draw_label(gx, gy + grid_size_a + cfg.label_font_size * 0.5, f"#{start_index + idx}")
                draw_grid(gx, gy, grid_size_a, grid_data, show_digits=True)

            c.showPage()

        per_a = cfg.answers_per_page
        start = 1
        buf2: List[Dict[str, object]] = []
        for it in puzzles:
            buf2.append(it)
            if len(buf2) == per_a:
                draw_answer_page(buf2, start)
                start += len(buf2)
                buf2 = []
        if buf2:
            draw_answer_page(buf2, start)

    answer_key_pages()

    template_notes = tget("notes_cta", {})
    if isinstance(template_notes, dict) and bool(template_notes.get("enabled", False)):
        draw_text_page(
            header_title=cfg.title,
            title=str(template_notes.get("title", "Notes / CTA")),
            body=str(template_notes.get("body", "")),
            image_path=str(template_notes.get("image_path", "")),
        )
    c.save()
