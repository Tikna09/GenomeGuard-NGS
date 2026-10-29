import tempfile
from pathlib import Path

from src.message_authentication import create_message_tag
from src.persistent_freshness_pipeline import (
    PersistentFreshnessPipeline,
)


KEY = b"local-persistence-experiment-key"
STREAM_ID = "synthetic-stream-001"
PAYLOAD = b"ACGT" * 256


def submit(pipeline, sequence_number):
    message_id = f"synthetic-message-{sequence_number}"
    tag = create_message_tag(
        KEY,
        STREAM_ID,
        message_id,
        sequence_number,
        PAYLOAD,
    )

    return pipeline.process(
        KEY,
        STREAM_ID,
        message_id,
        sequence_number,
        PAYLOAD,
        tag,
    )


def main():
    with tempfile.TemporaryDirectory() as temp_dir:
        database_path = str(Path(temp_dir) / "freshness.sqlite3")

        # First pipeline instance.
        pipeline = PersistentFreshnessPipeline(database_path)

        first = submit(pipeline, 1)
        replay = submit(pipeline, 1)
        pipeline.sequence_guard._connect().close()

        # Recreate the pipeline using the same database.
        restarted_pipeline = PersistentFreshnessPipeline(database_path)
        replay_after_restart = submit(restarted_pipeline, 1)
        higher_sequence = submit(restarted_pipeline, 2)

        results = {
            "first_message_accepted": first["accepted"],
            "duplicate_rejected": not replay["accepted"],
            "replay_after_restart_rejected": (
                not replay_after_restart["accepted"]
            ),
            "higher_sequence_accepted": higher_sequence["accepted"],
        }

        print("GenomeGuard-NGS - Persistence Experiment")
        print("----------------------------------------")

        for name, passed in results.items():
            print(f"{name}: {'PASS' if passed else 'FAIL'}")

        print(f"\nOverall: {sum(results.values())}/{len(results)} checks passed")

        if not all(results.values()):
            raise SystemExit(1)


if __name__ == "__main__":
    main()
