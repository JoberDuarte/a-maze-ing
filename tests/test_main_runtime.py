from __future__ import annotations

import builtins
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import a_maze_ing


def _write_config(path: Path, *, output_file: Path, display: str) -> None:
    path.write_text(
        "\n".join(
            [
                "WIDTH=10",
                "HEIGHT=10",
                "ENTRY=0,0",
                "EXIT=9,9",
                f"OUTPUT_FILE={output_file}",
                "PERFECT=True",
                "SEED=123",
                f"DISPLAY={display}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def test_main_runs_without_pygame_when_display_none(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_file = tmp_path / "config.txt"
    output_file = tmp_path / "maze.txt"
    _write_config(config_file, output_file=output_file, display="NONE")

    monkeypatch.setattr(a_maze_ing.sys, "argv", ["a_maze_ing.py", str(config_file)])
    exit_code = a_maze_ing.main()

    assert exit_code == 0
    assert output_file.exists()

    lines = output_file.read_text(encoding="utf-8").splitlines()
    assert len(lines) >= 13
    assert lines[10] == ""
    assert lines[11] == "0, 0"
    assert lines[12] == "9, 9"
    assert re.fullmatch(r"[NESW]+", lines[13])


def test_main_reports_clear_error_when_gui_requires_pygame(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    config_file = tmp_path / "config.txt"
    output_file = tmp_path / "maze.txt"
    _write_config(config_file, output_file=output_file, display="GUI")

    real_import = builtins.__import__

    def fake_import(name: str, *args: object, **kwargs: object) -> object:
        if name == "pygame":
            raise ModuleNotFoundError("No module named 'pygame'", name="pygame")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    monkeypatch.setattr(a_maze_ing.sys, "argv", ["a_maze_ing.py", str(config_file)])

    exit_code = a_maze_ing.main()
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "DISPLAY=GUI requires pygame" in captured.out
