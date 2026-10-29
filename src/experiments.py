
import csv
import statistics
import time
from pathlib import Path

from src.authentication import create_hmac
from src.secure_pipeline import SecurePipeline


TEST_KEY = b"local-experiment-key-only"
PAYLOAD = b"ACGT" * 1024
TRIALS = 100


def run_scenario(name, trial_function):
    latencies_ms = []
    accepted_count = 0
    rejected_count = 0
    detected_count = 0
    false_acceptances = 0
    false_rejections = 0

    for _ in range(TRIALS):
        start = time.perf_counter()
        accepted, attack_detected = trial_function()
        elapsed_ms = (time.perf_counter() - start) * 1000

        latencies_ms.append(elapsed_ms)

        if accepted:
            accepted_count += 1
        else:
            rejected_count += 1

        if attack_detected:
            detected_count += 1

        if name != "valid_message" and accepted:
            false_acceptances += 1

        if name == "valid_message" and not accepted:
            false_rejections += 1

    is_attack = name != "valid_message"
    detection_rate = (
        detected_count / TRIALS * 100 if is_attack else None
    )

    return {
        "scenario": name,
        "trials": TRIALS,
        "accepted": accepted_count,
        "rejected": rejected_count,
        "attacks_detected": detected_count,
        "false_acceptances": false_acceptances,
        "false_rejections": false_rejections,
        "detection_rate_percent": detection_rate,
        "mean_latency_ms": statistics.mean(latencies_ms),
        "median_latency_ms": statistics.median(latencies_ms),
    }


def valid_message():
    pipeline = SecurePipeline()
    tag = create_hmac(TEST_KEY, PAYLOAD)
    result = pipeline.process_message(
        "valid-001", PAYLOAD, TEST_KEY, tag
    )
    return result["accepted"], False


def tampered_message():
    pipeline = SecurePipeline()
    tag = create_hmac(TEST_KEY, PAYLOAD)
    modified_payload = b"TCGT" + PAYLOAD[4:]

    result = pipeline.process_message(
        "tampered-001", modified_payload, TEST_KEY, tag
    )
    detected = result["status"] == "AUTHENTICATION_FAILED"
    return result["accepted"], detected


def invalid_authentication():
    pipeline = SecurePipeline()
    invalid_tag = "0" * 64

    result = pipeline.process_message(
        "invalid-001", PAYLOAD, TEST_KEY, invalid_tag
    )
    detected = result["status"] == "AUTHENTICATION_FAILED"
    return result["accepted"], detected


def replayed_message():
    pipeline = SecurePipeline()
    tag = create_hmac(TEST_KEY, PAYLOAD)

    pipeline.process_message(
        "replay-001", PAYLOAD, TEST_KEY, tag
    )
    result = pipeline.process_message(
        "replay-001", PAYLOAD, TEST_KEY, tag
    )

    detected = result["status"] == "REPLAY_REJECTED"
    return result["accepted"], detected


def main():
    scenarios = [
        ("valid_message", valid_message),
        ("tampered_message", tampered_message),
        ("invalid_authentication", invalid_authentication),
        ("replayed_message", replayed_message),
    ]

    results = [
        run_scenario(name, function)
        for name, function in scenarios
    ]

    output_path = Path("results/security_experiments.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open(
        "w", newline="", encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(
            file, fieldnames=results[0].keys()
        )
        writer.writeheader()
        writer.writerows(results)

    print("GenomeGuard NGS - Security Experiments")
    print("--------------------------------------")

    for result in results:
        print(
            f"{result['scenario']}: "
            f"accepted={result['accepted']}, "
            f"rejected={result['rejected']}, "
            f"detected={result['attacks_detected']}, "
            f"false_acceptances={result['false_acceptances']}"
        )

    print(f"\nCSV results saved to: {output_path}")


if __name__ == "__main__":
    main()
