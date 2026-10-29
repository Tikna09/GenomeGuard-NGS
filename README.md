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
