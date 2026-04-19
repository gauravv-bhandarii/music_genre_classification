from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile

import streamlit as st

from music_genre_classifier.audio_features import extract_features
from music_genre_classifier.dataset import load_dataset, summarize_dataset
from music_genre_classifier.modeling import load_model, save_model, train_model


DEFAULT_DATA_DIR = Path("dataset")
DEFAULT_MODEL_PATH = Path("artifacts/genre_model.joblib")


st.set_page_config(page_title="Music Genre Classification", page_icon="🎵", layout="centered")
st.title("Music Genre Classification")
st.caption("Train a simple audio classifier and predict genres from uploaded clips.")


def render_dataset_summary(data_dir: Path) -> None:
    st.subheader("Dataset")
    if not data_dir.exists():
        st.info(f"Dataset folder not found: {data_dir}")
        return

    summary = summarize_dataset(data_dir)
    if not summary:
        st.warning("No supported audio files found yet.")
        return

    st.write(f"Total files: {sum(summary.values())}")
    st.dataframe(
        [{"genre": genre, "count": count} for genre, count in sorted(summary.items())],
        use_container_width=True,
        hide_index=True,
    )


def render_training(data_dir: Path, model_path: Path) -> None:
    st.subheader("Train Model")
    sample_rate = st.number_input("Sample rate", min_value=8000, max_value=48000, value=22050, step=50)
    clip_duration = st.number_input("Clip duration (seconds)", min_value=5, max_value=120, value=30, step=1)
    test_size = st.slider("Test split", min_value=0.1, max_value=0.4, value=0.2, step=0.05)

    if st.button("Train and save model", type="primary"):
        try:
            dataset = load_dataset(data_dir=data_dir, sample_rate=int(sample_rate), clip_duration=int(clip_duration))
            model, metrics = train_model(
                features=dataset.features,
                labels=dataset.labels,
                class_names=dataset.class_names,
                test_size=float(test_size),
            )
            save_model(
                model=model,
                class_names=dataset.class_names,
                sample_rate=int(sample_rate),
                clip_duration=int(clip_duration),
                output_path=model_path,
            )
        except Exception as exc:
            st.error(f"Training failed: {exc}")
            return

        st.success(f"Model saved to {model_path.resolve()}")
        st.metric("Accuracy", f"{metrics['accuracy']:.4f}")
        st.text("Classification report")
        st.code(str(metrics["report"]))


def render_prediction(model_path: Path) -> None:
    st.subheader("Predict Genre")
    if not model_path.exists():
        st.info("Train a model first so prediction can use it.")
        return

    uploaded = st.file_uploader("Upload an audio file", type=["wav", "mp3", "flac", "ogg", "au", "aiff", "m4a"])
    if uploaded is None:
        return

    bundle = load_model(model_path)
    suffix = Path(uploaded.name).suffix or ".wav"

    with NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_file.write(uploaded.getbuffer())
        temp_path = Path(temp_file.name)

    try:
        features = extract_features(
            audio_path=temp_path,
            sample_rate=int(bundle["sample_rate"]),
            clip_duration=int(bundle["clip_duration"]),
        )
        model = bundle["model"]
        class_names = bundle["class_names"]
        predicted_index = int(model.predict(features.reshape(1, -1))[0])
        st.success(f"Predicted genre: {class_names[predicted_index]}")

        if hasattr(model, "predict_proba"):
            probabilities = model.predict_proba(features.reshape(1, -1))[0]
            ranked = sorted(zip(class_names, probabilities, strict=True), key=lambda item: item[1], reverse=True)
            st.dataframe(
                [{"genre": label, "probability": float(probability)} for label, probability in ranked],
                use_container_width=True,
                hide_index=True,
            )
    except Exception as exc:
        st.error(f"Prediction failed: {exc}")
    finally:
        temp_path.unlink(missing_ok=True)


def main() -> None:
    data_dir_input = st.text_input("Dataset directory", value=str(DEFAULT_DATA_DIR))
    model_path_input = st.text_input("Model path", value=str(DEFAULT_MODEL_PATH))

    data_dir = Path(data_dir_input)
    model_path = Path(model_path_input)

    render_dataset_summary(data_dir)
    render_training(data_dir, model_path)
    render_prediction(model_path)


if __name__ == "__main__":
    main()
