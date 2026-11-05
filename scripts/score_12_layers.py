"""
scripts/score_12_layers.py

Scans the repository codebase and generates docs/12-layers-status.md
scoring all 12 Miriam Miradi layers as PRESENT/PARTIAL/MISSING
with one-line evidence for each.
"""

import os
import re
import datetime
from typing import Dict, List, Tuple

# Layer definitions and search regex patterns
LAYER_PATTERNS = {
    1: {
        "name": "Business Understanding",
        "patterns": [
            r"decision_scope", r"business_rules", r"policy_engine",
            r"success_criteria", r"supported_decision", r"business_understanding"
        ],
        "keywords": ["decision scope", "business rules", "success criteria"]
    },
    2: {
        "name": "Data Understanding",
        "patterns": [
            r"data_completeness", r"check_missing_fields", r"field_availability",
            r"data_validation", r"schema_validation", r"missing_fields"
        ],
        "keywords": ["completeness check", "missing fields", "schema validation"]
    },
    3: {
        "name": "Knowledge Engineering",
        "patterns": [
            r"vector_store", r"embeddings", r"knowledge_graph",
            r"document_ingestion", r"retrieval_tool", r"chunking"
        ],
        "keywords": ["vector store", "chunking", "knowledge graph", "embeddings"]
    },
    4: {
        "name": "Context Engineering",
        "patterns": [
            r"context_bundle", r"context_builder", r"assemble_context",
            r"differentiated_context", r"filter_context", r"context_engineering"
        ],
        "keywords": ["differentiated context", "context bundle", "context builder"]
    },
    5: {
        "name": "Model Engineering",
        "patterns": [
            r"model_profile", r"model_tier", r"temperature\s*=",
            r"system_prompt", r"model_selector", r"gemini-1\.5", r"gpt-4"
        ],
        "keywords": ["model profile", "temperature=", "task specific model", "system_prompt"]
    },
    6: {
        "name": "Semantic Engineering",
        "patterns": [
            r"resolve_concept", r"semantic_resolution", r"domain_ontology",
            r"abbreviation_map", r"synonym_mapper", r"semantic_engineering"
        ],
        "keywords": ["resolve concept", "synonym mapper", "abbreviation expansion", "domain ontology"]
    },
    7: {
        "name": "Agent Engineering",
        "patterns": [
            r"StateGraph", r"LangGraph", r"add_node", r"add_edge",
            r"agent_executor", r"Workflow", r"agent_engineering"
        ],
        "keywords": ["LangGraph", "StateGraph", "add_node", "agent executor"]
    },
    8: {
        "name": "Loop Engineering",
        "patterns": [
            r"verification_loop", r"retry_count", r"human_in_the_loop",
            r"human_review", r"escalat", r"constraint_check", r"loop_engineering"
        ],
        "keywords": ["verification loop", "human in the loop", "constraint check", "human review"]
    },
    9: {
        "name": "Evaluation Engineering",
        "patterns": [
            r"test_eval", r"golden_dataset", r"evaluation_runner",
            r"benchmark", r"run_eval", r"pass_rate", r"evaluation_engineering"
        ],
        "keywords": ["evaluation runner", "golden dataset", "benchmark", "pass rate"]
    },
    10: {
        "name": "Harness Engineering",
        "patterns": [
            r"trace_run", r"execution_trace", r"run_metadata",
            r"replay_run", r"telemetry", r"harness_engineering"
        ],
        "keywords": ["trace run", "replay run", "run metadata", "execution trace"]
    },
    11: {
        "name": "Infrastructure / Production Engineering",
        "patterns": [
            r"timeout\s*=", r"retry_strategy", r"exponential_backoff",
            r"fallback", r"circuit_breaker", r"max_retries", r"infrastructure_engineering"
        ],
        "keywords": ["timeout=", "exponential backoff", "fallback", "circuit breaker"]
    },
    12: {
        "name": "Continual Learning",
        "patterns": [
            r"continual_learning", r"feedback_loop", r"failure_pattern",
            r"cluster_errors", r"candidate_improvement"
        ],
        "keywords": ["continual learning", "feedback loop", "failure pattern", "candidate improvement"]
    }
}

EXCLUDED_DIRS = {".git", ".github", "node_modules", "dist", "build", "__pycache__", ".pytest_cache", "venv", ".venv"}
EXCLUDED_FILES = {"12-layers-status.md", "all-repos-layer-scores.md", "score_12_layers.py"}


def scan_codebase() -> Dict[int, List[Tuple[str, int, str]]]:
    """
    Scan files for layer patterns.
    Returns mapping: layer_num -> list of (filepath, line_number, matched_line_text)
    """
    matches: Dict[int, List[Tuple[str, int, str]]] = {i: [] for i in range(1, 13)}

    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
        for file in files:
            if file in EXCLUDED_FILES:
                continue
            # Scan text files only
            if not file.endswith((".py", ".ts", ".js", ".md", ".json", ".yaml", ".yml", ".sh", ".toml")):
                continue

            rel_path = os.path.relpath(os.path.join(root, file), ".").replace("\\", "/")
            try:
                with open(rel_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line_idx, line in enumerate(f, start=1):
                        for layer_num, config in LAYER_PATTERNS.items():
                            for pat in config["patterns"]:
                                if re.search(pat, line, re.IGNORECASE):
                                    matches[layer_num].append((rel_path, line_idx, line.strip()))
                                    break
            except Exception as e:
                print(f"Skipping {rel_path} due to read error: {e}")

    return matches


def evaluate_layer_status(matches: List[Tuple[str, int, str]]) -> Tuple[str, str]:
    """
    Determine PRESENT, PARTIAL, or MISSING status and format a single-line evidence string.
    Criteria:
      - If found in active implementation code (.py, .ts, .js), status = PRESENT
      - If found only in documentation (.md, .json), status = PARTIAL
      - If not found or only self-referential in layer documentation (e.g. only in docs/layers.md), status = PARTIAL / MISSING
    """
    if not matches:
        return "MISSING", "No implementation or documentation patterns found in codebase."

    # Filter out pure docs definition matches if we want to differentiate code vs doc
    code_matches = [m for m in matches if not m[0].startswith("docs/layers.md") and not m[0].startswith("docs/checklist.md")]

    if not code_matches:
        # Only found in layers/checklist doc
        first = matches[0]
        return "PARTIAL", f"Documented in `{first[0]}:{first[1]}`: {first[2][:80]}"

    py_or_src = [m for m in code_matches if m[0].endswith((".py", ".ts", ".js"))]
    if py_or_src:
        first = py_or_src[0]
        return "PRESENT", f"Implemented in `{first[0]}:{first[1]}`: {first[2][:80]}"
    else:
        first = code_matches[0]
        return "PARTIAL", f"Configured or documented in `{first[0]}:{first[1]}`: {first[2][:80]}"


def generate_status_markdown(results: Dict[int, Tuple[str, str]]) -> str:
    today = datetime.date.today().strftime("%Y-%m-%d")
    lines = [
        f"# 12-Layer Production Agent Status ({today})",
        "",
        "Evaluation of repository alignment with Miriam Miradi's 12-layer production agent architecture.",
        "",
        "| Layer # | Layer Name | Status | Evidence |",
        "|---|---|---|---|",
    ]

    for layer_num in range(1, 13):
        name = LAYER_PATTERNS[layer_num]["name"]
        status, evidence = results[layer_num]
        status_badge = f"**{status}**"
        clean_evidence = evidence.replace("|", "\\|")
        lines.append(f"| {layer_num} | {name} | {status_badge} | {clean_evidence} |")

    lines.append("")
    summary_counts = {
        "PRESENT": sum(1 for s, _ in results.values() if s == "PRESENT"),
        "PARTIAL": sum(1 for s, _ in results.values() if s == "PARTIAL"),
        "MISSING": sum(1 for s, _ in results.values() if s == "MISSING"),
    }
    lines.append("### Summary")
    lines.append(f"- **PRESENT:** {summary_counts['PRESENT']} / 12")
    lines.append(f"- **PARTIAL:** {summary_counts['PARTIAL']} / 12")
    lines.append(f"- **MISSING:** {summary_counts['MISSING']} / 12")
    lines.append("")

    return "\n".join(lines)


def main():
    print("Scanning codebase for 12-layer patterns...")
    raw_matches = scan_codebase()
    results: Dict[int, Tuple[str, str]] = {}

    for layer_num in range(1, 13):
        status, evidence = evaluate_layer_status(raw_matches[layer_num])
        results[layer_num] = (status, evidence)
        print(f"Layer {layer_num} ({LAYER_PATTERNS[layer_num]['name']}): {status} - {evidence}")

    os.makedirs("docs", exist_ok=True)
    out_path = "docs/12-layers-status.md"
    content = generate_status_markdown(results)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Status report written to {out_path}")


if __name__ == "__main__":
    main()
