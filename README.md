# GenomeGuard-NGS
## An Experimental Evaluation of Data Integrity and Replay Protection in Simulated NGS Data Pipelines

![Language](https://img.shields.io/badge/Language-Python-blue)
![Security](https://img.shields.io/badge/Focus-Cybersecurity-red)
![Cryptography](https://img.shields.io/badge/Cryptography-HMAC--SHA256-green)
![Storage](https://img.shields.io/badge/Storage-SQLite-lightgrey)
![Testing](https://img.shields.io/badge/Testing-pytest-blue)

**GenomeGuard-NGS** is a Python-based cybersecurity research prototype designed to evaluate message authentication, data integrity, and replay protection in a simulated Next-Generation Sequencing (NGS)-style data pipeline.

The project investigates how cryptographic authentication and persistent sequence tracking can help identify modified messages and reject replayed messages in a controlled, local environment.

It compares a baseline pipeline that uses in-memory replay protection with an enhanced pipeline that authenticates message metadata and maintains persistent sequence state using SQLite.

> **Research scope:** GenomeGuard-NGS is an experimental simulation using synthetic DNA-alphabet payloads. It does not process real genomic or patient data, connect to sequencing equipment, or demonstrate detection of actual network-based Man-in-the-Middle (MitM) attacks.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Research Objectives](#research-objectives)
3. [Problem Statement](#problem-statement)
4. [Proposed Solution](#proposed-solution)
5. [System Architecture](#system-architecture)
6. [Security Features](#security-features)
7. [Technology Stack](#technology-stack)
8. [Project Structure](#project-structure)
9. [Installation and Setup](#installation-and-setup)
10. [Running the Project](#running-the-project)
11. [Experimental Methodology](#experimental-methodology)
12. [Security Experiment Results](#security-experiment-results)
13. [Security Comparison Results](#security-comparison-results)
14. [Performance Benchmark](#performance-benchmark)
15. [Automated Testing](#automated-testing)
16. [Understanding the Results](#understanding-the-results)
17. [Security Limitations](#security-limitations)
18. [Future Improvements](#future-improvements)
19. [Reproducibility](#reproducibility)
20. [Conclusion](#conclusion)
21. [Author](#author)

---

## 1. Project Overview

Next-Generation Sequencing technologies generate biological sequence data that may pass through multiple software components during processing. As with other data-processing systems, the integrity and authenticity of messages exchanged between components are important security considerations.

GenomeGuard-NGS provides a controlled environment for investigating selected message-level security properties.

The prototype implements two approaches:

**Baseline pipeline**
- Verifies a message payload using HMAC authentication.
- Uses an in-memory replay guard to track accepted message identifiers.
- Generates a SHA-256 digest for accepted payloads.
- Demonstrates the loss of replay history when the pipeline instance is recreated.

**Persistent freshness pipeline**
- Authenticates stream identifiers, message identifiers, sequence numbers, and payloads.
- Uses HMAC-SHA-256 to verify the authenticated message fields.
- Stores accepted sequence state in SQLite.
- Rejects duplicate or stale sequence numbers.
- Retains sequence state when the pipeline is reconstructed using the same database.

The project evaluates the behavior of these implementations through automated tests, security experiments, and comparative performance measurements.

### Research question

How does persistent sequence-based freshness validation affect replay protection and message-processing latency compared with a baseline implementation using in-memory replay tracking?

---

## 2. Research Objectives

The main objectives are:

1. Evaluate message authentication using HMAC-SHA-256.
2. Test detection of modified payloads when the original authentication tag is retained.
3. Test rejection of invalid authentication tags.
4. Evaluate duplicate-message rejection.
5. Investigate replay protection after pipeline reconstruction.
6. Evaluate persistent sequence-number tracking using SQLite.
7. Measure processing latency for two pipeline configurations.
8. Maintain repeatable experiments and machine-readable CSV results.
9. Document the security limitations and possible extensions of the prototype.

---

## 3. Problem Statement

Data-processing pipelines can be exposed to several message-level security risks.

### Data modification

A message payload may be altered while being transferred or processed. Without appropriate integrity verification, a receiver may process data that differs from what the sender authenticated.

### Invalid authentication

An attacker may provide an incorrect or forged authentication tag. The receiver needs to verify the tag before accepting the message.

### Message replay

A previously valid message may be submitted again. Authentication alone does not automatically prevent replay because an unchanged, previously authenticated message may still have a valid tag.

### Loss of volatile security state

A replay guard that stores accepted message identifiers only in memory loses that history when its process or pipeline instance is recreated. Previously accepted messages may then be accepted again if they otherwise pass validation.

### Research objective

GenomeGuard-NGS investigates these risks using synthetic messages and compares an in-memory baseline with persistent sequence-based freshness validation.

---

## 4. Proposed Solution

The project combines cryptographic message authentication with replay and freshness checks.

### Baseline design

The baseline verifies the HMAC tag associated with the payload and checks whether the message identifier has already been accepted by the current replay guard.

If authentication fails, the message is rejected. If the message identifier has already been accepted, the replay guard rejects it. Otherwise, the message is accepted and a SHA-256 payload digest is returned.

### Persistent freshness design

The persistent implementation authenticates the following fields:

- Stream identifier
- Message identifier
- Sequence number
- Payload

After successful authentication, it checks the sequence number against the last accepted number for that stream.

The message is rejected if its sequence number is not strictly greater than the stored sequence number. If validation succeeds, the sequence state is updated in SQLite.

This approach addresses the specific limitation of losing replay history when a pipeline instance is recreated, provided the same intact database is reused.

---

## 5. System Architecture

### 5.1 Baseline message flow

```text
Synthetic Message
       |
       v
HMAC Authentication
       |
       +---- Invalid ----> AUTHENTICATION_FAILED
       |
       v
In-Memory Replay Guard
       |
       +---- Duplicate --> REPLAY_REJECTED
       |
       v
Accept Message
       |
       v
Generate SHA-256 Payload Digest
```

### 5.2 Persistent freshness message flow

```text
Synthetic Message
       |
       v
Authenticate Message Fields
       |
       +---- Invalid ----> AUTHENTICATION_FAILED
       |
       v
Check SQLite Sequence State
       |
       +---- Stale or Duplicate
       |                 |
       |                 v
       |          STALE_OR_REPLAYED
       |
       v
Update Persistent Sequence State
       |
       v
Accept Message
```

### 5.3 Security-state comparison

| Property | Baseline pipeline | Persistent freshness pipeline |
|---|---|---|
| Payload authentication | Yes | Yes |
| Authenticated metadata | Payload only in the baseline HMAC | Stream ID, message ID, sequence number, and payload |
| Replay state | In-memory set | SQLite sequence state |
| State survives pipeline reconstruction | No | Yes, when the same intact database is reused |
| Rejects tested tampering | Yes | Yes |
| Rejects tested replay after reconstruction | No | Yes |

The comparison describes the current implementations. It does not imply that either implementation has been validated against every attack class.

---

## 6. Security Features

### 6.1 HMAC-SHA-256 authentication

HMAC is a keyed message-authentication mechanism. It enables a receiver with the correct secret key to verify that an authentication tag corresponds to the expected message.

The baseline implementation authenticates the payload. The persistent implementation authenticates a structured encoding of the stream ID, message ID, sequence number, and payload.

### 6.2 SHA-256 payload digest

The baseline generates a SHA-256 digest for an accepted payload.

A digest can help compare data against a trusted expected digest. A plain hash alone does not authenticate the sender or prove who created the data.

### 6.3 In-memory replay protection

The baseline replay guard tracks previously accepted message identifiers in a Python set.

It rejects a duplicate identifier while the relevant state remains in memory. Recreating the pipeline resets this set.

### 6.4 Persistent sequence tracking

The persistent sequence guard stores the latest accepted sequence number for each stream in SQLite.

A message must have a strictly increasing sequence number to be accepted. This supports the tested replay-protection scenario after pipeline reconstruction.

### 6.5 Input validation

The message-authentication implementation validates message identifiers, stream identifiers, sequence numbers, and payload types before constructing the authenticated message representation.

The tests also cover invalid Unicode identifier cases and sequence-number validation.

### 6.6 Audit logging

The baseline includes a JSON Lines audit-log writer for recording message-processing results.

The current local audit-log approach should not be considered tamper-proof. Stronger protection would require additional access controls, protected storage, or independently anchored audit records.

---

## 7. Technology Stack

| Technology | Role |
|---|---|
| Python | Implementation and experimental scripts |
| HMAC-SHA-256 | Keyed message authentication |
| SHA-256 | Payload digest generation |
| SQLite | Persistent sequence-state storage |
| pytest | Automated testing |
| CSV | Experiment and benchmark result storage |
| Git | Version control |

The project is designed to run locally in a Python environment.

---

## 8. Project Structure

```text
GenomeGuard-NGS/
├── data/
├── logs/
├── results/
│   ├── comparative_benchmark.csv
│   └── security_experiments.csv
├── src/
│   ├── authentication.py
│   ├── audit_log.py
│   ├── benchmark.py
│   ├── comparative_benchmark.py
│   ├── demo.py
│   ├── experiments.py
│   ├── freshness_pipeline.py
│   ├── integrity.py
│   ├── message_authentication.py
│   ├── persistence_experiment.py
│   ├── persistent_freshness_pipeline.py
│   ├── persistent_sequence_guard.py
│   ├── replay_protection.py
│   ├── secure_pipeline.py
│   ├── security_comparison.py
│   ├── sequence_guard.py
│   ├── synthetic_data.py
│   └── verification.py
├── tests/
├── requirements.txt
└── README.md
```

The `results/` directory contains the recorded security experiment and comparative benchmark CSV files. The `src/` directory contains the implementation and experiment scripts, while `tests/` contains the automated test suite.

---

## 9. Installation and Setup

### Prerequisites

- Python
- Git
- A Linux terminal or another compatible command-line environment

### Step 1: Clone the repository

Replace the placeholder below with the actual URL of your GitHub repository.

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd GenomeGuard-NGS
```

### Step 2: Create a virtual environment

```bash
python -m venv .venv
```

### Step 3: Activate the environment on Kali Linux

```bash
source .venv/bin/activate
```

### Step 4: Install dependencies

```bash
python -m pip install -r requirements.txt
```

If you are using an existing environment in which the dependencies are already installed, you can proceed directly to the test and experiment commands.

---

## 10. Running the Project

Run these commands from the repository root with the virtual environment activated.

### Run the automated tests

```bash
python -m pytest -q
```

### Run the security experiment

```bash
python -m src.experiments
```

### Run the persistence experiment

```bash
python -m src.persistence_experiment
```

### Run the comparative performance benchmark

```bash
python -m src.comparative_benchmark
```

### Run the security comparison experiment

```bash
python -m src.security_comparison
```

The scripts may write result files into `results/`. Check the relevant script before rerunning experiments if you want to preserve an earlier result, because some scripts may overwrite their output.

---

## 11. Experimental Methodology

The project uses local synthetic messages rather than real genomic datasets or external network traffic.

### 11.1 Security experiment

The recorded security experiment performs 100 trials for each of four scenarios:

1. Valid messages.
2. Tampered messages.
3. Invalid authentication tags.
4. Replayed messages.

The experiment records message acceptance, rejection, attack detection, false acceptance, false rejection, detection rate where applicable, and latency.

### 11.2 Security comparison experiment

The comparison script evaluates five baseline checks and six persistent freshness checks.

The baseline tests include valid-message acceptance, payload tampering, invalid tags, duplicate identifiers, and replay after pipeline reconstruction.

The persistent tests include valid-message acceptance, payload tampering, invalid tags, duplicate sequence numbers, replay after reconstruction using the same database, and acceptance of a higher sequence number.

### 11.3 Performance benchmark

The benchmark uses:

- Payload size: 4,096 bytes
- Trials per pipeline per round: 200
- Rounds: 5
- Total messages per pipeline: 1,000

Latency is recorded in milliseconds.

Because the two pipelines authenticate different fields and use different replay-state mechanisms, the benchmark compares complete pipeline configurations rather than isolating one component's cost.

---

## 12. Security Experiment Results

The recorded results in `results/security_experiments.csv` are:

| Scenario | Trials | Accepted | Rejected | Attacks detected | Detection rate |
|---|---:|---:|---:|---:|---:|
| Valid message | 100 | 100 | 0 | 0 | N/A |
| Tampered message | 100 | 0 | 100 | 100 | 100% |
| Invalid authentication | 100 | 0 | 100 | 100 | 100% |
| Replayed message | 100 | 0 | 100 | 100 | 100% |

No false acceptances or false rejections were recorded in these tested scenarios.

### Interpretation

All valid messages were accepted in the valid-message scenario. The tampered-message, invalid-authentication, and replay scenarios were rejected in every recorded trial.

These results support the behavior of the current implementation under the tested conditions. They should not be interpreted as a guarantee of 100% detection for all possible attacks.

---

## 13. Security Comparison Results

The separate security comparison script reported 11 passing checks.

| Test | Baseline | Persistent freshness |
|---|---|---|
| Valid message accepted | Pass | Pass |
| Tampered payload rejected | Pass | Pass |
| Invalid authentication tag rejected | Pass | Pass |
| Duplicate or repeated sequence rejected | Pass | Pass |
| Replay after pipeline reconstruction | Accepted, demonstrating a limitation | Rejected |
| Higher sequence accepted | Not included in this comparison | Pass |

**Overall result: 11/11 checks passed.**

### Key observation

The baseline's in-memory replay history is lost when a new pipeline instance is created. The tested replay was therefore accepted after reconstruction.

The persistent pipeline rejected the same sequence after reconstruction because it reused the SQLite database containing the previously accepted sequence number.

This result demonstrates the value of retaining freshness state for the tested scenario. It does not show that SQLite is protected against database modification or rollback.

---

## 14. Performance Benchmark

The recorded results in `results/comparative_benchmark.csv` are summarized below.

| Metric | Baseline in-memory | Persistent freshness |
|---|---:|---:|
| Payload size | 4,096 bytes | 4,096 bytes |
| Total messages | 1,000 | 1,000 |
| Accepted messages | 1,000 | 1,000 |
| Rejected messages | 0 | 0 |
| Average of round mean latencies | 0.0124 ms | 0.3808 ms |
| Average of round median latencies | 0.0112 ms | 0.3396 ms |

The persistent pipeline recorded approximately 30.7 times the baseline's average round-mean latency in this experiment.

### Performance interpretation

The persistent implementation performs additional work:

- Authenticates message metadata as well as the payload.
- Validates sequence freshness.
- Reads and updates persistent sequence state.

The baseline authenticates only the payload and uses an in-memory replay guard.

Consequently, the measured difference reflects the combined behavior of these configurations. It cannot be attributed exclusively to SQLite.

The results represent local processing latency for one payload size and the recorded test environment. They do not establish production throughput or network latency.

---

## 15. Automated Testing

The latest confirmed test-suite output was:

```text
58 passed in 0.25s
```

The test suite covers authentication, integrity verification, freshness checks, persistent sequence tracking, replay protection, input validation, and related pipeline behavior.

A passing test suite provides evidence that the tested conditions behaved as expected. It does not prove that the implementation is free from all security vulnerabilities.

For reproducibility, run:

```bash
python -m pytest -q
```

Record the output when preparing a new release or research submission.

---

## 16. Understanding the Results

The experiments support three main observations.

### Observation 1: Authentication rejects the tested tampering

The recorded experiments rejected modified payloads when the original authentication tag was retained, as well as invalid authentication tags.

This behavior depends on using the correct shared secret and authenticating the data that the receiver intends to trust.

### Observation 2: Persistent state improves the tested restart behavior

The baseline lost its in-memory replay history when recreated. The persistent pipeline retained sequence state in the reused database and rejected the tested replay.

### Observation 3: The persistent configuration has higher observed latency

The persistent pipeline recorded higher latency while performing additional metadata authentication and database operations.

The results demonstrate a trade-off in the current configurations. A more controlled benchmark would be required to isolate the cost of persistent storage from the cost of additional authentication.

---

## 17. Security Limitations

GenomeGuard-NGS is a research prototype, not a production-ready security product.

### 17.1 No real network-based MitM evaluation

The experiments simulate message tampering and replay within local code. They do not intercept real network traffic, manipulate live sessions, or evaluate TLS certificate validation.

Therefore, actual network-based MitM detection effectiveness has not been demonstrated.

### 17.2 Key management

The experiments use local test keys. Production deployment would require a secure method for generating, storing, distributing, rotating, and revoking keys.

### 17.3 Database integrity

Persistent replay protection depends on retaining trustworthy sequence state. SQLite alone does not prevent unauthorized modification, deletion, or rollback of the database.

### 17.4 Replay protection scope

Strictly increasing sequence numbers reject the tested duplicate or stale sequence values. Other issues, such as stream initialization, recovery, sequence synchronization, and delivery ordering, need further evaluation.

### 17.5 Audit-log integrity

A local JSON Lines audit log can be useful for recording events, but an attacker with sufficient filesystem access may be able to modify it. The current implementation does not provide tamper-proof audit logging.

### 17.6 Synthetic payloads

The experiments use synthetic DNA-alphabet bytes. They do not test biological correctness, sequencing accuracy, or a real NGS processing workflow.

### 17.7 Performance generalization

The benchmark covers one payload size and five rounds. Hardware, operating-system load, storage performance, database settings, and workload may affect the results.

---

## 18. Future Improvements

Potential future research directions include:

1. **Isolated network testing:** Evaluate message modification and replay in a controlled lab using synthetic messages.
2. **Key management:** Add a documented key-management design and test key rotation.
3. **Database tampering:** Test whether database modification or rollback can defeat freshness validation.
4. **Concurrency evaluation:** Expand stress tests for simultaneous message processing.
5. **Broader benchmarks:** Test multiple payload sizes and workloads over repeated runs.
6. **Audit protection:** Evaluate tamper-evident or independently anchored audit records.
7. **Reproducibility:** Record operating-system, Python, dependency, and database versions alongside benchmark results.
8. **NGS workflow integration:** Investigate integration with a suitable non-sensitive test workflow before making claims about real sequencing environments.

These are proposed extensions, not completed features.

---

## 19. Reproducibility

The experiment scripts and recorded CSV outputs provide a basis for reproducing the current local tests.

From the repository root, run:

```bash
python -m pytest -q
python -m src.experiments
python -m src.persistence_experiment
python -m src.comparative_benchmark
python -m src.security_comparison
```

Review the scripts before rerunning them if you need to preserve earlier CSV outputs.

The committed benchmark CSV and the security experiment CSV should be treated as records of specific runs. New runs may produce different timing measurements.

---

## 20. Conclusion

GenomeGuard-NGS provides a local experimental environment for evaluating message authentication, integrity verification, and replay protection in a simulated NGS-like data pipeline.

The recorded security experiment rejected all tested tampered-message, invalid-authentication, and replay cases across 100 trials per scenario. The security comparison reported 11 passing checks, including rejection of the tested replay after persistent pipeline reconstruction. The latest confirmed automated test suite also passed all 58 tests.

The comparative benchmark showed higher observed latency for the persistent freshness pipeline than for the baseline. Because the implementations perform different amounts of work, the measured difference represents a configuration-level comparison rather than an isolated estimate of database overhead.

The findings provide preliminary evidence that persistent sequence tracking can address the specific replay-history limitation demonstrated in the baseline. Further network-level testing, key-management evaluation, database-integrity testing, and broader performance analysis are needed before drawing conclusions about real-world NGS deployments.

---

## 21. Author

**Ankit Kirtane**

Cybersecurity | Artificial Intelligence & Data Science

**Project:** GenomeGuard-NGS

Add your actual GitHub profile, repository URL, and LinkedIn profile URL before publishing this README.

---
*Disclaimer: This repository is intended for educational and defensive cybersecurity research using synthetic data in a local simulation. It is not a validated NGS security product and should not be used as the sole security control for real systems.*
