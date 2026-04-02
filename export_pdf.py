import argparse
import json
import os
from datetime import datetime

from sudoku.pdf_export import ExportConfig, export_sudoku_json_to_pdf


def timestamp_folder_name() -> str:
    now = datetime.now()
    return f"{now.minute:02d}_{now.hour:02d}_{now.day:02d}_{now.month:02d}"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True, help="Path to sudoku batch JSON")
    p.add_argument("--config", required=True, help="Path to PDF export config JSON")
    p.add_argument("--outdir", default=os.path.join(os.getcwd(), "output"), help="Base output folder")
    args = p.parse_args()

    with open(args.config, "r", encoding="utf-8") as f:
        cfg_raw = json.load(f)
    cfg = ExportConfig.from_dict(cfg_raw)

    out_dir = os.path.join(args.outdir, timestamp_folder_name())
    os.makedirs(out_dir, exist_ok=True)

    out_path = os.path.join(out_dir, "sudoku_book.pdf")
    export_sudoku_json_to_pdf(args.input, out_path, cfg)
    print(out_path)


if __name__ == "__main__":
    main()
