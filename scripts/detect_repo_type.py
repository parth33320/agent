"""
scripts/detect_repo_type.py

Given a repo name and its README content, calls Gemini API (gemini-1.5-flash)
with GEMINI_API_KEY to classify the software project into one category from:
[supply-chain, hr, finance, healthcare, e-commerce, devtools, education,
 real-estate, legal, marketing, social, gaming, other].

Caches classifications in docs/repo-classifications.json.
Falls back gracefully to "other" if GEMINI_API_KEY is not set or rate-limited.
"""

import os
import sys
import json
import argparse
from typing import Dict

VALID_CATEGORIES = [
    "supply-chain",
    "hr",
    "finance",
    "healthcare",
    "e-commerce",
    "devtools",
    "education",
    "real-estate",
    "legal",
    "marketing",
    "social",
    "gaming",
    "other",
]

CACHE_FILE = "docs/repo-classifications.json"


def load_cache() -> Dict[str, str]:
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load {CACHE_FILE}: {e}", file=sys.stderr)
    return {}


def save_cache(cache: Dict[str, str]):
    os.makedirs(os.path.dirname(CACHE_FILE) or ".", exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)


def classify_with_gemini(repo_name: str, readme_content: str) -> str:
    """Call Gemini API via google-generativeai SDK."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY not configured. Falling back to rule-based / 'other'.", file=sys.stderr)
        return rule_based_fallback(repo_name, readme_content)

    prompt = (
        f"Based on this repo name and README, classify this software project into one category from this list: "
        f"supply-chain, hr, finance, healthcare, e-commerce, devtools, education, real-estate, "
        f"legal, marketing, social, gaming, other. Return only the category word.\n\n"
        f"Repo Name: {repo_name}\n\n"
        f"README:\n{readme_content[:4000]}"
    )

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        raw_text = response.text.strip().lower()

        for cat in VALID_CATEGORIES:
            if cat in raw_text:
                return cat
        return "other"
    except Exception as e:
        print(f"Error calling Gemini API: {e}. Falling back to 'other'.", file=sys.stderr)
        return rule_based_fallback(repo_name, readme_content)


def rule_based_fallback(repo_name: str, readme_content: str) -> str:
    """Fallback heuristics when Gemini is unavailable or rate-limited."""
    text = f"{repo_name} {readme_content}".lower()
    if any(k in text for k in ["supply chain", "logistics", "procurement", "warehouse", "freight", "inventory"]):
        return "supply-chain"
    if any(k in text for k in ["human resources", "payroll", "recruiting", "employee", "onboarding"]):
        return "hr"
    if any(k in text for k in ["fintech", "banking", "payment", "crypto", "trading", "invoice", "finance"]):
        return "finance"
    if any(k in text for k in ["medical", "clinic", "health", "hospital", "patient", "triage", "biotech"]):
        return "healthcare"
    if any(k in text for k in ["ecommerce", "e-commerce", "storefront", "cart", "checkout", "shopify"]):
        return "e-commerce"
    if any(k in text for k in ["developer tool", "cli", "sdk", "compiler", "linter", "agent", "devtools", "skills"]):
        return "devtools"
    if any(k in text for k in ["education", "course", "curriculum", "learning", "student", "teacher"]):
        return "education"
    if any(k in text for k in ["real estate", "property", "tenant", "landlord", "mortgage", "realtor"]):
        return "real-estate"
    if any(k in text for k in ["legal", "contract", "compliance", "clause", "lawyer", "attorney"]):
        return "legal"
    if any(k in text for k in ["marketing", "campaign", "newsletter", "ads", "seo", "funnel"]):
        return "marketing"
    if any(k in text for k in ["social", "chat", "community", "forum", "messaging", "feed"]):
        return "social"
    if any(k in text for k in ["game", "gaming", "unity", "unreal", "shader", "physics"]):
        return "gaming"
    return "other"


def detect_repo_type(repo_name: str, readme_content: str, force_refresh: bool = False) -> str:
    cache = load_cache()
    if not force_refresh and repo_name in cache:
        return cache[repo_name]

    category = classify_with_gemini(repo_name, readme_content)
    if category not in VALID_CATEGORIES:
        category = "other"

    cache[repo_name] = category
    save_cache(cache)
    return category


def main():
    parser = argparse.ArgumentParser(description="Classify repo type using Gemini API")
    parser.add_argument("--repo-name", required=True, help="Name of repository")
    parser.add_argument("--readme-file", help="Path to README file")
    parser.add_argument("--readme-text", help="Direct README text string")
    parser.add_argument("--refresh", action="store_true", help="Force cache refresh")
    args = parser.parse_args()

    readme_content = ""
    if args.readme_file and os.path.exists(args.readme_file):
        with open(args.readme_file, "r", encoding="utf-8", errors="ignore") as f:
            readme_content = f.read()
    elif args.readme_text:
        readme_content = args.readme_text

    cat = detect_repo_type(args.repo_name, readme_content, force_refresh=args.refresh)
    print(cat)


if __name__ == "__main__":
    main()
