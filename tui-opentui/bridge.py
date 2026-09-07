"""
RAGA Python Engine Bridge for OpenTUI
Executes query retrieval, reranking, and generation and prints JSON output.
"""
import sys
import os
import json
import time

# Add RAGA root directory to sys.path
raga_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if raga_root not in sys.path:
    sys.path.insert(0, raga_root)

from core.query_classifier import classify_query
from core.retriever import retrieve
from core.generator import generate_answer
from core.status_engine import get_status
import ollama
from config import OLLAMA_HOST


def list_models():
    try:
        client = ollama.Client(host=OLLAMA_HOST)
        resp = client.list()
        models_list = []
        raw_models = getattr(resp, "models", []) if hasattr(resp, "models") else resp.get("models", [])
        for m in raw_models:
            name = getattr(m, "model", "") if hasattr(m, "model") else m.get("model", "")
            size = getattr(m, "size", 0) if hasattr(m, "size") else m.get("size", 0)
            details = getattr(m, "details", None) if hasattr(m, "details") else m.get("details", {})
            param_size = getattr(details, "parameter_size", "") if hasattr(details, "parameter_size") else details.get("parameter_size", "")
            quant = getattr(details, "quantization_level", "") if hasattr(details, "quantization_level") else details.get("quantization_level", "")
            
            size_str = f"{size / (1024**3):.1f} GB" if size >= 1024**3 else f"{size / (1024**2):.0f} MB"
            models_list.append({
                "name": name,
                "size": size_str,
                "parameters": param_size,
                "quantization": quant,
                "is_embedding": "embed" in name.lower(),
            })
        return models_list
    except Exception as e:
        return [
            {"name": "qwen2.5:3b", "size": "1.9 GB", "parameters": "3.1B", "quantization": "Q4_K_M", "is_embedding": False},
            {"name": "qwen2.5-coder:7b", "size": "4.7 GB", "parameters": "7.6B", "quantization": "Q4_K_M", "is_embedding": False},
            {"name": "llama3.2:3b", "size": "2.0 GB", "parameters": "3.2B", "quantization": "Q4_K_M", "is_embedding": False},
        ]


def handle_query(query: str, model: str | None = None):
    t0 = time.time()
    try:
        qtype = classify_query(query)

        if qtype in ("filesystem", "location"):
            from core.engine import ask
            res = ask(query)
            sources_data = []
            for i, p in enumerate(res.get("sources", [])[:5], 1):
                sources_data.append({
                    "id": i,
                    "path": p,
                    "score": 0.95,
                    "chunkText": f"File referenced: {p}"
                })
            return {
                "qtype": qtype,
                "text": res.get("text", ""),
                "sources": sources_data,
                "elapsed": round(time.time() - t0, 2),
            }

        # Content query
        chunks = retrieve(query, top_k=7)
        answer = generate_answer(query, chunks, model=model) if chunks else "No relevant information found in indexed files."

        sources_data = []
        seen = set()
        idx = 1
        for c in chunks:
            p = c.get("file_path", "")
            if p and p not in seen:
                seen.add(p)
                sources_data.append({
                    "id": idx,
                    "path": p,
                    "score": float(c.get("score", 0.85)),
                    "chunkText": c.get("chunk_text", "")
                })
                idx += 1
                if idx > 5:
                    break

        return {
            "qtype": qtype,
            "text": answer,
            "sources": sources_data,
            "elapsed": round(time.time() - t0, 2),
        }
    except Exception as e:
        return {
            "qtype": "content",
            "text": f"Error running query: {str(e)}",
            "sources": [],
            "elapsed": round(time.time() - t0, 2),
        }


if __name__ == "__main__":
    try:
        if len(sys.argv) < 2:
            print(json.dumps({"error": "No query provided"}))
            sys.exit(1)

        cmd = sys.argv[1]
        if cmd == "--status":
            s = get_status()
            print(json.dumps(s))
        elif cmd == "--models":
            m = list_models()
            print(json.dumps(m))
        elif cmd == "--query":
            # python bridge.py --query "prompt" --model "qwen2.5:3b"
            query_text = sys.argv[2] if len(sys.argv) > 2 else ""
            model_arg = None
            if "--model" in sys.argv:
                m_idx = sys.argv.index("--model")
                if m_idx + 1 < len(sys.argv):
                    model_arg = sys.argv[m_idx + 1]
            out = handle_query(query_text, model=model_arg)
            print(json.dumps(out))
        else:
            out = handle_query(cmd)
            print(json.dumps(out))
    except Exception as e:
        print(json.dumps({
            "qtype": "content",
            "text": f"Error executing query: {str(e)}",
            "sources": [],
            "elapsed": 0,
        }))

