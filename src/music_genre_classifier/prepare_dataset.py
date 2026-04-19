from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from music_genre_classifier.constants import SUPPORTED_EXTENSIONS


def detect_genre_root(source: Path) -> Path:
    direct_children = [path for path in source.iterdir() if path.is_dir()]
    if any(any(file.is_file() and file.suffix.lower() in SUPPORTED_EXTENSIONS for file in child.iterdir()) for child in direct_children):
        return source

    if len(direct_children) == 1:
        nested_children = [path for path in direct_children[0].iterdir() if path.is_dir()]
        if any(
            any(file.is_file() and file.suffix.lower() in SUPPORTED_EXTENSIONS for file in child.iterdir())
            for child in nested_children
        ):
            return direct_children[0]

    raise ValueError(
        "Could not detect genre folders under the source path. Expected a layout like genres_original/blues/*.wav."
    )


def copy_genre_dataset(source: Path, target: Path) -> dict[str, int]:
    genre_root = detect_genre_root(source)
    counts: dict[str, int] = {}

    for genre_dir in sorted(path for path in genre_root.iterdir() if path.is_dir()):
        destination_dir = target / genre_dir.name
        destination_dir.mkdir(parents=True, exist_ok=True)

        copied = 0
        for audio_file in sorted(genre_dir.iterdir()):
            if audio_file.is_file() and audio_file.suffix.lower() in SUPPORTED_EXTENSIONS:
                shutil.copy2(audio_file, destination_dir / audio_file.name)
                copied += 1

        if copied:
            counts[genre_dir.name] = copied
    return counts


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Copy a GTZAN-style dataset into this project's folder layout.")
    parser.add_argument("--source", required=True, help="Path to the extracted source dataset")
    parser.add_argument("--target", default="dataset", help="Destination directory for the copied dataset")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    source = Path(args.source).expanduser().resolve()
    target = Path(args.target).expanduser().resolve()

    if not source.exists():
        raise FileNotFoundError(f"Source dataset path does not exist: {source}")

    counts = copy_genre_dataset(source=source, target=target)
    if not counts:
        print("No supported audio files were copied.")
        return 1

    total = sum(counts.values())
    print(f"Copied {total} audio files into {target}")
    for genre, count in sorted(counts.items()):
        print(f"{genre}: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
