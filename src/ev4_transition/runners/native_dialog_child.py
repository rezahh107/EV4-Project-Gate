from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable


def _result(status: str, selected_path: str | None = None, error_type: str | None = None) -> str:
    payload = {"status": status, "selected_path": selected_path}
    if error_type:
        payload["error_type"] = error_type
    return json.dumps(payload, ensure_ascii=False)


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="EV4 native directory chooser child process")
    parser.add_argument("--initial-directory", default="")
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        initial = args.initial_directory if args.initial_directory and Path(args.initial_directory).is_dir() else None
        selected = filedialog.askdirectory(initialdir=initial, mustexist=True)
        root.destroy()
    except Exception as exc:
        print(_result("unavailable", error_type=type(exc).__name__))
        return 2

    if not selected:
        print(_result("cancelled"))
        return 0
    print(_result("selected", str(Path(selected))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
