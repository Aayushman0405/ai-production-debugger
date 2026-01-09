from ai_debugger.tests.test_signals import synthetic_signals
from ai_debugger.correlator.signal_ranker import rank_signals


if __name__ == "__main__":
    signals = synthetic_signals()

    ranked = rank_signals(signals)

    print("Ranked Signals (most important first):")
    for i, s in enumerate(ranked, start=1):
        print(f"{i}. {s['signal_type']} | severity={s['severity']}")
