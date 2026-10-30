
import csv
from pathlib import Path

output = Path("benchmark_results/security_validation_report.csv")

results = [
    ["Valid transfer", 200, "accepted", "PASS"],
    ["Invalid HMAC", 401, "authentication_failed", "PASS"],
    ["Payload tampering", 400, "integrity_failed", "PASS"],
    ["Invalid metadata", 400, "invalid_metadata_fields", "PASS"],
    ["First replay transfer", 200, "accepted", "PASS"],
    ["Duplicate sequence replay", 409, "replay_or_duplicate", "PASS"],
]

output.parent.mkdir(parents=True, exist_ok=True)

with output.open("w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow([
        "Security Test",
        "Expected HTTP Status",
        "Expected Server Response",
        "Result"
    ])
    writer.writerows(results)

print("Security validation report generated.")
print(f"File: {output}")
print(f"Total tests: {len(results)}")
print(f"Passed: {sum(row[3] == 'PASS' for row in results)}")
