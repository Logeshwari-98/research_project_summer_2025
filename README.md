# Financial Data Lineage Explainer

A simple tool I built to explain how financial metrics are calculated. Ask questions like "How was Q2 revenue calculated?" and get step-by-step answers that show the SQL and logic behind each number.

## What it does

When I work with business data, I often see metric names like `revenue_q2_2023` or `gross_margin_percentage_by_product` but don't know exactly how they were computed. This tool helps by:

- Storing metric definitions and their calculation steps in one place
- Finding the most relevant steps when you ask a question
- Using a local AI model to write clear explanations in plain English
- Showing which metrics were used in the answer

Everything runs on your own computer - no data goes to the cloud.

## Quick start

1. Install Python and Ollama
2. Download a small AI model:
   ```bash
   ollama pull gemma:2b
   ```
3. Install the Python packages:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the app:
   ```bash
   python app.py
   ```
5. Open your browser to `http://127.0.0.1:7860`

## How to use

Type questions like:
- "How was Q2 revenue calculated?"
- "How is gross margin percentage by product computed?"
- "How was net income calculated?"

The tool will show you the steps, the SQL used, and any missing pieces it found.

## What's included

- `app.py` - The main web interface
- `utils.py` - Helper functions for searching and AI calls
- `data/lineage.json` - The metric definitions and SQL steps
- `evaluate.py` - Script to test the tool with sample questions
- `tests.json` - Sample questions and expected answers

## How it works

1. The tool stores metric definitions in a simple JSON file
2. When you ask a question, it searches for the most relevant calculation steps
3. It sends those steps to a local AI model (gemma:2b) to write an explanation
4. The AI model cites specific step IDs and points out anything missing

## Limitations

- The AI model sometimes gives slightly different answers for the same question
- It only knows about metrics that are written down in the lineage file
- If the lineage file is wrong, the explanations will also be wrong
- It works best with clear, specific questions

## Requirements

- Python 3.8+
- Ollama (for running local AI models)
- About 2GB free space (for the AI model)

## Files you need

The core files are:
- `app.py`
- `utils.py` 
- `requirements.txt`
- `data/lineage.json`
- `tests.json`
- `evaluate.py`

## Running tests

To see how well the tool works on sample questions:

```bash
python evaluate.py
```

This will create `eval_results.json` with scores and print a summary.

## Paper

This tool was built for a research project. The full paper explains the approach, tests, and results in detail.

## License

This is a student project. Feel free to use and modify for your own work.
