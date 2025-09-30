# app.py
import gradio as gr
from utils import load_lineage, build_embeddings_and_index, retrieve_relevant_steps, build_prompt, call_llm_ollama, call_llm_openai, normalize_text
import json
import os

LINEAGE_PATH = "data/lineage.json"

def start_app():
    lineage = load_lineage(LINEAGE_PATH)
    client, collection = build_embeddings_and_index(lineage)

    def answer_query(user_query):
        # retrieve (normalized) and lightly boost with explicit metric mentions
        q = normalize_text(user_query)
        retrieved = retrieve_relevant_steps(collection, q, k=8)
        # metric-name boosting: if a metric name appears in query, append all its steps
        boosted = []
        for metric, info in lineage.items():
            if normalize_text(metric) in q:
                for step in info.get("steps", []):
                    boosted.append({
                        "id": f"{metric}__{step.get('id','')}",
                        "doc": f"METRIC: {metric}\nSTEP_ID: {step.get('id','')}\nSQL: {step.get('sql','')}\nDESC: {step.get('description','')}",
                        "meta": {"metric": metric, "step_id": step.get("id","")}
                    })
        retrieved = (retrieved or []) + boosted
        prompt, used_metrics = build_prompt(user_query, retrieved, lineage)
        # try Ollama
        res = call_llm_ollama(prompt, model=os.getenv("OLLAMA_MODEL","gemma:2b"))
        source = "ollama"
        if res is None:
            # try OpenAI
            res = call_llm_openai(prompt)
            source = "openai" if res else "none"
        if not res:
            return "No LLM available. Install Ollama (https://ollama.ai) or set OPENAI_API_KEY.", ""
        # include the used metrics and the relevant steps (for traceability)
        # Show all retrieved metrics rather than only those used in the final prompt
        refs_metrics = sorted({s["meta"].get("metric") for s in retrieved if s.get("meta") and s["meta"].get("metric")})
        refs = "\n".join([f"- {m}" for m in refs_metrics]) if refs_metrics else "none"
        return res, refs

    with gr.Blocks() as demo:
        gr.Markdown("# Financial Data Lineage Explainer (Prototype)\nType a question like: \"How was gross_margin_percentage_by_product computed?\"")
        with gr.Row():
            inp = gr.Textbox(lines=1, placeholder="Ask about a metric (e.g., 'How was Q2 revenue calculated?')", label="Query")
            btn = gr.Button("Explain")
        out = gr.Textbox(lines=12, label="LLM Explanation")
        refs = gr.Textbox(lines=4, label="Referenced metrics (retrieved)")
        btn.click(answer_query, inputs=inp, outputs=[out, refs])
    demo.launch(server_name="0.0.0.0", share=False)

if __name__ == "__main__":
    start_app()
