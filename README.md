# GenomeGuard NGS — Day 1 Starter

A local, defensive research prototype for evaluating integrity controls in a **simulated** NGS-style data pipeline.

## Safety and scope
- Uses synthetic DNA-alphabet strings only (A/C/G/T).
- Does not connect to networks or intercept traffic.
- Does not use real genomic or patient data.
- SHA-256 detects differences only when the expected digest is trusted; it does not authenticate the sender.

## Setup (Kali Linux)

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git nano
mkdir -p ~/GenomeGuard-NGS
cd ~/GenomeGuard-NGS
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install pytest
```

Copy the starter files into `~/GenomeGuard-NGS` (or unzip the supplied starter archive there). Then run:

```bash
python -m pytest -q
python -m src.demo
```

Expected: tests pass and the demo reports that the original synthetic payload verifies, then reports that the modified copy fails verification.

## Day 1 outcomes
- Generate deterministic synthetic payloads.
- Create SHA-256 baseline digests.
- Detect changes to a file against a trusted baseline.
- Run unit tests.

## Next
Day 2 adds HMAC authentication. Day 3 adds controlled message-tampering and replay scenarios. The current Day 1 code is not a production security system.

## Security Evaluation

GenomeGuard NGS is a local defensive research prototype for
evaluating integrity, authentication, and basic replay detection
in a simulated NGS-like data pipeline.

### Implemented Features

- SHA-256 integrity verification
- HMAC-SHA-256 message authentication
- In-memory replay detection
- Integrated verification pipeline
- JSONL audit logging
- Performance benchmark and CSV experiment runner

### Preliminary Experimental Results

In one local run, 100 trials were performed for each scenario:

| Scenario | Result |
|---|---|
| Valid messages | 100 accepted |
| Modified payloads | 100 rejected |
| Invalid authentication tags | 100 rejected |
| Replayed message IDs | 100 rejected |

The automated test suite reported 22 passing tests.

These are preliminary results from controlled synthetic tests.
They do not demonstrate 100% detection against real-world
man-in-the-middle attacks.

### Limitations

- Replay state is held in memory and lost on restart.
- HMAC authenticates the payload, not the message ID or freshness metadata.
- Audit logs are not tamper-proof.
- Performance results require repeated trials for reliable comparison.
- No real sequencing equipment, patient data, or external network interception is used.

### Future Work

- Authenticate payloads together with message IDs and freshness metadata.
- Evaluate replay persistence and concurrent message handling.
- Repeat experiments with different payload sizes.
- Compare baseline integrity, HMAC, and freshness-aware approaches.
- Review related research and assess the novelty of the approach.
