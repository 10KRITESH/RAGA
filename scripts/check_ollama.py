"""Confirm Ollama is reachable and required models are pulled."""
from typer import _completion_classes
import sys
import ollama
from config import EMBEDDING_MODEL, GENERATION_MODEL_DEFAULT, GENERATION_MODEL_CODE, OLLAMA_HOST


def main():
    client = ollama.Client(host=OLLAMA_HOST)

    try:
        response = client.list()
    except Exception as e:
        print(f"Could not reach Ollama at {OLLAMA_HOST}: {e}")
        sys.exit(1)

    installed = {m["model"] for m in response.get("models", [])}
    required = {EMBEDDING_MODEL, GENERATION_MODEL_DEFAULT, GENERATION_MODEL_CODE}

    print(f"Ollama reachable at {OLLAMA_HOST}")
    print(f"Installed models: {len(installed)}")

    missing = [m for m in required if not any(m in i for i in installed)]
    if missing:
        print(f"Missing models: {', '.join(missing)}")
        print("Run: " + " && ".join(f"ollama pull {m}" for m in missing))
        sys.exit(1)

    print("All required models present.")


if __name__ == "__main__":
    main()