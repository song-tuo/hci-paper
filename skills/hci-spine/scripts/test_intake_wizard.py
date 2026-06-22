#!/usr/bin/env python3
"""Field-validation tests for intake_wizard.py. Run: python3 test_intake_wizard.py
No pytest dependency — plain asserts + a tiny runner."""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import intake_wizard as iw  # noqa: E402

PASS = 0
FAIL = 0


def check(name, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✓ {name}")
    else:
        FAIL += 1
        print(f"  ✗ {name}")


def main():
    print("== intake_wizard field-validation tests ==")

    # defaults are valid
    cfg = iw.Config()
    check("default Config validates clean", iw.validate_config(cfg) == [])

    # every contribution FORM (+ undecided) has a codex-roles default
    check("DEFAULT_CODEX_ROLES covers all forms + undecided",
          set(iw.CONTRIBUTION_FORMS).issubset(iw.DEFAULT_CODEX_ROLES) and "undecided" in iw.DEFAULT_CODEX_ROLES)

    # default config is 'undecided' (from_idea-safe) and validates clean
    check("default primary_form is undecided", cfg.primary_form == "undecided")
    check("undecided default validates clean", iw.validate_config(cfg) == [])

    # undecided cannot carry a secondary form
    bad_u = iw.Config(); bad_u.primary_form = "undecided"; bad_u.secondary_form = "empirical"
    check("undecided + secondary rejected", any("undecided" in e for e in iw.validate_config(bad_u)))

    # as_dict carries every declared field
    check("as_dict has all FIELD_ORDER keys",
          set(cfg.as_dict().keys()) == set(iw.FIELD_ORDER))

    # bad enum value is caught
    bad = iw.Config(); bad.primary_form = "aihci"   # aihci is an AREA, not a form
    errs = iw.validate_config(bad)
    check("bad primary_form rejected (aihci is an area)", any("primary_form" in e for e in errs))

    # secondary_form must differ from primary (executable mixed)
    badm = iw.Config(); badm.primary_form = "artifact"; badm.secondary_form = "artifact"
    check("secondary==primary rejected", any("secondary_form" in e for e in iw.validate_config(badm)))

    # valid mixed config passes
    mix = iw.Config(); mix.primary_form = "artifact"; mix.secondary_form = "empirical"
    check("valid mixed (artifact+empirical) validates", iw.validate_config(mix) == [])

    # bad codex role caught
    bad2 = iw.Config(); bad2.codex_roles = ["review", "make_coffee"]
    check("unknown codex role rejected", any("codex_roles" in e for e in iw.validate_config(bad2)))

    # empty codex_roles caught
    bad3 = iw.Config(); bad3.codex_roles = []
    check("empty codex_roles rejected", any("codex_roles" in e for e in iw.validate_config(bad3)))

    # duplicate codex roles caught
    bad4 = iw.Config(); bad4.codex_roles = ["review", "review"]
    check("duplicate codex roles rejected", any("duplicate" in e for e in iw.validate_config(bad4)))

    # non-positive citation count caught
    bad5 = iw.Config(); bad5.citation_target_count = 0
    check("citation_target_count<=0 rejected", any("citation_target_count" in e for e in iw.validate_config(bad5)))

    # bool is not accepted as int (Python gotcha)
    bad6 = iw.Config(); bad6.citation_target_count = True
    check("bool citation_target_count rejected", any("citation_target_count" in e for e in iw.validate_config(bad6)))

    # empty reference_paths caught
    bad7 = iw.Config(); bad7.reference_paths = []
    check("empty reference_paths rejected", any("reference_paths" in e for e in iw.validate_config(bad7)))

    # validate_config accepts a plain dict too
    check("validate_config accepts dict", iw.validate_config(cfg.as_dict()) == [])

    # write_config round-trips valid JSON with all keys
    with tempfile.TemporaryDirectory() as d:
        jp, mp = iw.write_config(cfg, Path(d))
        loaded = json.loads(Path(jp).read_text(encoding="utf-8"))
        check("written JSON parses + has all keys", set(loaded) == set(iw.FIELD_ORDER))
        check("written md exists", Path(mp).is_file())

    print(f"\n== {PASS} passed, {FAIL} failed ==")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
