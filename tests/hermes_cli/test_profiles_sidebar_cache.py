"""Regression tests for dashboard sidebar scan coalescing."""

import inspect
import tempfile
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest import mock

from fastapi import HTTPException

from hermes_cli.web_routers import profiles


class SidebarCacheTests(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch.object(profiles, "_SIDEBAR_CACHE_TTL_SECONDS", 5.0)
        patcher.start()
        self.addCleanup(patcher.stop)
        profiles._sidebar_profile_cache_clear()
        self.addCleanup(profiles._sidebar_profile_cache_clear)

    def test_profile_cache_uses_db_and_wal_fingerprint_and_defensive_copies(self):
        with tempfile.TemporaryDirectory() as root:
            db_path = Path(root) / "state.db"
            wal_path = Path(f"{db_path}-wal")
            db_path.write_bytes(b"db-v1")
            wal_path.write_bytes(b"wal-v1")
            first_fingerprint = profiles._sidebar_db_fingerprint(db_path)
            first_key = (str(db_path), first_fingerprint, False, 0, (), 50, 100, ())
            payload = {"recents": None, "cron": [{"id": "one"}], "messaging": []}

            profiles._sidebar_profile_cache_put(first_key, payload)
            cached = profiles._sidebar_profile_cache_get(first_key)
            cached["cron"][0]["id"] = "mutated"
            self.assertEqual(
                profiles._sidebar_profile_cache_get(first_key)["cron"][0]["id"],
                "one",
            )

            wal_path.write_bytes(b"wal-v2-is-different")
            second_fingerprint = profiles._sidebar_db_fingerprint(db_path)
            second_key = (str(db_path), second_fingerprint, False, 0, (), 50, 100, ())
            self.assertNotEqual(first_fingerprint, second_fingerprint)
            self.assertIsNone(profiles._sidebar_profile_cache_get(second_key))

            profiles._sidebar_profile_cache_put(second_key, payload)
            self.assertIsNone(profiles._sidebar_profile_cache_get(first_key))

    def test_profile_cache_is_lru_bounded(self):
        with mock.patch.object(profiles, "_SIDEBAR_PROFILE_CACHE_MAX_ENTRIES", 2):
            for index in range(3):
                key = (f"/db/{index}", (index, None), False, 0, (), 50, 100, ())
                profiles._sidebar_profile_cache_put(key, {"index": index})
            self.assertEqual(len(profiles._SIDEBAR_PROFILE_CACHE), 2)

    def test_applies_defaults_and_returns_defensive_copies(self):
        calls = 0

        @profiles._sidebar_singleflight_cache
        def scan(profile="all", limit=20):
            nonlocal calls
            calls += 1
            return {"profile": profile, "rows": [{"limit": limit}]}

        first = scan()
        first["rows"][0]["limit"] = 999
        second = scan(profile="all", limit=20)

        self.assertEqual(calls, 1)
        self.assertEqual(second, {"profile": "all", "rows": [{"limit": 20}]})

    def test_coalesces_concurrent_identical_scans(self):
        workers = 12
        entered = threading.Event()
        release = threading.Event()
        calls = 0
        calls_lock = threading.Lock()

        @profiles._sidebar_singleflight_cache
        def scan(profile="all"):
            nonlocal calls
            with calls_lock:
                calls += 1
            entered.set()
            self.assertTrue(release.wait(timeout=2))
            return {"profile": profile, "rows": []}

        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(scan, "default") for _ in range(workers)]
            self.assertTrue(entered.wait(timeout=1))
            time.sleep(0.05)
            release.set()
            results = [future.result(timeout=2) for future in futures]

        self.assertEqual(calls, 1)
        self.assertEqual(results, [{"profile": "default", "rows": []}] * workers)

    def test_expires(self):
        clock = iter((100.0, 100.0, 100.0, 106.0, 106.0, 106.0))
        calls = 0

        @profiles._sidebar_singleflight_cache
        def scan():
            nonlocal calls
            calls += 1
            return {"generation": calls}

        with mock.patch.object(profiles.time, "monotonic", side_effect=clock):
            self.assertEqual(scan(), {"generation": 1})
            self.assertEqual(scan(), {"generation": 2})
        self.assertEqual(calls, 2)

    def test_does_not_cache_failures(self):
        calls = 0

        @profiles._sidebar_singleflight_cache
        def scan():
            nonlocal calls
            calls += 1
            if calls == 1:
                raise RuntimeError("transient")
            return {"ok": True}

        with self.assertRaisesRegex(RuntimeError, "transient"):
            scan()
        self.assertEqual(scan(), {"ok": True})
        self.assertEqual(scan(), {"ok": True})
        self.assertEqual(calls, 2)

    def test_does_not_cache_payloads_that_carry_profile_errors(self):
        # A 200 with a non-empty errors[] is how a failed profile scan is
        # reported. Caching it for the TTL keeps the empty recents page in
        # front of a store that has already recovered.
        calls = 0

        @profiles._sidebar_singleflight_cache
        def scan():
            nonlocal calls
            calls += 1
            if calls == 1:
                return {
                    "errors": [{"profile": "default", "error": "disk I/O error"}],
                    "recents": {"sessions": []},
                }
            return {"errors": [], "recents": {"sessions": [{"id": "yesterday"}]}}

        first = scan()
        second = scan()

        self.assertEqual(first["errors"][0]["error"], "disk I/O error")
        self.assertEqual(second["recents"]["sessions"], [{"id": "yesterday"}])
        self.assertEqual(calls, 2)

    def test_can_be_disabled(self):
        calls = 0

        @profiles._sidebar_singleflight_cache
        def scan():
            nonlocal calls
            calls += 1
            return calls

        with mock.patch.object(profiles, "_SIDEBAR_CACHE_TTL_SECONDS", 0.0):
            self.assertEqual((scan(), scan()), (1, 2))

    def test_a_poll_arriving_mid_refresh_is_served_the_previous_scan(self):
        """The fix for #140412. A refresh opens every profile's state.db, so against a multi-GB
        store it outruns the desktop's poll interval by a long way. Waiting for it costs an AnyIO
        worker, the pool is 40 wide for the whole API, and 36 parked workers starved the uvicorn
        loop until the shutdown watchdog exited 75 -- which the desktop reports as a disconnect.
        So a poll that lands mid-refresh answers from the scan being replaced and returns its
        worker immediately."""
        clock = [1000.0]
        entered, release = threading.Event(), threading.Event()
        calls = []

        @profiles._sidebar_singleflight_cache
        def scan():
            calls.append(None)
            if len(calls) > 1:  # only the second scan is the slow one being overtaken
                entered.set()
                self.assertTrue(release.wait(timeout=10))
            return {"generation": len(calls)}

        before = profiles._SIDEBAR_STALE_STATS["served"]
        # Patching time.monotonic also patches it for this test body, so wall-clock
        # assertions below use perf_counter. threading.Event is unaffected either way.
        with mock.patch.object(profiles.time, "monotonic", lambda: clock[0]):
            self.assertEqual(scan(), {"generation": 1})
            clock[0] += profiles._SIDEBAR_CACHE_TTL_SECONDS + 1.0  # the TTL lapses
            slow = threading.Thread(target=scan, daemon=True)
            slow.start()
            self.assertTrue(entered.wait(timeout=10), "the second scan must be in flight")
            started = time.perf_counter()
            served = scan()
            elapsed = time.perf_counter() - started
            release.set()
            slow.join(timeout=10)

        self.assertEqual(served, {"generation": 1},
                         "the superseded scan must answer while its replacement runs")
        self.assertLess(elapsed, 1.0, "a mid-refresh poll must not park a worker thread")
        self.assertEqual(len(calls), 2, "and must not start a third scan of its own")
        self.assertEqual(profiles._SIDEBAR_STALE_STATS["served"], before + 1)

    def test_a_caller_with_nothing_to_serve_sheds_rather_than_hold_a_worker(self):
        """Cold start, scan already running, waiter budget gone: the pool matters more than this
        one response, so it sheds with a retryable 503 instead of blocking."""
        entered, release = threading.Event(), threading.Event()

        @profiles._sidebar_singleflight_cache
        def scan():
            entered.set()
            self.assertTrue(release.wait(timeout=10))
            return {"rows": []}

        exhausted = threading.BoundedSemaphore(1)
        self.assertTrue(exhausted.acquire(blocking=False))
        holder = threading.Thread(target=scan, daemon=True)
        holder.start()
        try:
            self.assertTrue(entered.wait(timeout=10))
            before = profiles._SIDEBAR_STALE_STATS["shed"]
            with mock.patch.object(profiles, "_SIDEBAR_WAITERS", exhausted):
                started = time.perf_counter()
                with self.assertRaises(HTTPException) as caught:
                    scan()
                elapsed = time.perf_counter() - started
        finally:
            release.set()
            holder.join(timeout=10)

        self.assertEqual(caught.exception.status_code, 503)
        self.assertEqual(caught.exception.headers.get("Retry-After"), "1")
        self.assertLess(elapsed, 1.0, "shedding must be immediate, not a timed-out wait")
        self.assertEqual(profiles._SIDEBAR_STALE_STATS["shed"], before + 1)

    def test_a_snapshot_too_old_to_stand_in_is_not_served(self):
        """The grace window is what keeps 'stale' honest: past it the entry stops answering, so a
        gateway that has been wedged for an hour cannot keep handing back an hour-old sidebar."""
        clock = [1000.0]
        entered, release = threading.Event(), threading.Event()
        calls = []

        @profiles._sidebar_singleflight_cache
        def scan():
            calls.append(None)
            if len(calls) > 1:
                entered.set()
                self.assertTrue(release.wait(timeout=10))
            return {"generation": len(calls)}

        exhausted = threading.BoundedSemaphore(1)
        self.assertTrue(exhausted.acquire(blocking=False))
        with mock.patch.object(profiles.time, "monotonic", lambda: clock[0]):
            self.assertEqual(scan(), {"generation": 1})
            clock[0] += profiles._SIDEBAR_STALE_GRACE_SECONDS + 1.0
            slow = threading.Thread(target=scan, daemon=True)
            slow.start()
            try:
                self.assertTrue(entered.wait(timeout=10))
                with mock.patch.object(profiles, "_SIDEBAR_WAITERS", exhausted):
                    with self.assertRaises(HTTPException) as caught:
                        scan()
            finally:
                release.set()
                slow.join(timeout=10)

        self.assertEqual(caught.exception.status_code, 503,
                         "an expired-past-grace entry must not be served as a stand-in")

    def test_entries_past_the_grace_window_are_dropped_on_the_next_store(self):
        """`_lookup` stopped popping expired entries so they can stand in for a running scan;
        these snapshots are whole project trees, so the ones that can no longer do that have to
        go, or the cache just accumulates them."""
        clock = [1000.0]

        @profiles._sidebar_singleflight_cache
        def scan(profile="all"):
            return {"profile": profile}

        with mock.patch.object(profiles.time, "monotonic", lambda: clock[0]):
            scan(profile="one")
            clock[0] += profiles._SIDEBAR_STALE_GRACE_SECONDS + 1.0
            scan(profile="two")

        self.assertEqual([dict(key)["profile"] for key in scan._sidebar_cache], ["two"],
                         "the entry too old to stand in for a scan must not be retained")

    def test_preserves_fastapi_signature(self):
        def scan(profile: str = "all", limit: int = 20):
            return profile, limit

        wrapped = profiles._sidebar_singleflight_cache(scan)

        self.assertEqual(inspect.signature(wrapped), inspect.signature(scan))



if __name__ == "__main__":
    unittest.main()
