"""
scripts/sync_mattpocock.py

Fetches upstream files from mattpocock/skills main branch without authentication:
- AGENTS.md, CLAUDE.md, GLOSSARY.md
- All skills/**/SKILL.md discovered via GitHub Tree API

Compares them with local files in parth33320/agent:
- Updates or creates modified/new files locally
- Leaves local files in place if deleted upstream, adding a warning note in PR body
- Outputs pr_body.md and writes GitHub Action step outputs
"""

import os
import sys
import requests
from typing import Dict, List, Set, Tuple

UPSTREAM_REPO = "mattpocock/skills"
TREE_API_URL = f"https://api.github.com/repos/{UPSTREAM_REPO}/git/trees/main?recursive=1"
RAW_BASE_URL = f"https://raw.githubusercontent.com/{UPSTREAM_REPO}/main"

STATIC_TARGET_FILES = ["AGENTS.md", "CLAUDE.md", "GLOSSARY.md"]


def get_upstream_target_paths() -> List[str]:
    """Retrieve list of targeted paths from upstream git tree."""
    headers = {"User-Agent": "sync-mattpocock-bot"}
    resp = requests.get(TREE_API_URL, headers=headers, timeout=30)
    resp.raise_for_status()
    tree_data = resp.json().get("tree", [])

    skill_paths = [
        item["path"]
        for item in tree_data
        if item.get("type") == "blob"
        and item.get("path", "").startswith("skills/")
        and item.get("path", "").endswith("SKILL.md")
    ]

    # Combine static files + discovered skill paths
    all_targets = sorted(list(set(STATIC_TARGET_FILES + skill_paths)))
    return all_targets


def fetch_raw_content(path: str) -> str:
    """Fetch raw file content from upstream repo using unauthenticated GET."""
    url = f"{RAW_BASE_URL}/{path}"
    headers = {"User-Agent": "sync-mattpocock-bot"}
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.text


def find_local_tracked_skill_files() -> List[str]:
    """Find all local files that match our target patterns."""
    local_files = []
    for f in STATIC_TARGET_FILES:
        if os.path.exists(f):
            local_files.append(f)

    if os.path.exists("skills"):
        for root, _, files in os.walk("skills"):
            for file in files:
                if file == "SKILL.md":
                    rel_path = os.path.relpath(os.path.join(root, file), ".")
                    # Normalize slashes for consistency across OSes
                    local_files.append(rel_path.replace("\\", "/"))

    return sorted(local_files)


def sync_files() -> Tuple[List[str], List[str], List[str]]:
    """
    Sync upstream files to local repository.
    Returns (added_files, modified_files, deleted_upstream_files).
    """
    upstream_paths = get_upstream_target_paths()
    upstream_set = set(upstream_paths)
    local_existing = find_local_tracked_skill_files()

    added = []
    modified = []
    deleted_upstream = []

    for path in upstream_paths:
        try:
            upstream_content = fetch_raw_content(path)
        except Exception as e:
            print(f"Error fetching {path}: {e}", file=sys.stderr)
            continue

        if not os.path.exists(path):
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(upstream_content)
            added.append(path)
            print(f"Added new file: {path}")
        else:
            with open(path, "r", encoding="utf-8") as f:
                current_content = f.read()

            if current_content != upstream_content:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(upstream_content)
                modified.append(path)
                print(f"Modified existing file: {path}")
            else:
                print(f"Unchanged: {path}")

    # Check if any local file no longer exists upstream
    for local_file in local_existing:
        if local_file not in upstream_set:
            deleted_upstream.append(local_file)
            print(f"File no longer exists upstream: {local_file}")

    return added, modified, deleted_upstream


def generate_pr_body(added: List[str], modified: List[str], deleted_upstream: List[str]) -> str:
    """Generate Markdown PR body describing the sync changes."""
    body_lines = [
        "## Upstream Sync: `mattpocock/skills`",
        "",
        "Automated upstream synchronization from `mattpocock/skills` (`main` branch).",
        "",
    ]

    total_changes = len(added) + len(modified)
    body_lines.append(f"**Total files updated/added:** {total_changes}")
    body_lines.append("")

    if added:
        body_lines.append("### ➕ Newly Added Files")
        for f in added:
            body_lines.append(f"- `{f}`")
        body_lines.append("")

    if modified:
        body_lines.append("### 📝 Modified Files")
        for f in modified:
            body_lines.append(f"- `{f}`")
        body_lines.append("")

    if deleted_upstream:
        body_lines.append("### ⚠️ Upstream Deletions Detected")
        body_lines.append("The following files were not found in the upstream tree and have been kept locally:")
        for f in deleted_upstream:
            body_lines.append(f"- `{f}` no longer exists upstream — manual review recommended")
        body_lines.append("")

    body_lines.append("---")
    body_lines.append("*Synced via GitHub Action `sync_mattpocock.yml`.*")
    return "\n".join(body_lines)


def main():
    print("Starting sync with mattpocock/skills...")
    added, modified, deleted_upstream = sync_files()

    has_changes = bool(added or modified)
    print(f"Sync complete. Added: {len(added)}, Modified: {len(modified)}, Deleted upstream: {len(deleted_upstream)}")

    pr_body = generate_pr_body(added, modified, deleted_upstream)
    with open("pr_body.md", "w", encoding="utf-8") as f:
        f.write(pr_body)

    # Write output to GITHUB_OUTPUT if available
    gh_output = os.environ.get("GITHUB_OUTPUT")
    if gh_output:
        with open(gh_output, "a", encoding="utf-8") as f:
            f.write(f"has_changes={'true' if has_changes else 'false'}\n")
            f.write(f"num_added={len(added)}\n")
            f.write(f"num_modified={len(modified)}\n")


if __name__ == "__main__":
    main()
