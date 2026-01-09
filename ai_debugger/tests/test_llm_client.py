from ai_debugger.tests.test_signals import synthetic_signals
from ai_debugger.correlator.signal_ranker import rank_signals
from ai_debugger.reasoning.prompt_template import build_prompt
from ai_debugger.reasoning.llm_client import MockLLMClient, LLMResponseError
from ai_debugger.reasoning.response_validator import (
    validate_rca_response,
    InvalidRCAResponse
)


def run(mode):
    print(f"\n=== Testing LLM mode: {mode} ===")

    signals = synthetic_signals()
    ranked = rank_signals(signals)
    prompt = build_prompt(ranked)

    client = MockLLMClient(mode=mode)

    try:
        response = client.analyze(prompt)
        validated = validate_rca_response(response, ranked)
        print("✅ Accepted RCA:", validated)
    except (LLMResponseError, InvalidRCAResponse) as e:
        print("❌ Rejected:", str(e))


if __name__ == "__main__":
    for mode in ["good", "insufficient", "invalid_json", "hallucination"]:
        run(mode)
