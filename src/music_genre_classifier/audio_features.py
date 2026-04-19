from __future__ import annotations

from pathlib import Path

import librosa
import numpy as np


def extract_features(audio_path: str | Path, sample_rate: int = 22050, clip_duration: int = 30) -> np.ndarray:
    """Extract a fixed-length feature vector from an audio file."""
    import soundfile as sf
    try:
        signal, loaded_sr = sf.read(str(audio_path), dtype='float32', always_2d=False)
        if signal.ndim > 1:
            signal = signal.mean(axis=1)  # stereo → mono
        # Resample if needed
        if loaded_sr != sample_rate:
            signal = librosa.resample(signal, orig_sr=loaded_sr, target_sr=sample_rate)
        sr = sample_rate
        # Clip to duration
        max_samples = sample_rate * clip_duration
        signal = signal[:max_samples]
    except Exception:
        # fallback to librosa default loader
        signal, sr = librosa.load(path=str(audio_path), sr=sample_rate, mono=True, duration=clip_duration)

    if signal.size == 0:
        raise ValueError(f"No audio samples found in {audio_path}")

    mfcc = librosa.feature.mfcc(y=signal, sr=sr, n_mfcc=20)
    chroma = librosa.feature.chroma_stft(y=signal, sr=sr)
    spectral_centroid = librosa.feature.spectral_centroid(y=signal, sr=sr)
    spectral_rolloff = librosa.feature.spectral_rolloff(y=signal, sr=sr)
    zero_crossing_rate = librosa.feature.zero_crossing_rate(y=signal)
    tempo, _ = librosa.beat.beat_track(y=signal, sr=sr)

    stats = [
        mfcc.mean(axis=1),
        mfcc.std(axis=1),
        chroma.mean(axis=1),
        chroma.std(axis=1),
        spectral_centroid.mean(axis=1),
        spectral_centroid.std(axis=1),
        spectral_rolloff.mean(axis=1),
        spectral_rolloff.std(axis=1),
        zero_crossing_rate.mean(axis=1),
        zero_crossing_rate.std(axis=1),
        np.array([tempo.item() if isinstance(tempo, np.ndarray) else float(tempo)], dtype=np.float64),
    ]
    return np.concatenate(stats, axis=0).astype(np.float32)


def extract_bpm(audio_path: str | Path, sample_rate: int = 22050, clip_duration: int = 30) -> float:
    """Extract tempo (BPM) from an audio file."""
    import soundfile as sf
    try:
        signal, loaded_sr = sf.read(str(audio_path), dtype='float32', always_2d=False)
        if signal.ndim > 1:
            signal = signal.mean(axis=1)
        if loaded_sr != sample_rate:
            signal = librosa.resample(signal, orig_sr=loaded_sr, target_sr=sample_rate)
        signal = signal[:sample_rate * clip_duration]
    except Exception:
        signal, _ = librosa.load(path=str(audio_path), sr=sample_rate, mono=True, duration=clip_duration)
    if signal.size == 0:
        return 0.0
    tempo, _ = librosa.beat.beat_track(y=signal, sr=sample_rate)
    return round(float(tempo.item() if isinstance(tempo, np.ndarray) else float(tempo)))
