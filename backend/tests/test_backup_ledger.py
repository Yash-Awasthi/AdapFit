"""A restore replays only erasure events newer than the dump, the last one per account winning."""
from scripts.backup import pending_erasures


def test_pending_erasures_after_dump():
    live = [[5, "account_erased", "old"], [15, "deletion_requested", "a"], [16, "deletion_cancelled", "a"],
            [17, "deletion_requested", "b"], [18, "account_erased", "c"]]
    newer_dump = [[17, "deletion_requested", "b"], [12, "account_erased", "d"]]
    assert pending_erasures(10, [live, newer_dump]) == {"b": "deletion_requested", "c": "account_erased",
                                                        "d": "account_erased"}
