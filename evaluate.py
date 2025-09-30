# evaluate.py
import json
from utils import load_lineage, build_embeddings_and_index, retrieve_relevant_steps, build_prompt, call_llm_ollama, call_llm_openai
from sentence_transformers import SentenceTransformer
import numpy as np
from pathlib import Path
import os
from tqdm import tqdm

MODEL = SentenceTransformer("all-MiniLM-L6-v2")

def embed(text):
    return MODEL.encode([text])[0]

def cosine(a,b):
    return np.dot(a,b)/(np.linalg.norm(a)*np.linalg.norm(b)+1e-10)

def run_eval(tests_path="tests.json"):
    with open(tests_path,"r") as f:
        tests = json.load(f)
    lineage = load_lineage("data/lineage.json")
    client, collection = build_embeddings_and_index(lineage)
    results = []
    for t in tqdm(tests):
        q = t["query"]
        retrieved = retrieve_relevant_steps(collection, q, k=6)
        prompt, used_metrics = build_prompt(q, retrieved, lineage)
        res = call_llm_ollama(prompt, model=os.getenv("OLLAMA_MODEL","gemma:2b"))
        if res is None:
            res = call_llm_openai(prompt)
        if not res:
            res = "[NO_MODEL_AVAILABLE]"
        # score similarity between res and ground_truth
        gt = t["ground_truth"]
        score = cosine(embed(gt), embed(res))
        results.append({"query": q, "metric": t.get("metric"), "model_answer": res, "ground_truth": gt, "similarity": float(score)})
    outp = Path("eval_results.json")
    outp.write_text(json.dumps(results, indent=2))
    print("Wrote eval_results.json")
    # print summary
    for r in results:
        print(f"Query: {r['query']}\nSim: {r['similarity']:.3f}\nAnswer (truncated): {r['model_answer'][:300]}...\n---\n")

if __name__ == "__main__":
    run_eval()
