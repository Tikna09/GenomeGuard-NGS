# GenomeGuard-NGS Network Extension

## Overview

This extension implements a network-based security layer for simulated Next-Generation Sequencing (NGS) data transfers.

It demonstrates application-level message authentication, payload integrity verification, and persistent replay protection over TLS 1.3.

## Architecture

- **Sender:** Kali Linux
- **Receiver:** Ubuntu Server
- **Transport:** TLS 1.3
- **Authentication:** HMAC-SHA256
- **Integrity:** SHA-256
- **Replay protection:** Persistent SQLite sequence tracking
- **Test payloads:** Synthetic FASTQ-like files

## Security Features

1. TLS 1.3 communication with server certificate verification.
2. HMAC-SHA256 authentication of transfer metadata.
3. SHA-256 verification of received payloads.
4. Persistent duplicate-sequence detection.
5. Input and metadata validation.
6. Automated security validation.

## Directory Structure

- `sender.py` — Secure client.
- `receiver.py` — Secure TLS receiver.
- `baseline_sender.py` — TLS-only benchmark client.
- `baseline_receiver.py` — TLS-only benchmark server.
- `automated_security_tests.py` — Automated security tests.
- `benchmark_results/` — CSV results and performance graphs.
- `tests/` — Additional test resources.

## Experimental Security Validation

The automated test suite produced the following results:

| Test | Expected HTTP status | Result |
|---|---:|---|
| Valid transfer | 200 | PASS |
| Invalid HMAC | 401 | PASS |
| Payload tampering | 400 | PASS |
| Invalid metadata | 400 | PASS |
| First replay test transfer | 200 | PASS |
| Duplicate sequence replay | 409 | PASS |

## Performance Evaluation

The benchmark compares a TLS-only baseline against the GenomeGuard-enabled transfer pipeline using synthetic payloads of 1 MiB, 10 MiB, and 50 MiB.

Five trials were conducted for each payload size and configuration. The results and graphs are available in `benchmark_results/`.

The measurements showed variability, including an extreme outlier in the original TLS-only 50 MiB trials. A separate retest was conducted and is reported independently. These results should not be interpreted as proof that GenomeGuard is faster than TLS-only.

## Reproducibility and Security

Generate your own HMAC key and TLS certificates for local testing. Never commit private keys, HMAC secrets, passwords, or virtual environments.

The receiver's private TLS key and the HMAC secret must remain protected.

## Limitations

- Uses synthetic FASTQ-like payloads, not validated biological sequencing datasets.
- Evaluated in a controlled Kali-to-Ubuntu virtual network.
- Does not demonstrate a real-world man-in-the-middle attack.
- Not a clinical or production sequencing deployment.
- Benchmark measurements are affected by virtual-machine and system variability.

## Research Scope

This extension evaluates application-level integrity, authentication, and replay protection for simulated NGS data transfers. It is an experimental cybersecurity prototype, not a sequencing or biological analysis engine.
