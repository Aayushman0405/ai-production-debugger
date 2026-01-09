from ai_debugger.tests.test_signals import synthetic_signals
from ai_debugger.correlator.signal_ranker import rank_signals
from ai_debugger.reasoning.prompt_template import build_prompt


if __name__ == "__main__":
    signals = synthetic_signals()
    ranked = rank_signals(signals)

    prompt = build_prompt(ranked)

    print("===== PROMPT SENT TO LLM =====")
    print(prompt)
