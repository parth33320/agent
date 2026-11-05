import os
import unittest
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, os.path.abspath("scripts"))

from sync_mattpocock import (
    get_upstream_target_paths,
    generate_pr_body,
    sync_files
)
from score_12_layers import (
    evaluate_layer_status,
    generate_status_markdown
)
from detect_repo_type import (
    detect_repo_type,
    rule_based_fallback,
    VALID_CATEGORIES
)
from sync_all_repos import (
    load_competitive_map,
    generate_improvement_proposal
)


class TestSyncMattPocock(unittest.TestCase):
    def test_generate_pr_body_with_changes(self):
        added = ["skills/test/SKILL.md"]
        modified = ["AGENTS.md"]
        deleted = ["old/SKILL.md"]
        body = generate_pr_body(added, modified, deleted)
        self.assertIn("Total files updated/added:** 2", body)
        self.assertIn("➕ Newly Added Files", body)
        self.assertIn("`skills/test/SKILL.md`", body)
        self.assertIn("📝 Modified Files", body)
        self.assertIn("`AGENTS.md`", body)
        self.assertIn("⚠️ Upstream Deletions Detected", body)
        self.assertIn("`old/SKILL.md` no longer exists upstream — manual review recommended", body)

    @patch("sync_mattpocock.requests.get")
    def test_get_upstream_target_paths(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "tree": [
                {"path": "skills/eng/SKILL.md", "type": "blob"},
                {"path": "skills/other/README.md", "type": "blob"},
                {"path": "other/SKILL.md", "type": "blob"}
            ]
        }
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        paths = get_upstream_target_paths()
        self.assertIn("AGENTS.md", paths)
        self.assertIn("CLAUDE.md", paths)
        self.assertIn("GLOSSARY.md", paths)
        self.assertIn("skills/eng/SKILL.md", paths)
        self.assertNotIn("skills/other/README.md", paths)
        self.assertNotIn("other/SKILL.md", paths)


class TestScore12Layers(unittest.TestCase):
    def test_evaluate_layer_status(self):
        status, evidence = evaluate_layer_status([])
        self.assertEqual(status, "MISSING")

        status, evidence = evaluate_layer_status([("scripts/test.py", 10, "timeout = 30")])
        self.assertEqual(status, "PRESENT")
        self.assertIn("scripts/test.py:10", evidence)

        status, evidence = evaluate_layer_status([("docs/layers.md", 20, "timeout = 30")])
        self.assertEqual(status, "PARTIAL")

    def test_generate_status_markdown(self):
        results = {i: ("PRESENT", f"Evidence {i}") for i in range(1, 13)}
        md = generate_status_markdown(results)
        self.assertIn("# 12-Layer Production Agent Status", md)
        self.assertIn("**PRESENT:** 12 / 12", md)


class TestDetectRepoType(unittest.TestCase):
    def test_rule_based_fallback(self):
        cat = rule_based_fallback("warehouse-robotics", "Logistics and freight distribution system")
        self.assertEqual(cat, "supply-chain")

        cat = rule_based_fallback("payroll-suite", "Employee benefits and onboarding")
        self.assertEqual(cat, "hr")

        cat = rule_based_fallback("trading-engine", "Fintech algorithmic trading and payments")
        self.assertEqual(cat, "finance")

        cat = rule_based_fallback("clinic-ehr", "Hospital patient triage workflow")
        self.assertEqual(cat, "healthcare")

        cat = rule_based_fallback("random-repo", "Nothing special")
        self.assertEqual(cat, "other")

    def test_valid_categories(self):
        self.assertEqual(len(VALID_CATEGORIES), 13)
        self.assertIn("supply-chain", VALID_CATEGORIES)
        self.assertIn("other", VALID_CATEGORIES)


class TestCompetitiveMap(unittest.TestCase):
    def test_competitive_map_content(self):
        cmap = load_competitive_map()
        self.assertIn("supply-chain", cmap)
        self.assertEqual(cmap["supply-chain"], ["servicenow.com", "sap.com", "salesforce.com"])
        self.assertEqual(len(cmap["hr"]), 3)
        self.assertEqual(len(cmap["finance"]), 3)
        self.assertEqual(len(cmap["other"]), 0)

    def test_generate_improvement_proposal_mock(self):
        proposal = generate_improvement_proposal(
            "supply-chain-app",
            "supply-chain",
            "A test supply chain application",
            {"sap.com": ["SAP IBP autonomous rebalancing"]},
            "2026-11-05"
        )
        self.assertIn("Agent Improvement Proposal: Supply-Chain Features from Frontier Apps", proposal)
        self.assertIn("supply-chain-app", proposal)


if __name__ == "__main__":
    unittest.main()
