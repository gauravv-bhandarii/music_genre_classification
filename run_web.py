import uvicorn

if __name__ == "__main__":
    print("Starting Music Genre Classifier Web API...")
    uvicorn.run("music_genre_classifier.web:app", host="127.0.0.1", port=8000, reload=True)
