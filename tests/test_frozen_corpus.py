"""The 100-row corpus freeze for the blind re-code.

METHODOLOGY §6 commits this project to establishing reliability with a blind
re-code: the same evidence, stripped of the proposed stage and its reasoning,
coded cold. The project is currently expanding the reviewed corpus to 100
institutions. Until that milestone, these checks are intentionally dormant so
the human reviewer can add and revise rows through review.py.

Once the 100-row milestone is reached, the maintainer records the hashes below
from that 100-row corpus and the checks become the blind-review freeze. Any
later change then fails the suite until the blind re-code is deliberately
completed.

What is frozen, and what deliberately is NOT:

- `not_classified.json` and `transitions.jsonl` are pinned by SHA-256. Both are
  human-gated, neither is written by an automated pass, so a byte-for-byte pin
  costs nothing.
- `agreement.json` is pinned on its FIGURES only: every key except the two prose
  strings, `_readme` and `limitation`. The file is derived — rebuilt from
  `institutions.json` and `not_classified.json` — and the re-code reads the
  counts, never the caveat wording. A whole-file digest went red the first time
  that caveat was reworded without a single figure moving. The digest below was
  computed at the v1.0.3 tag and again after the rewording and is the same
  either way, so narrowing this pin re-froze nothing.
- `institutions.json` is pinned only on the fields the re-code actually reads —
  `name`, `stage`, `rationale`, `events` — plus its row count. A whole-file
  digest would have gone red the first time monitor.py refreshed a
  `latest_signal`, which is an auto field the re-code never sees. Freezing the
  parts that matter keeps the daily engine runnable.

UNFREEZING is a deliberate act, not a chore: when the re-code is done, delete
this file in the same commit that publishes the result. Re-pinning a digest to
make a red suite green again defeats the entire point of it. Before the target,
the skip below is the expected expansion state.
"""

import hashlib
import json
from pathlib import Path

import pytest

DATA = Path(__file__).resolve().parents[1] / "data"
FREEZE_TARGET_ROWS = 100


def _expansion_phase():
    try:
        rows = json.loads((DATA / "institutions.json").read_text(encoding="utf-8"))
        return len(rows) < FREEZE_TARGET_ROWS
    except (OSError, ValueError, TypeError):
        return False


pytestmark = pytest.mark.skipif(
    _expansion_phase(),
    reason="blind-review freeze activates after the reviewed corpus reaches 100 institutions",
)

# These hashes are the release baseline. At the 100-row milestone, the
# maintainer replaces them with hashes captured from that 100-row corpus once,
# then keeps them fixed for the blind re-code.
FROZEN_FILES = {
    "not_classified.json": "d5b2bcaebebada083c6a84ecd540e32158c0f8cb8a9cd9a52a109d1a2c6cbf4f",
    # Empty file: the panel starts absent and fills prospectively. Its first
    # record will fail this test, which is the correct moment to stop and think
    # about whether the freeze still applies.
    "transitions.jsonl": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
}

# sha256 over agreement.json with the two prose keys dropped, sorted-keys JSON —
# the published figures, and nothing else. Identical at the v1.0.3 tag and after
# the caveat rewording: this pins the released numbers, it is not a re-pin.
AGREEMENT_PROSE_KEYS = ("_readme", "limitation")
AGREEMENT_FIGURES_SHA = "67a44ddb5b6ced88e911edc31ba370303460955295f221c7b42c18e2bd82ce09"

# sha256 over [{name, stage, rationale, events}] sorted-keys JSON. The row count
# is updated to 100 at the milestone; until then the module-level skip keeps the
# historical release values from acting as an expansion gate.
INSTITUTIONS_CORE_SHA = "300c15ffebd0747d07d4c35577d3d07b46937a505e72cb75000f0b23a930bea7"
INSTITUTIONS_ROWS = 84

UNFREEZE = (
    "The 100-row corpus is frozen for the blind re-code (METHODOLOGY §6). If this "
    "change is intentional, say so in the PR and remove tests/test_frozen_corpus.py "
    "in the same commit — do not re-pin the digest."
)


@pytest.mark.parametrize("name,expected", sorted(FROZEN_FILES.items()))
def test_frozen_file_is_unchanged(name, expected):
    actual = hashlib.sha256((DATA / name).read_bytes()).hexdigest()
    assert actual == expected, f"{name} changed. {UNFREEZE}"


def test_agreement_figures_are_unchanged():
    """Prose may be corrected; a figure may not."""
    data = json.loads((DATA / "agreement.json").read_text(encoding="utf-8"))
    for key in AGREEMENT_PROSE_KEYS:
        data.pop(key, None)
    blob = json.dumps(data, ensure_ascii=False, sort_keys=True).encode("utf-8")
    assert hashlib.sha256(blob).hexdigest() == AGREEMENT_FIGURES_SHA, (
        f"an agreement figure changed. {UNFREEZE}"
    )


def test_institutions_recode_inputs_are_unchanged():
    rows = json.loads((DATA / "institutions.json").read_text(encoding="utf-8"))
    assert len(rows) == INSTITUTIONS_ROWS, f"row count changed. {UNFREEZE}"
    core = [
        {"name": r["name"], "stage": r["stage"], "rationale": r["rationale"],
         "events": r["events"]}
        for r in rows
    ]
    blob = json.dumps(core, ensure_ascii=False, sort_keys=True).encode("utf-8")
    assert hashlib.sha256(blob).hexdigest() == INSTITUTIONS_CORE_SHA, (
        f"a stage, rationale or event timeline changed. {UNFREEZE}"
    )


def test_the_roles_module_ships_no_data():
    """The roles module is scaffolding until a human has reviewed real events.

    Shipping an empty file is a claim — "this exists and is empty" — and it is
    the claim this branch is making. A row appearing here without the review
    protocol behind it would be exactly the failure METHODOLOGY §5 exists to
    prevent.
    """
    for name in ("roles.jsonl", "roles_not_found.jsonl"):
        assert (DATA / name).read_text(encoding="utf-8") == "", f"{name} is not empty"
    assert json.loads((DATA / "roles_expansion.json").read_text(encoding="utf-8")) == []
