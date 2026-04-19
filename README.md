# BeatMind.xo 🎵

A premium, interactive AI-powered music genre classification web application built with FastAPI + Vanilla JS.

## Features

- 🎮 **Guess the Genre** — Game mode where you pick the genre before the AI reveals it
- 🥁 **BPM Detection** — Real tempo extracted from every audio file
- 🎛️ **Live Audio Visualizer** — Real-time frequency bar canvas that pulses with the music
- 💿 **Spinning Vinyl Record** — Animated CSS vinyl that rotates during playback
- 🌊 **Waveform Player** — Interactive waveform via WaveSurfer.js for scrubbing/playback
- 🎨 **Dynamic Genre Theming** — Entire UI colour palette shifts based on the predicted genre
- 📊 **Confidence Bars** — Animated probability bars for all predicted genres
- 🎤 **Track Metadata** — Artist, title and album art extracted from ID3/MP4 tags
- ▶️ **YouTube Link** — One-click search for the song's official video
- 📋 **Session History** — Slide-out sidebar logs every track you've analyzed
- 🏆 **Score Counter** — Tracks your guessing streak vs the AI
- 🎉 **Confetti** — Bursts in the genre's colours when you guess correctly
- 📎 **Share** — Copies a one-line summary to your clipboard
- ⌨️ **Keyboard Shortcuts** — `Space` play/pause · `R` reset · `S` share

## Supported Formats

`.wav` · `.mp3` · `.ogg` · `.flac` · `.m4a` · `.aac` · `.wma` · `.mp4` · `.mov` · `.avi`

## Tech Stack

| Layer    | Technology                                      |
|----------|-------------------------------------------------|
| Backend  | Python · FastAPI · librosa · scikit-learn · mutagen |
| Frontend | Vanilla HTML/CSS/JS · WaveSurfer.js · canvas-confetti |
| ML Model | Random Forest Classifier (sklearn Pipeline)     |

## Project Structure

```
beatmind-xo/
├── frontend/           # Full website (HTML, CSS, JS)
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── src/
│   └── music_genre_classifier/
│       ├── audio_features.py   # librosa feature extraction + BPM
│       ├── cli.py              # Training & prediction CLI
│       ├── dataset.py          # Dataset loading utilities
│       ├── modeling.py         # RandomForest pipeline
│       ├── prepare_dataset.py  # GTZAN data preparation helper
│       └── web.py              # FastAPI server
├── tests/
├── pyproject.toml
├── run_web.py          # Quick-start server script
└── README.md
```

## Setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .[web]
```

## Train a model

You need a dataset organised like:

```
dataset/
  rock/    song1.wav ...
  jazz/    song2.wav ...
  blues/   song3.wav ...
```

Then train:

```powershell
genre-classifier train --data-dir .\dataset --model-out .\artifacts\genre_model.joblib
```

## Run the web app

```powershell
python run_web.py
```

Open **http://127.0.0.1:8000** in your browser.

## Keyboard Shortcuts

| Key     | Action            |
|---------|-------------------|
| `Space` | Play / Pause      |
| `R`     | Reset / New track |
| `S`     | Share result      |

## Prepare GTZAN-style data

```powershell
prepare-gtzan --source .\Data\genres_original --target .\dataset
```

## Notes

- The ML model uses summary statistics over MFCC, chroma, tempo and spectral features.
- For production accuracy, consider training on the full GTZAN dataset (1000 tracks, 10 genres).
- A future upgrade path: swap the Random Forest for a CNN trained on mel-spectrograms.
