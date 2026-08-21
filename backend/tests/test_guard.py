import unittest
import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.app.rag.guard import hallucination_guard, HallucinationGuard

class TestHallucinationGuard(unittest.TestCase):
    def setUp(self):
        self.guard = HallucinationGuard()

    def test_guard_valid_entities(self):
        context_ids = {"CVE-2024-21626", "T1611", "CVE-2021-44228"}
        text = "The vulnerability CVE-2024-21626 allows container escape via technique T1611."
        res = self.guard.validate_and_sanitize(text, context_ids)
        
        self.assertEqual(res.ids_checked, 2)
        self.assertEqual(res.ids_verified, 2)
        self.assertFalse(res.unverified_claims_removed)
        self.assertIn("CVE-2024-21626", res.sanitized_text)
        self.assertIn("T1611", res.sanitized_text)

    def test_guard_poisoned_output_stripping(self):
        context_ids = {"CVE-2024-21626", "T1611"}
        
        # Deliberately poisoned output containing fake CVE-2099-99999 and fake technique T9999
        poisoned_text = (
            "Analysis shows that CVE-2024-21626 is related to the zero-day exploit CVE-2099-99999 "
            "and uses the unverified technique T9999 to escape."
        )
        
        res = self.guard.validate_and_sanitize(poisoned_text, context_ids)
        
        self.assertEqual(res.ids_checked, 3)
        self.assertEqual(res.ids_verified, 1)
        self.assertTrue(res.unverified_claims_removed)
        self.assertIn("CVE-2024-21626", res.verified_ids)
        self.assertIn("CVE-2099-99999", res.unverified_ids)
        self.assertIn("T9999", res.unverified_ids)
        
        # Prove fake CVE and technique were stripped/replaced
        self.assertIn("[UNVERIFIED CLAIM REMOVED: CVE-2099-99999]", res.sanitized_text)
        self.assertIn("[UNVERIFIED CLAIM REMOVED: T9999]", res.sanitized_text)
        self.assertNotIn("CVE-2099-99999 ", res.sanitized_text)

    def test_guard_empty_input(self):
        res = self.guard.validate_and_sanitize("", set())
        self.assertEqual(res.ids_checked, 0)
        self.assertEqual(res.ids_verified, 0)
        self.assertFalse(res.unverified_claims_removed)

if __name__ == "__main__":
    unittest.main()
