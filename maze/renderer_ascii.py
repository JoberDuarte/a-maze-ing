"""ASCII renderer with BFS animation and large markers.

This module produces an ANSI-colored ASCII view of a maze and provides an
interactive session helper that animates BFS and the final path.
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass

from maze.models import Direction, ALL_DIRECTIONS
from maze.solver import shortest_path_letters

MAX_BUILD_ATTEMPTS = 24


@dataclass
class RenderTheme:
    """Render theme colors matching the original Pygame palette."""

    bg_a: str
    bg_b: str
    wall_color: str
    path_color: str
    search_color: str
    entry_color: str
    exit_color: str
    pattern_42_color: str = "\033[38;2;215;170;35m"  # FILLED_BLOCK (Amarelo)
    reset: str = "\033[0m"


THEMES: list[RenderTheme] = [
    RenderTheme(
        bg_a="\033[48;2;30;30;38m",
        bg_b="\033[48;2;36;36;45m",
        wall_color="\033[38;2;255;255;255m",
        path_color="\033[38;2;0;120;255m",
        search_color="\033[38;2;80;80;80m",
        entry_color="\033[38;2;0;200;0m",
        exit_color="\033[38;2;200;0;0m",
    ),
    RenderTheme(
        bg_a="\033[48;2;12;20;26m",
        bg_b="\033[48;2;20;30;40m",
        wall_color="\033[38;2;120;220;255m",
        path_color="\033[38;2;140;255;170m",
        search_color="\033[38;2;130;205;255m",
        entry_color="\033[38;2;255;210;80m",
        exit_color="\033[38;2;255;120;220m",
    ),
]


def _bfs_visit_order(grid, width, height, entry, exit_):
    ex, ey = entry
    tx, ty = exit_
    queue = deque([(ex, ey)])
    visited = {(ex, ey)}
    order = [(ex, ey)]

    while queue:
        x, y = queue.popleft()
        if (x, y) == (tx, ty):
            break

        for direction in ALL_DIRECTIONS:
            if grid[y][x].has_wall(direction):
                continue

            nx = x + direction.dx
            ny = y + direction.dy

            if not (0 <= nx < width and 0 <= ny < height):
                continue

            if (nx, ny) in visited:
                continue

            visited.add((nx, ny))
            queue.append((nx, ny))
            order.append((nx, ny))

    return order


def _path_cells_from_letters(
    entry: tuple[int, int],
    letters: str,
) -> list[tuple[int, int]]:
    x, y = entry
    path = [(x, y)]

    for m in letters:
        if m == "N":
            y -= 1
        elif m == "E":
            x += 1
        elif m == "S":
            y += 1
        elif m == "W":
            x -= 1

        path.append((x, y))

    return path


def render_ascii(
    grid: list[list[object]],
    width: int,
    height: int,
    entry: tuple[int, int],
    exit_: tuple[int, int],
    search_visited: set[tuple[int, int]] = None,
    path_visited: set[tuple[int, int]] = None,
    pattern_42_cells: set[tuple[int, int]] = None,
    theme_index: int = 0,
) -> str:
    theme = THEMES[theme_index % len(THEMES)]
    search_visited = search_visited or set()
    path_visited = path_visited or set()
    pattern_42_cells = pattern_42_cells or set()
    out_lines: list[str] = []

    # Top border
    top_left = theme.wall_color + "┏"
    top_middle = "━━━┳" * (width - 1)
    top_right = "━━━┓" + theme.reset
    out_lines.append(top_left + top_middle + top_right)

    for y in range(height):
        line_mid = ""

        for x in range(width):
            cell = grid[y][x]
            bg = theme.bg_a if (x + y) % 2 == 0 else theme.bg_b

            # West wall / spacer
            if cell.has_wall(Direction.WEST):
                west_seg = theme.wall_color + "┃" + theme.reset
            else:
                west_seg = bg + " " + theme.reset

            line_mid += west_seg

            # Content (priority: 42 pattern > entry/exit > path > search)
            symbol = " "
            color = bg
            if (x, y) in pattern_42_cells:
                symbol, color = "█", theme.pattern_42_color
            elif (x, y) == entry:
                symbol, color = "E", theme.entry_color
            elif (x, y) == exit_:
                symbol, color = "X", theme.exit_color
            elif (x, y) in path_visited:
                symbol, color = "█", theme.path_color  # large path marker
            elif (x, y) in search_visited:
                symbol, color = "▓", theme.search_color  # dense search marker

            line_mid += f"{bg}{color} {symbol} {theme.reset}"

        # Eastmost wall or spacer
        if grid[y][width - 1].has_wall(Direction.EAST):
            line_mid += theme.wall_color + "┃" + theme.reset
        else:
            line_mid += " "

        out_lines.append(line_mid)

        if y < height - 1:
            line_div = theme.wall_color + "┣"

            for x in range(width):
                if grid[y][x].has_wall(Direction.SOUTH):
                    seg = "━━━"
                else:
                    bg_seg = theme.bg_a if (x + y) % 2 == 0 else theme.bg_b
                    seg_parts = [
                        theme.reset,
                        bg_seg,
                        "   ",
                        theme.reset,
                        theme.wall_color,
                    ]
                    seg = "".join(seg_parts)

                line_div += seg
                line_div += "╋" if x < width - 1 else "┫"

            out_lines.append(line_div + theme.reset)

    bottom_left = theme.wall_color + "┗"
    bottom_middle = "━━━┻" * (width - 1)
    bottom_right = "━━━┛" + theme.reset
    out_lines.append(bottom_left + bottom_middle + bottom_right)

    return "\n".join(out_lines)


def interactive_ascii_session(
    generator_factory,
    width,
    height,
    entry,
    exit_,
    perfect,
):
    show_path = True
    theme_idx = 0

    def build_and_animate():
        last_error: RuntimeError | None = None

        for _ in range(MAX_BUILD_ATTEMPTS):
            gen = generator_factory()
            maze = gen.generate(perfect=perfect)

            if not maze.pattern_42_applied:
                warn_msg = (
                    "Warning: '42' pattern could not be applied "
                    "(maze too small)."
                )
                print(warn_msg)

            try:
                path_str = shortest_path_letters(
                    maze.grid,
                    width,
                    height,
                    entry,
                    exit_,
                )
                search_order = _bfs_visit_order(
                    maze.grid,
                    width,
                    height,
                    entry,
                    exit_,
                )
                path_points = _path_cells_from_letters(entry, path_str)
                p42 = maze.pattern_42_cells or set()

                if show_path:
                    # BFS animation
                    for i in range(0, len(search_order), 3):
                        print("\033[H", end="")
                        print(render_ascii(
                            maze.grid,
                            width,
                            height,
                            entry,
                            exit_,
                            set(search_order[:i]),
                            set(),
                            p42,
                            theme_idx,
                        ))
                        time.sleep(0.01)

                    # Path animation
                    for i in range(len(path_points) + 1):
                        print("\033[H", end="")
                        print(render_ascii(
                            maze.grid,
                            width,
                            height,
                            entry,
                            exit_,
                            set(search_order),
                            set(path_points[:i]),
                            p42,
                            theme_idx,
                        ))
                        time.sleep(0.04)

                return maze.grid, search_order, path_points, p42

            except RuntimeError as exc:
                last_error = exc
                continue

        if last_error is None:
            raise RuntimeError("Could not generate a valid maze path.")

        msg = (
            f"Could not generate a valid maze path after "
            f"{MAX_BUILD_ATTEMPTS} attempts."
        )
        raise RuntimeError(msg) from last_error

    grid, search_order, path_points, p42 = build_and_animate()

    while True:
        print("\033[H", end="")
        print(
            render_ascii(
                grid,
                width,
                height,
                entry,
                exit_,
                set(search_order) if show_path else set(),
                set(path_points) if show_path else set(),
                p42,
                theme_idx,
            )
        )

        ctrl_color = THEMES[theme_idx % 2].wall_color
        ctrl_reset = THEMES[theme_idx % 2].reset
        ctrl_msg = "R: New | P: Path | C: Color | Q: Quit"
        print("\n" + ctrl_color + ctrl_msg + ctrl_reset)

        cmd = input("> ").strip().lower()
        if cmd == "q":
            break
        elif cmd == "c":
            theme_idx = (theme_idx + 1) % len(THEMES)
        elif cmd == "p":
            show_path = not show_path
        elif cmd == "r":
            (
                grid,
                search_order,
                path_points,
                p42,
            ) = build_and_animate()
