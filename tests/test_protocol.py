"""
Unit tests for the Tri-Agent Protocol parser and serializers.
"""

import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.protocol import (
    parse_hf_response,
    format_hf_response,
    format_gemini_result,
    parse_gemini_result
)


class TestTriAgentProtocol(unittest.TestCase):

    def test_parse_valid_response_block(self):
        raw_msg = """
Here is my decision:
<HF_RESPONSE>
STATUS=CONTINUE
AGENT=CHATGPT
TARGET_AGENT=HERMES

TASK_SUMMARY:
Run discovery command

NEXT_ACTION:
Inspect local projects

PROMPT:
python list_projects.py

INPUT_REQUIRED:
NO

OUTPUT_EXPECTED:
JSON list of projects

RETURN_REQUIRED:
YES
</HF_RESPONSE>
"""
        parsed = parse_hf_response(raw_msg)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.get("status"), "CONTINUE")
        self.assertEqual(parsed.get("agent"), "CHATGPT")
        self.assertEqual(parsed.get("target_agent"), "HERMES")
        self.assertEqual(parsed.get("task_summary"), "Run discovery command")
        self.assertEqual(parsed.get("next_action"), "Inspect local projects")
        self.assertEqual(parsed.get("prompt"), "python list_projects.py")
        self.assertFalse(parsed.get("input_required"))
        self.assertTrue(parsed.get("return_required"))

    def test_format_hf_response(self):
        result_str = format_hf_response(
            status="CONTINUE",
            agent="CHATGPT",
            target_agent="HERMES",
            task_summary="Execute step 1",
            next_action="Run pytest",
            prompt="pytest -v",
            input_required=False,
            output_expected="Tests passed",
            return_required=True
        )
        self.assertIn("<HF_RESPONSE>", result_str)
        self.assertIn("AGENT=CHATGPT", result_str)
        self.assertIn("STATUS=CONTINUE", result_str)
        self.assertIn("TASK_SUMMARY:\nExecute step 1", result_str)

    def test_gemini_result_format_and_parse(self):
        gemini_str = format_gemini_result(
            status="SUCCESS",
            file_path="results/diagram.png",
            file_type="PNG",
            dimensions="1920x1080",
            timestamp="2026-09-28 22:00:00",
            prompt_used="Draw a cloud architecture diagram",
            errors=None
        )
        parsed = parse_gemini_result(gemini_str)
        self.assertEqual(parsed.get("status"), "SUCCESS")
        self.assertEqual(parsed.get("file_path"), "results/diagram.png")
        self.assertEqual(parsed.get("dimensions"), "1920x1080")


if __name__ == "__main__":
    unittest.main()
