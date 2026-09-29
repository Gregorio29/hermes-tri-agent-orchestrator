"""
Unit tests for Loop Controller and circuit breaker detection.
"""

import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.loop_controller import LoopController


class TestLoopController(unittest.TestCase):

    def setUp(self):
        self.controller = LoopController(max_iterations=10, max_retries=2)

    def test_iteration_limit(self):
        # check_iteration_limit returns (is_limit_reached, reason)
        reached, reason = self.controller.check_iteration_limit(5)
        self.assertFalse(reached)
        self.assertIsNone(reason)

        reached, reason = self.controller.check_iteration_limit(11)
        self.assertTrue(reached)
        self.assertIn("iteraciones", reason.lower())

    def test_identical_loop_detection(self):
        identical_prompt = "Execute command: dir /s /b"
        
        # Add identical prompts to history
        loop_detected = False
        reason_msg = None
        for _ in range(6):
            detected, reason = self.controller.record_and_check_prompt(identical_prompt)
            if detected:
                loop_detected = True
                reason_msg = reason
                break
        
        self.assertTrue(loop_detected)
        self.assertIsNotNone(reason_msg)


if __name__ == "__main__":
    unittest.main()
