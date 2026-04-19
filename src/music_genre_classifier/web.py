from __future__ import annotations

import base64
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from music_genre_classifier.audio_features import extract_bpm, extract_features
from music_genre_classifier.modeling import load_model

app = FastAPI(title="BeatMind.xo API")

MODEL_PATH = Path("artifacts/genre_model.joblib")

try:
    if MODEL_PATH.exists():
        bundle = load_model(MODEL_PATH)
        print("Model loaded successfully!")
    else:
        bundle = None
        print(f"Warning: Model not found at {MODEL_PATH}. Prediction will fail until trained.")
except Exception as e:
    bundle = None
    print(f"Error loading model: {e}")


def extract_track_metadata(file_path: str) -> dict:
    """Extract ID3/metadata tags from audio file using mutagen."""
    meta = {
        "title": None,
        "artist": None,
        "album": None,
        "year": None,
        "album_art": None,  # base64 encoded if found
    }
    try:
        from mutagen import File as MutagenFile
        audio = MutagenFile(file_path, easy=False)
        if audio is None:
            return meta

        # --- ID3 (MP3) tags ---
        if hasattr(audio, "tags") and audio.tags is not None:
            tags = audio.tags

            def _get(keys):
                for k in keys:
                    val = tags.get(k)
                    if val:
                        if hasattr(val, "text"):
                            return str(val.text[0]) if val.text else None
                        if hasattr(val, "__iter__") and not isinstance(val, str):
                            try:
                                return str(list(val)[0])
                            except Exception:
                                pass
                        return str(val)
                return None

            meta["title"]  = _get(["TIT2", "title", "\xa9nam"])
            meta["artist"] = _get(["TPE1", "artist", "\xa9ART", "TPE2"])
            meta["album"]  = _get(["TALB", "album", "\xa9alb"])
            meta["year"]   = _get(["TDRC", "date", "\xa9day", "TYER"])

            # Album art — ID3 APIC frame
            for key in tags.keys():
                if key.startswith("APIC"):
                    apic = tags[key]
                    if hasattr(apic, "data") and apic.data:
                        b64 = base64.b64encode(apic.data).decode("utf-8")
                        mime = getattr(apic, "mime", "image/jpeg")
                        meta["album_art"] = f"data:{mime};base64,{b64}"
                    break

        # --- MP4/AAC (mutagen.mp4) ---
        try:
            from mutagen.mp4 import MP4
            if isinstance(audio, MP4):
                t = audio.tags or {}
                meta["title"]  = meta["title"]  or (str(t["\xa9nam"][0]) if "\xa9nam" in t else None)
                meta["artist"] = meta["artist"] or (str(t["\xa9ART"][0]) if "\xa9ART" in t else None)
                meta["album"]  = meta["album"]  or (str(t["\xa9alb"][0]) if "\xa9alb" in t else None)
                meta["year"]   = meta["year"]   or (str(t["\xa9day"][0]) if "\xa9day" in t else None)
                if "covr" in t and t["covr"]:
                    cover = t["covr"][0]
                    b64 = base64.b64encode(bytes(cover)).decode("utf-8")
                    meta["album_art"] = f"data:image/jpeg;base64,{b64}"
        except Exception:
            pass

    except Exception as e:
        print(f"Metadata extraction warning: {e}")

    return meta


@app.post("/api/predict")
async def predict_genre(audio_file: UploadFile = File(...)):
    global bundle
    if bundle is None:
        if MODEL_PATH.exists():
            bundle = load_model(MODEL_PATH)
            print("Model dynamically loaded!")
        else:
            raise HTTPException(
                status_code=500,
                detail="Model is not trained or loaded. Please train a model first.",
            )

    suffix = Path(audio_file.filename).suffix if audio_file.filename else ".wav"
    with NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        content = await audio_file.read()
        temp_file.write(content)
        temp_path = temp_file.name

    try:
        # --- Song metadata ---
        track_meta = extract_track_metadata(temp_path)

        # --- BPM ---
        bpm = extract_bpm(temp_path, int(bundle["sample_rate"]), int(bundle["clip_duration"]))

        # --- Genre prediction ---
        feature_vector = extract_features(
            audio_path=temp_path,
            sample_rate=int(bundle["sample_rate"]),
            clip_duration=int(bundle["clip_duration"]),
        )
        model = bundle["model"]
        class_names = bundle["class_names"]

        predicted_index = int(model.predict(feature_vector.reshape(1, -1))[0])
        predicted_genre = class_names[predicted_index]

        response_data: dict = {
            "predicted_genre": predicted_genre,
            "probabilities": [],
            "track_meta": track_meta,
            "bpm": bpm,
            "genre_options": sorted(class_names),
        }

        if hasattr(model, "predict_proba"):
            probabilities = model.predict_proba(feature_vector.reshape(1, -1))[0]
            ranked = sorted(
                zip(class_names, probabilities, strict=True),
                key=lambda item: item[1],
                reverse=True,
            )
            response_data["probabilities"] = [
                {"genre": label, "probability": float(prob)}
                for label, prob in ranked
            ]

        return JSONResponse(content=response_data)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {e}")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


# Serve the static frontend folder
frontend_dir = Path("frontend")
frontend_dir.mkdir(parents=True, exist_ok=True)
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
