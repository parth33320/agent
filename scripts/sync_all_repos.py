"""
scripts/sync_all_repos.py

Multi-repo automation for parth33320:
1. Outbound — Push Miriam Miradi docs (docs/layers.md, docs/checklist.md, AGENTS.md, CLAUDE.md, GLOSSARY.md)
   to all parth33320 repos (skipping 'agent'). Opens/updates PR titled:
   'Agent docs sync: layers, checklist, skills updated' on branch 'sync-agent-docs-YYYY-MM-DD'.
2. Inbound — Check for docs/12-layers-status.md in each repo, aggregate status into
   docs/all-repos-layer-scores.md (| repo-name | date | Layer scores summary |), and commit to agent repo main.
3. Competitive Innovation Proposals — Detect repo category via detect_repo_type.py, look up competitor
   URLs in scripts/competitive_map.json, scrape release notes (with fallback), and use Gemini API (gemini-1.5-flash)
   to create docs/improvement_proposals/YYYY-MM-DD.md with 3-5 concrete proposals. Open/update PR on target repo:
   Branch 'agent-improvement-YYYY-MM-DD', Title '🤖 Agent Improvement Proposal: [category] features from frontier apps'.
"""

import os
import re
import sys
import json
import base64
import datetime
import argparse
import requests
from typing import Dict, List, Optional, Tuple, Any

from detect_repo_type import detect_repo_type, VALID_CATEGORIES

GITHUB_API_BASE = "https://api.github.com"
OWNER = "parth33320"
SELF_REPO = "agent"

DOC_FILES_TO_SYNC = [
    "docs/layers.md",
    "docs/checklist.md",
    "AGENTS.md",
    "CLAUDE.md",
    "GLOSSARY.md"
]

CATEGORY_KEYWORDS = {
    "supply-chain": ["supply chain", "logistics", "procurement", "inventory", "warehouse", "freight", "carrier", "tracking"],
    "hr": ["recruitment", "payroll", "performance", "onboarding", "benefits", "employee", "workforce"],
    "finance": ["payment", "banking", "treasury", "invoice", "compliance", "fraud", "ledger", "accounting"],
    "healthcare": ["clinical", "patient", "ehr", "hipaa", "diagnosis", "telehealth", "prescription"],
    "e-commerce": ["checkout", "cart", "catalog", "merchandising", "storefront", "order management", "discounts"],
    "devtools": ["ci/cd", "deployment", "compiler", "runtime", "observability", "debugging", "sdk", "api"],
    "education": ["course", "curriculum", "assessment", "grading", "lms", "student", "assignment"],
    "real-estate": ["listing", "lease", "tenant", "property", "brokerage", "mortgage", "zoning"],
    "legal": ["contract", "e-signature", "litigation", "compliance", "clauses", "nda", "matter"],
    "marketing": ["campaign", "attribution", "lead", "segmentation", "email", "crm", "conversion"],
    "social": ["messaging", "moderation", "feed", "community", "reactions", "notifications", "threads"],
    "gaming": ["rendering", "physics", "multiplayer", "matchmaking", "gameplay", "assets", "npc"],
    "other": ["automation", "optimization", "intelligence", "workflow", "integration"]
}


def get_auth_headers() -> Dict[str, str]:
    token = os.environ.get("AGENT_REPO_TOKEN") or os.environ.get("GITHUB_TOKEN")
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "sync-all-repos-agent"
    }
    if token:
        headers["Authorization"] = f"token {token}"
    return headers


def list_user_repos() -> List[Dict[str, Any]]:
    """List all public and accessible repos for OWNER."""
    url = f"{GITHUB_API_BASE}/users/{OWNER}/repos?per_page=100"
    headers = get_auth_headers()
    try:
        resp = requests.get(url, headers=headers, timeout=20)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"Error listing repos for {OWNER}: {e}", file=sys.stderr)
        return []


def get_repo_file(repo_name: str, path: str, ref: str = "main") -> Optional[Tuple[str, str]]:
    """Fetch file content (decoded utf-8) and sha from a remote repo."""
    url = f"{GITHUB_API_BASE}/repos/{OWNER}/{repo_name}/contents/{path}?ref={ref}"
    headers = get_auth_headers()
    resp = requests.get(url, headers=headers, timeout=15)
    if resp.status_code == 200:
        data = resp.json()
        raw_b64 = data.get("content", "")
        sha = data.get("sha", "")
        content = base64.b64decode(raw_b64).decode("utf-8", errors="ignore")
        return content, sha
    return None


def get_local_file_content(path: str) -> Optional[str]:
    """Read local file content from current agent repository."""
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return None


def get_default_branch(repo_name: str) -> str:
    url = f"{GITHUB_API_BASE}/repos/{OWNER}/{repo_name}"
    headers = get_auth_headers()
    resp = requests.get(url, headers=headers, timeout=15)
    if resp.status_code == 200:
        return resp.json().get("default_branch", "main")
    return "main"


def get_branch_ref(repo_name: str, branch: str) -> Optional[str]:
    """Get the commit SHA that a branch points to."""
    url = f"{GITHUB_API_BASE}/repos/{OWNER}/{repo_name}/git/ref/heads/{branch}"
    headers = get_auth_headers()
    resp = requests.get(url, headers=headers, timeout=15)
    if resp.status_code == 200:
        return resp.json().get("object", {}).get("sha")
    return None


def create_or_update_branch(repo_name: str, branch_name: str, base_branch: str) -> bool:
    """Ensure branch exists and is updated to base branch commit."""
    headers = get_auth_headers()
    base_sha = get_branch_ref(repo_name, base_branch)
    if not base_sha:
        print(f"[{repo_name}] Could not find base branch {base_branch}", file=sys.stderr)
        return False

    existing_sha = get_branch_ref(repo_name, branch_name)
    if not existing_sha:
        create_url = f"{GITHUB_API_BASE}/repos/{OWNER}/{repo_name}/git/refs"
        payload = {"ref": f"refs/heads/{branch_name}", "sha": base_sha}
        resp = requests.post(create_url, headers=headers, json=payload, timeout=15)
        if resp.status_code in [201, 200]:
            return True
        print(f"[{repo_name}] Failed creating branch {branch_name}: {resp.text}", file=sys.stderr)
        return False
    else:
        # Update branch to base_sha
        update_url = f"{GITHUB_API_BASE}/repos/{OWNER}/{repo_name}/git/refs/heads/{branch_name}"
        payload = {"sha": base_sha, "force": True}
        resp = requests.patch(update_url, headers=headers, json=payload, timeout=15)
        return resp.status_code in [200, 201]


def put_file_content(repo_name: str, path: str, content: str, commit_message: str, branch: str) -> bool:
    """Create or update a file in the remote repo on specified branch."""
    headers = get_auth_headers()
    url = f"{GITHUB_API_BASE}/repos/{OWNER}/{repo_name}/contents/{path}"

    # Check if file exists on this branch to get sha
    existing = get_repo_file(repo_name, path, ref=branch)
    payload = {
        "message": commit_message,
        "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
        "branch": branch
    }
    if existing:
        payload["sha"] = existing[1]

    resp = requests.put(url, headers=headers, json=payload, timeout=15)
    return resp.status_code in [200, 201]


def open_or_update_pull_request(repo_name: str, head_branch: str, base_branch: str, title: str, body: str) -> bool:
    """Open a PR or update body/title if PR already exists."""
    headers = get_auth_headers()
    prs_url = f"{GITHUB_API_BASE}/repos/{OWNER}/{repo_name}/pulls"

    # Check for existing PR
    resp = requests.get(f"{prs_url}?head={OWNER}:{head_branch}&base={base_branch}&state=open", headers=headers, timeout=15)
    if resp.status_code == 200 and resp.json():
        pr_number = resp.json()[0]["number"]
        update_url = f"{prs_url}/{pr_number}"
        patch_resp = requests.patch(update_url, headers=headers, json={"title": title, "body": body}, timeout=15)
        print(f"[{repo_name}] Updated existing PR #{pr_number}")
        return patch_resp.status_code == 200

    # Create new PR
    payload = {
        "title": title,
        "head": head_branch,
        "base": base_branch,
        "body": body
    }
    post_resp = requests.post(prs_url, headers=headers, json=payload, timeout=15)
    if post_resp.status_code == 201:
        print(f"[{repo_name}] Opened new PR: {post_resp.json().get('html_url')}")
        return True
    print(f"[{repo_name}] Failed to open PR: {post_resp.text}", file=sys.stderr)
    return False


# ---------------------------------------------------------
# Outbound: Push best practices docs to all repos
# ---------------------------------------------------------
def process_outbound_repo_sync(repo_name: str, today: str) -> None:
    """Sync docs/layers.md, docs/checklist.md, AGENTS.md, CLAUDE.md, GLOSSARY.md to repo."""
    default_branch = get_default_branch(repo_name)

    layers_file = get_repo_file(repo_name, "docs/layers.md", ref=default_branch)
    files_to_update = {}

    for doc_path in DOC_FILES_TO_SYNC:
        local_content = get_local_file_content(doc_path)
        if not local_content:
            continue
        remote_data = get_repo_file(repo_name, doc_path, ref=default_branch)
        if not remote_data or remote_data[0] != local_content:
            files_to_update[doc_path] = local_content

    if not files_to_update:
        print(f"[{repo_name}] All docs up to date.")
        return

    branch_name = f"sync-agent-docs-{today}"
    pr_title = "Agent docs sync: layers, checklist, skills updated"
    is_initial_add = (layers_file is None)

    body_intro = "Initial addition of 12-layer production agent architecture and skills." if is_initial_add else "Update 12-layer production agent architecture and skills to latest versions."
    pr_body_lines = [
        f"## {pr_title}",
        "",
        body_intro,
        "",
        "### Synchronized Files:",
    ]
    for p in files_to_update.keys():
        pr_body_lines.append(f"- `{p}`")
    pr_body_lines.extend([
        "",
        "---",
        "*Automated synchronization via parth33320/agent.*"
    ])
    pr_body = "\n".join(pr_body_lines)

    # Save local pr_body.md for logging/debugging
    with open("pr_body.md", "w", encoding="utf-8") as f:
        f.write(pr_body)

    if not create_or_update_branch(repo_name, branch_name, default_branch):
        print(f"[{repo_name}] Failed branch setup for outbound sync.", file=sys.stderr)
        return

    for doc_path, content in files_to_update.items():
        commit_msg = f"chore: sync {doc_path} from agent repo"
        put_file_content(repo_name, doc_path, content, commit_msg, branch_name)

    open_or_update_pull_request(repo_name, branch_name, default_branch, pr_title, pr_body)


# ---------------------------------------------------------
# Inbound: Aggregate 12-layer scores from repos
# ---------------------------------------------------------
def process_inbound_layer_scores(repos: List[Dict[str, Any]], today: str) -> None:
    """Fetch docs/12-layers-status.md from each repo and update docs/all-repos-layer-scores.md."""
    status_entries = []

    for repo in repos:
        repo_name = repo["name"]
        if repo_name == SELF_REPO:
            continue
        default_branch = repo.get("default_branch", "main")
        status_file = get_repo_file(repo_name, "docs/12-layers-status.md", ref=default_branch)
        if status_file:
            content = status_file[0]
            # Extract summary counts or line
            present = len(re.findall(r"\*\*PRESENT\*\*", content))
            partial = len(re.findall(r"\*\*PARTIAL\*\*", content))
            missing = len(re.findall(r"\*\*MISSING\*\*", content))
            summary = f"PRESENT: {present}/12, PARTIAL: {partial}/12, MISSING: {missing}/12"
            status_entries.append((repo_name, today, summary))

    if not status_entries:
        print("No remote repositories with docs/12-layers-status.md found.")
        return

    all_scores_path = "docs/all-repos-layer-scores.md"
    existing_content = get_local_file_content(all_scores_path)
    if not existing_content:
        header = "# Multi-Repository 12-Layer Production Status Report\n\n| Repo Name | Date | Layer Scores Summary |\n|---|---|---|\n"
    else:
        header = existing_content.strip() + "\n"

    new_lines = []
    for repo_name, date_str, summary in status_entries:
        line = f"| {repo_name} | {date_str} | {summary} |"
        if line not in header:
            new_lines.append(line)

    if new_lines:
        updated_content = header + "\n".join(new_lines) + "\n"
        with open(all_scores_path, "w", encoding="utf-8") as f:
            f.write(updated_content)
        print(f"Updated {all_scores_path} with {len(new_lines)} entries.")


# ---------------------------------------------------------
# Competitive Intelligence & Feature Proposals
# ---------------------------------------------------------
def load_competitive_map() -> Dict[str, List[str]]:
    path = "scripts/competitive_map.json"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def scrape_competitor_site(domain: str, category: str) -> List[str]:
    """Scrape competitor site and extract snippets matching category keywords."""
    url = f"https://{domain}" if not domain.startswith("http") else domain
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    snippets = []
    keywords = CATEGORY_KEYWORDS.get(category, CATEGORY_KEYWORDS["other"])

    try:
        resp = requests.get(url, headers=headers, timeout=5)
        text = resp.text
        clean_text = re.sub(r"<[^>]+>", " ", text)
        sentences = re.split(r"[.\n]+", clean_text)
        for s in sentences:
            cleaned = " ".join(s.split())
            if len(cleaned) > 25 and any(kw in cleaned.lower() for kw in keywords):
                snippets.append(cleaned)
                if len(snippets) >= 6:
                    break
    except Exception as e:
        print(f"Scraping {domain} failed: {e}", file=sys.stderr)

    return snippets


def generate_improvement_proposal(repo_name: str, category: str, readme: str, competitor_snippets: Dict[str, List[str]], today: str) -> str:
    """Generate Markdown proposal with 3-5 concrete feature proposals."""
    api_key = os.environ.get("GEMINI_API_KEY")

    competitor_section = []
    for comp, snips in competitor_snippets.items():
        if snips:
            competitor_section.append(f"### {comp} Intel:\n" + "\n".join(f"- {s}" for s in snips))

    competitor_text = "\n\n".join(competitor_section) if competitor_section else "No live competitor telemetry available; synthesizing from category benchmarks."

    prompt = f"""You are a Principal Software Architect evaluating competitive intelligence for software repository '{repo_name}' in category '{category}'.

Repo README:
{readme[:3000]}

Competitor Release Intel from Frontier Competitors in {category}:
{competitor_text}

Generate a comprehensive proposal with 3 to 5 high-value, production-grade features matching this repository's tech stack and category ({category}) inspired by frontier apps.
For each proposal include:
1. Feature Name & Frontier Inspiration
2. Business Value & User Impact
3. Architecture & Technical Integration Plan
4. Draft Interface or Implementation Specification

Format as a clean, polished Markdown document starting with:
# 🤖 Agent Improvement Proposal: {category.title()} Features from Frontier Apps ({today})
"""

    if not api_key:
        print(f"[{repo_name}] GEMINI_API_KEY not configured. Generating standard proposal.", file=sys.stderr)
        return f"""# 🤖 Agent Improvement Proposal: {category.title()} Features from Frontier Apps ({today})

## Executive Summary
This proposal provides targeted architectural and feature enhancements for **{repo_name}** ({category}), synthesizing capabilities from leading industry competitors and 12-layer production agent standards.

---

## Proposed Features

### 1. Automated Category Telemetry & Telemetry Guardrails
- **Inspiration:** Frontier platforms in `{category}`
- **Business Value:** Prevents unmonitored operational failures and introduces deterministic runtime verification.
- **Architecture Integration:** Introduce a verification loop node validating inputs and responses before state commitment.
- **Specification:** Add schema validators and exception routing.

### 2. Task-Specific Model Profiles & Adaptive Routing
- **Inspiration:** Modular multi-agent architectures
- **Business Value:** Minimizes inference cost while boosting accuracy on complex domain tasks.
- **Architecture Integration:** Differentiate model roles (fast classification vs deep reasoning).

### 3. Continual Learning & Feedback Capture
- **Inspiration:** Enterprise workflow intelligence
- **Business Value:** Automatically clusters repeated human overrides to recommend candidate prompt or policy updates.
- **Specification:** Capture operator corrections to a governed feedback queue.

---

## Action Items
- [ ] Review proposed schema extensions and architectural modifications.
- [ ] Schedule pilot rollout for automated validation guards.
"""

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        resp = model.generate_content(prompt)
        return resp.text
    except Exception as e:
        print(f"Error calling Gemini: {e}. Generating fallback proposal.", file=sys.stderr)
        return f"# 🤖 Agent Improvement Proposal: {category.title()} Features ({today})\n\nFallback generated due to API rate-limit/network error."


def process_competitive_proposal(repo_name: str, today: str) -> None:
    default_branch = get_default_branch(repo_name)
    readme_data = get_repo_file(repo_name, "README.md", ref=default_branch)
    readme_content = readme_data[0] if readme_data else f"# {repo_name}"

    category = detect_repo_type(repo_name, readme_content)
    comp_map = load_competitive_map()
    competitors = comp_map.get(category, [])

    scraped_data = {}
    for comp in competitors:
        snips = scrape_competitor_site(comp, category)
        if snips:
            scraped_data[comp] = snips

    proposal_md = generate_improvement_proposal(repo_name, category, readme_content, scraped_data, today)

    branch_name = f"agent-improvement-{today}"
    proposal_path = f"docs/improvement_proposals/{today}.md"
    pr_title = f"🤖 Agent Improvement Proposal: {category} features from frontier apps"
    pr_body = (
        f"## {pr_title}\n\n"
        f"Automated architectural review for `{repo_name}` based on category intelligence (`{category}`).\n\n"
        f"Added proposal plan at `{proposal_path}`.\n\n"
        "---\n*Generated by parth33320/agent.*"
    )

    with open("pr_body.md", "w", encoding="utf-8") as f:
        f.write(pr_body)

    if not create_or_update_branch(repo_name, branch_name, default_branch):
        print(f"[{repo_name}] Failed to create branch {branch_name}", file=sys.stderr)
        return

    put_file_content(
        repo_name,
        proposal_path,
        proposal_md,
        f"docs: add agent improvement proposal for {today}",
        branch_name
    )

    open_or_update_pull_request(repo_name, branch_name, default_branch, pr_title, pr_body)


# ---------------------------------------------------------
# Main Execution Entrypoint
# ---------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Multi-repo synchronizer for 12-layer architecture")
    parser.add_argument("--repo", help="Target single repository for testing/selective execution")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of repositories to process")
    args = parser.parse_args()

    today = datetime.date.today().strftime("%Y-%m-%d")
    print(f"Starting multi-repo synchronization for {OWNER} on {today}...")

    repos = list_user_repos()
    print(f"Found {len(repos)} repositories under {OWNER}.")

    if args.repo:
        repos = [r for r in repos if r["name"] == args.repo]
        print(f"Filtered to target repository: {args.repo}")
    elif args.limit:
        repos = repos[:args.limit]
        print(f"Limited run to first {args.limit} repositories.")

    # 1. Process Outbound Doc Sync & 3. Competitive Proposals per repo
    for repo in repos:
        repo_name = repo["name"]
        if repo_name == SELF_REPO:
            continue
        print(f"\n--- Processing repository: {repo_name} ---")
        try:
            process_outbound_repo_sync(repo_name, today)
        except Exception as e:
            print(f"[{repo_name}] Error in outbound sync: {e}", file=sys.stderr)

        try:
            process_competitive_proposal(repo_name, today)
        except Exception as e:
            print(f"[{repo_name}] Error in competitive proposal: {e}", file=sys.stderr)

    # 2. Process Inbound Layer Scores Aggregation
    print("\n--- Aggregating Inbound 12-Layer Scores ---")
    try:
        process_inbound_layer_scores(repos, today)
    except Exception as e:
        print(f"Error in inbound layer score aggregation: {e}", file=sys.stderr)

    print("\nMulti-repo synchronization complete.")


if __name__ == "__main__":
    main()
