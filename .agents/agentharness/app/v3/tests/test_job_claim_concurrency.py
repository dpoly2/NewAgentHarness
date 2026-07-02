"""test_job_claim_concurrency.py — T6 job-claim concurrency proof (SQLite path).

The Postgres path uses ``UPDATE ... WHERE id = (SELECT ... FOR UPDATE SKIP
LOCKED)`` which we cannot execute here (no PG infra). This test exercises the
SQLite branch we CAN run: the two-step optimistic claim
(``SELECT oldest queued id`` then ``UPDATE ... WHERE status='queued'``). Two
threads hammering the queue must claim each job exactly once — no double-claim,
no lost job — proving the WHERE-guarded UPDATE serializes correctly.

Each thread calls _claim_queued_job(), which uses _thread_conn() — a distinct
thread-local SQLite connection per thread, so this is a genuine two-connection
race, the same shape as two worker processes.
"""
import os
import sys
import tempfile
import threading
from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent
APP = HERE.parent
sys.path.insert(0, str(APP))

os.environ.setdefault("DB_BACKEND", "sqlite")

import core.config as _cfg  # noqa: E402
_TMP_DB = Path(tempfile.mkdtemp()) / "test_claim.db"
_cfg.DB_PATH = _TMP_DB

import core.db_backend as _dbk  # noqa: E402
_dbk.DB_PATH = _TMP_DB

import core.database as d  # noqa: E402

import pytest  # noqa: E402


@pytest.fixture(scope="module", autouse=True)
def _schema():
    d._init_schema()


def _enqueue(n: int) -> list[str]:
    ids = []
    for i in range(n):
        jid = f"cjob-{i:04d}"
        d._queue_job_record({
            "run_id": jid,
            "agent_id": "agent",
            "project": "proj",
            "task": "t",
            "status": "queued",
            "queued_at": d._now_iso(),
            "job_data": {},
        })
        ids.append(jid)
    return ids


def test_two_threads_claim_disjoint_jobs():
    n = 200
    _enqueue(n)

    claimed: list[str] = []
    lock = threading.Lock()
    barrier = threading.Barrier(2)

    def worker():
        barrier.wait()  # maximize contention: both threads start together
        while True:
            job = d._claim_queued_job()
            if job is None:
                # queue may be transiently empty mid-race; confirm truly drained
                if d._count_queued_jobs() == 0:
                    return
                continue
            with lock:
                claimed.append(job["id"])

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)

    counts = Counter(claimed)
    dupes = {k: v for k, v in counts.items() if v > 1}
    assert not dupes, f"jobs double-claimed: {dupes}"
    assert len(claimed) == n, f"expected {n} unique claims, got {len(claimed)}"
    assert set(counts) == set(f"cjob-{i:04d}" for i in range(n)), "some jobs never claimed"
    # Every job is now 'running' and stamped with a worker id.
    conn = d._db_connection()
    try:
        remaining = conn.execute(
            "SELECT COUNT(*) FROM job_queue WHERE status = 'queued'"
        ).fetchone()[0]
        unstamped = conn.execute(
            "SELECT COUNT(*) FROM job_queue WHERE status='running' AND (worker_id IS NULL OR worker_id='')"
        ).fetchone()[0]
    finally:
        conn.close()
    assert remaining == 0
    assert unstamped == 0
