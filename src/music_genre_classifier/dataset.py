from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from music_genre_classifier.audio_features import extract_features
from music_genre_classifier.constants import SUPPORTED_EXTENSIONS


@dataclass(slots=True)
class GenreDataset:
    features: np.ndarray
    labels: np.ndarray
    class_names: list[str]
    file_paths: list[Path]


def iter_audio_files(data_dir: str | Path) -> list[tuple[str, Path]]:
    root = Path(data_dir)
    if not root.exists():
        raise FileNotFoundError(f"Dataset directory does not exist: {root}")

    discovered: list[tuple[str, Path]] = []
    for genre_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        for audio_file in sorted(genre_dir.iterdir()):
            if audio_file.suffix.lower() in SUPPORTED_EXTENSIONS and audio_file.is_file():
                discovered.append((genre_dir.name, audio_file))
    return discovered


def load_dataset(data_dir: str | Path, sample_rate: int = 22050, clip_duration: int = 30) -> GenreDataset:
    items = iter_audio_files(data_dir)
    if not items:
        raise ValueError(
            "No audio files were found. Expected folders like dataset/rock/*.wav and dataset/jazz/*.wav."
        )

    class_names = sorted({genre for genre, _ in items})
    class_to_index = {name: index for index, name in enumerate(class_names)}

    features: list[np.ndarray] = []
    labels: list[int] = []
    file_paths: list[Path] = []

    skipped = 0
    for genre, audio_path in items:
        try:
            feat = extract_features(audio_path, sample_rate=sample_rate, clip_duration=clip_duration)
            features.append(feat)
            labels.append(class_to_index[genre])
            file_paths.append(audio_path)
        except Exception as exc:
            print(f"  ⚠ Skipping {audio_path.name}: {exc}")
            skipped += 1

    if skipped:
        print(f"  Skipped {skipped} file(s) due to read errors.")

    return GenreDataset(
        features=np.vstack(features),
        labels=np.asarray(labels, dtype=np.int64),
        class_names=class_names,
        file_paths=file_paths,
    )


def summarize_dataset(data_dir: str | Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    for genre, _ in iter_audio_files(data_dir):
        counts[genre] = counts.get(genre, 0) + 1
    return counts
