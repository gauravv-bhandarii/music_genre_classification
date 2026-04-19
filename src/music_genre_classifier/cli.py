from __future__ import annotations

import argparse
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Train and run a music genre classifier.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    train_parser = subparsers.add_parser("train", help="Train a model from a genre-organized dataset.")
    train_parser.add_argument("--data-dir", required=True, help="Dataset root, e.g. dataset/rock/*.wav")
    train_parser.add_argument("--model-out", default="artifacts/genre_model.joblib", help="Where to save the model bundle")
    train_parser.add_argument("--sample-rate", type=int, default=22050)
    train_parser.add_argument("--clip-duration", type=int, default=30)
    train_parser.add_argument("--test-size", type=float, default=0.2)

    predict_parser = subparsers.add_parser("predict", help="Predict the genre for one audio file.")
    predict_parser.add_argument("--model", required=True, help="Path to a saved model bundle")
    predict_parser.add_argument("--audio", required=True, help="Path to an audio file")

    inspect_parser = subparsers.add_parser("inspect", help="Show class counts in the dataset.")
    inspect_parser.add_argument("--data-dir", required=True, help="Dataset root")

    return parser


def run_train(args: argparse.Namespace) -> int:
    from music_genre_classifier.dataset import load_dataset
    from music_genre_classifier.modeling import save_model, train_model

    dataset = load_dataset(
        data_dir=args.data_dir,
        sample_rate=args.sample_rate,
        clip_duration=args.clip_duration,
    )
    model, metrics = train_model(
        features=dataset.features,
        labels=dataset.labels,
        class_names=dataset.class_names,
        test_size=args.test_size,
    )
    save_model(
        model=model,
        class_names=dataset.class_names,
        sample_rate=args.sample_rate,
        clip_duration=args.clip_duration,
        output_path=args.model_out,
    )

    print(f"Saved model to: {Path(args.model_out).resolve()}")
    print(f"Train samples: {metrics['train_samples']}")
    print(f"Test samples: {metrics['test_samples']}")
    print(f"Accuracy: {metrics['accuracy']:.4f}")
    print("Classification report:")
    print(metrics["report"])
    return 0


def run_predict(args: argparse.Namespace) -> int:
    from music_genre_classifier.audio_features import extract_features
    from music_genre_classifier.modeling import load_model

    bundle = load_model(args.model)
    feature_vector = extract_features(
        audio_path=args.audio,
        sample_rate=int(bundle["sample_rate"]),
        clip_duration=int(bundle["clip_duration"]),
    )
    model = bundle["model"]
    class_names = bundle["class_names"]

    predicted_index = int(model.predict(feature_vector.reshape(1, -1))[0])
    print(f"Predicted genre: {class_names[predicted_index]}")

    if hasattr(model, "predict_proba"):
        probabilities = model.predict_proba(feature_vector.reshape(1, -1))[0]
        ranked = sorted(
            zip(class_names, probabilities, strict=True),
            key=lambda item: item[1],
            reverse=True,
        )
        print("Top probabilities:")
        for label, probability in ranked[:3]:
            print(f"  {label}: {probability:.4f}")
    return 0


def run_inspect(args: argparse.Namespace) -> int:
    from music_genre_classifier.dataset import summarize_dataset

    summary = summarize_dataset(args.data_dir)
    total = sum(summary.values())

    if not summary:
        print("No supported audio files found.")
        return 1

    print(f"Total files: {total}")
    for genre, count in sorted(summary.items()):
        print(f"{genre}: {count}")
    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "train":
        return run_train(args)
    if args.command == "predict":
        return run_predict(args)
    if args.command == "inspect":
        return run_inspect(args)

    raise ValueError(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
