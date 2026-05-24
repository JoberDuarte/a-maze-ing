"""Main entry point for A-Maze-ing."""

from __future__ import annotations

import sys

from maze.config import load_config
from maze.errors import ConfigError
from maze.generator import MazeGenerator
from maze.renderer_ascii import interactive_ascii_session
from maze.solver import shortest_path_letters
from maze.writer import write_maze_file


MAX_BUILD_ATTEMPTS = 24


def main() -> int:
    """Program entry point."""
    if len(sys.argv) != 2:
        print("Usage: python3 a_maze_ing.py <config_file>")
        return 1

    config_path = sys.argv[1]

    try:
        config = load_config(config_path)

        regen_counter = 0

        def generator_factory() -> MazeGenerator:
            """Create a generator with changing seed on each regeneration."""
            nonlocal regen_counter
            if config.seed is not None:
                effective_seed = config.seed + regen_counter
            else:
                effective_seed = None

            regen_counter += 1
            return MazeGenerator(
                width=config.width,
                height=config.height,
                seed=effective_seed,
            )

        last_error: RuntimeError | None = None
        maze = None
        path_letters = ""

        for _ in range(MAX_BUILD_ATTEMPTS):
            generator = generator_factory()
            candidate = generator.generate(perfect=config.perfect)

            if not candidate.pattern_42_applied:
                warn_msg = (
                    "Warning: '42' pattern could not be applied "
                    "(maze too small)."
                )
                print(warn_msg)

            try:
                candidate_path = shortest_path_letters(
                    grid=candidate.grid,
                    width=candidate.width,
                    height=candidate.height,
                    entry=config.entry,
                    exit_=config.exit,
                )
                maze = candidate
                path_letters = candidate_path
                break
            except RuntimeError as exc:
                last_error = exc

        if maze is None:
            if last_error is None:
                raise RuntimeError("Could not generate a valid maze path.")

            msg = (
                f"Could not generate a valid maze path after "
                f"{MAX_BUILD_ATTEMPTS} attempts."
            )
            raise RuntimeError(msg) from last_error

        write_maze_file(
            output_file=config.output_file,
            grid=maze.grid,
            entry=config.entry,
            exit_=config.exit,
            path_letters=path_letters,
        )

        print(f"Maze generated successfully: {config.output_file}")
        print(f"Shortest path length: {len(path_letters)}")

        # Always use ASCII renderer for this simplified build.
        interactive_ascii_session(
            generator_factory=generator_factory,
            width=config.width,
            height=config.height,
            entry=config.entry,
            exit_=config.exit,
            perfect=config.perfect,
        )

    except ConfigError as exc:
        print(f"Configuration error: {exc}")
        return 1
    except OSError as exc:
        print(f"I/O error: {exc}")
        return 1
    except RuntimeError as exc:
        print(f"Runtime error: {exc}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
    