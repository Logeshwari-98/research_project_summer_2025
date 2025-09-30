# utils.py
import json
from sentence_transformers import SentenceTransformer
import numpy as np
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from pathlib import Path
import os
import subprocess
import requests

EMB_MODEL = "all-MiniLM-L6-v2"

os.environ["ANONYMIZED_TELEMETRY"] = "false"

def normalize_text(t: str) -> str:
    """Lowercase, replace underscores/hyphens with spaces, collapse extra whitespace."""
    if not isinstance(t, str):
        return ""
    return " ".join(t.lower().replace("_", " ").replace("-", " ").split())

def load_lineage(path="data/lineage.json"):
    with open(path, "r") as f:
        return json.load(f)

def build_embeddings_and_index(lineage):
    # Create a simple in-memory Chroma client (no Settings needed)
    client = chromadb.Client()

    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )

    # Create collection
    collection = client.create_collection(
        name="lineage_explanations",
        embedding_function=ef
    )

    documents, metadatas, ids = [], [], []
    for metric, info in lineage.items():
        for step in info.get("steps", []):
            doc = f"METRIC: {metric}\nSTEP_ID: {step.get('id','')}\nSQL: {step.get('sql','')}\nDESC: {step.get('description','')}"
            documents.append(doc)
            metadatas.append({"metric": metric, "step_id": step.get("id","")})
            ids.append(f"{metric}__{step.get('id','')}")
    collection.add(documents=documents, metadatas=metadatas, ids=ids)

    return client, collection


def retrieve_relevant_steps(collection, query, k=8):
    # normalize query to stabilize embeddings across small phrasing changes
    nq = normalize_text(query)
    results = collection.query(query_texts=[nq], n_results=k)
    # results: dict with ids, documents, metadatas
    docs = results["documents"][0]
    metadatas = results["metadatas"][0]
    ids = results["ids"][0]
    return [{"id": ids[i], "doc": docs[i], "meta": metadatas[i]} for i in range(len(docs))]

def build_prompt(user_query, retrieved_steps, lineage_lookup=None, top_k=5):
    header = f"User asked: {user_query}\n\nYou are an assistant that explains how financial metrics were calculated. " \
             "Use the available lineage steps below (SQL and short descriptions). Produce a clear step-by-step explanation in plain English. " \
             "If steps are missing, state what is missing. Cite which steps you used.\n\n"
    body = ""
    used_metrics = set()
    for s in retrieved_steps[:top_k]:
        body += f"---\n{ s['doc'] }\n"
        if s['meta'] and 'metric' in s['meta']:
            used_metrics.add(s['meta']['metric'])
    footer = "\n\nAnswer:"
    return header + body + footer, list(used_metrics)

# Ollama call wrapper: prefer Ollama CLI if present, otherwise fallback to OpenAI
def call_llm_ollama(prompt, model="gemma:2b", timeout=30):
    """Calls ollama CLI: `ollama run model` and stream prompt via stdin. Make sure ollama app is installed."""
    try:
        # Use the API endpoint instead of CLI for better control
        import requests
        print(f"Trying Ollama API with model: {model}")
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False
            },
            timeout=timeout
        )
        print(f"Ollama API response status: {response.status_code}")
        if response.status_code == 200:
            result = response.json().get("response", "")
            print(f"Ollama API response length: {len(result)}")
            return result
        else:
            print(f"Ollama API error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Ollama API exception: {e}")
        # Fallback to CLI method
        try:
            print(f"Trying Ollama CLI with model: {model}")
            p = subprocess.run(["ollama", "run", model], input=prompt.encode("utf-8"), capture_output=True, timeout=60)
            out = p.stdout.decode("utf-8")
            if out.strip():
                print(f"Ollama CLI success, output length: {len(out)}")
                return out
            else:
                stderr_out = p.stderr.decode("utf-8")
                print(f"Ollama CLI stderr: {stderr_out}")
                return stderr_out
        except FileNotFoundError:
            print("Ollama CLI not found")
            return None

def call_llm_openai(prompt, model="gpt-4o-mini", api_key_env="OPENAI_API_KEY"):
    key = os.getenv(api_key_env)
    if not key:
        return None
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    data = {"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": 1000}
    try:
        resp = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data, timeout=30)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except Exception:
        return None
