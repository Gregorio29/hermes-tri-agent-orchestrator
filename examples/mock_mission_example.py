"""
Example of building a synthetic mission state and simulating a Tri-Agent turn.
"""

import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.protocol import format_hf_response, parse_hf_response, format_gemini_result
from core.loop_controller import LoopController


def main():
    print("[*] Simulating Tri-Agent Orchestration Turn...")
    
    # 1. ChatGPT generates a planning step
    mock_chatgpt_response = format_hf_response(
        status="CONTINUE",
        agent="CHATGPT",
        target_agent="HERMES",
        task_summary="Scan external attack surface and verify HTTPS headers",
        next_action="Run passive security scan on target",
        prompt="python scanner.py -t example.com -q",
        input_required=False,
        output_expected="Scan JSON report in reports/ directory",
        return_required=True
    )
    
    print("\n[1] ChatGPT Formatted Protocol Block:")
    print(mock_chatgpt_response)
    
    # 2. Protocol parser digests the message
    parsed = parse_hf_response(mock_chatgpt_response)
    print(f"\n[2] Parsed Target: {parsed['target_agent']} | Status: {parsed['status']}")
    print(f"    Action Prompt: {parsed['prompt']}")
    
    # 3. Loop controller monitors state
    controller = LoopController(max_iterations=50)
    loop_detected, reason = controller.record_and_check_prompt(parsed['prompt'])
    print(f"\n[3] Loop Safety Status: Loop Detected = {loop_detected}")


if __name__ == "__main__":
    main()
