
import sqlite3
from pathlib import Path


class PersistentSequenceGuard:
    """Store the highest accepted sequence per stream in SQLite."""

    def __init__(self, database_path: str):
        self.database_path = str(database_path)

        if self.database_path != ":memory:":
            Path(self.database_path).parent.mkdir(
                parents=True, exist_ok=True
            )

        connection = self._connect()
        try:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS stream_sequences (
                    stream_id TEXT PRIMARY KEY,
                    last_sequence INTEGER NOT NULL
                        CHECK(last_sequence >= 0)
                )
            """)
        finally:
            connection.close()

    def _connect(self):
        connection = sqlite3.connect(
            self.database_path,
            timeout=10.0,
            isolation_level=None,
        )
        connection.execute("PRAGMA busy_timeout = 10000")
        return connection

    def accept(self, stream_id: str, sequence_number: int) -> bool:
        """Atomically accept only a strictly increasing sequence."""
        if not isinstance(stream_id, str) or not stream_id.strip():
            return False

        if (
            not isinstance(sequence_number, int)
            or isinstance(sequence_number, bool)
            or not 0 <= sequence_number <= 0x7FFFFFFFFFFFFFFF
        ):
            return False

        connection = self._connect()

        try:
            connection.execute("BEGIN IMMEDIATE")

            row = connection.execute(
                "SELECT last_sequence FROM stream_sequences "
                "WHERE stream_id = ?",
                (stream_id,),
            ).fetchone()

            if row is not None and sequence_number <= row[0]:
                connection.rollback()
                return False

            connection.execute(
                """
                INSERT INTO stream_sequences (stream_id, last_sequence)
                VALUES (?, ?)
                ON CONFLICT(stream_id)
                DO UPDATE SET last_sequence = excluded.last_sequence
                """,
                (stream_id, sequence_number),
            )

            connection.commit()
            return True

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()

