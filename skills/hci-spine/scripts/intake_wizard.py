#!/usr/bin/env python3
"""Interactive intake wizard for the hci-spine skill.

Writes hci_spine_output/hci_spine_config.json (+ .md) from an interactive
terminal session. Three modes:

  --keyboard-ui   curses arrow-key TUI (used by launch_hci_spine_ui.sh in an
                  external Terminal window). Falls back to --in-place if curses
                  is unavailable or stdin is not a tty.
  --in-place      numbered prompts in the current terminal (default when run
                  directly).
  --print-defaults  write a default config without prompting (smoke test / CI).

The primary_form field is intentionally FIRST: hci-spine routes on contribution
FORM (kept separate from area/tradition/venue) before anything else.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

CONTRIBUTION_FORMS = (
    "empirical", "artifact", "method", "conceptual_theoretical",
    "dataset_corpus", "critical_artistic", "replication",
)
SECONDARY_FORMS = ("none",) + CONTRIBUTION_FORMS  # "none" == single-form paper
# `undecided` is a valid PRIMARY choice during the exploratory forge phase; the form
# is committed at `lock`. It is NOT a real form (no playbook), so it is offered only
# for the primary slot and forbids a secondary.
PRIMARY_FORM_CHOICES = ("undecided",) + CONTRIBUTION_FORMS
WORKFLOWS = ("from_idea", "build_from_materials", "rewrite_existing")
TIERS = ("flash", "pro")
LANGUAGES = ("zh", "en")
REFERENCE_MODES = ("local_first", "specified_paths", "web")
CODEX_ROLES = ("review", "dual_write", "cite_verify", "data_audit")

# Suggested default Codex roles per PRIMARY FORM (SKILL.md "Codex Integration").
DEFAULT_CODEX_ROLES = {
    "undecided": ["review"],
    "empirical": ["data_audit", "cite_verify"],
    "artifact": ["review"],
    "method": ["review", "cite_verify"],
    "conceptual_theoretical": ["review"],
    "dataset_corpus": ["data_audit", "cite_verify"],
    "critical_artistic": ["review"],
    "replication": ["data_audit", "cite_verify"],
}

CHOICE_HELP = {
    "primary_form": {
        "undecided": "forge 阶段未定;lock 后再选(from_idea 默认)",
        "empirical": "对人/使用的论断,证据来自研究 (study design+分析+findings)",
        "artifact": "做出来的东西即贡献:系统/工具/技术/设计物 (why-hard+评估)",
        "method": "新的研究/设计做法即贡献 (需验证,不只是提出)",
        "conceptual_theoretical": "概念/框架/理论/设计空间 (需 grounding+可生成)",
        "dataset_corpus": "数据集/语料/基准 (provenance+ethics+datasheet)",
        "critical_artistic": "批判/思辨/艺术贡献 (provocation+定位+反思)",
        "replication": "复现/重复前人工作 (fidelity+诚实报告无论结果)",
    },
    "secondary_form": {"none": "单一形式;选一个则启用可执行的 mixed(主+次合并)"},
    "workflow": {
        "from_idea": "从一个(可能模糊的)想法开始,先过 idea-discovery/research-refine",
        "build_from_materials": "从素材文件夹(研究数据、日志、图、笔记)从零构筑",
        "rewrite_existing": "改进/重写一份已有初稿",
    },
    "tier": {"flash": "快速档", "pro": "完整档(更多研究/评审轮次)"},
    "output_language": {"zh": "中文", "en": "English"},
    "reference_mode": {
        "local_first": "先索引本地参考,再用网络补缺(推荐)",
        "specified_paths": "只用指定路径的参考",
        "web": "主要靠网络检索",
    },
}

CHOICE_FIELDS = {
    "primary_form": PRIMARY_FORM_CHOICES,
    "secondary_form": SECONDARY_FORMS,
    "workflow": WORKFLOWS,
    "tier": TIERS,
    "output_language": LANGUAGES,
    "reference_mode": REFERENCE_MODES,
}

TEXT_FIELDS = ("research_area", "tradition", "venue", "materials_dir", "draft_path", "user_motivation", "reference_paths")
INT_FIELDS = ("citation_target_count",)

FIELD_ORDER = (
    "primary_form",
    "secondary_form",
    "research_area",
    "tradition",
    "workflow",
    "venue",
    "tier",
    "output_language",
    "materials_dir",
    "draft_path",
    "user_motivation",
    "codex_roles",
    "reference_mode",
    "reference_paths",
    "citation_target_count",
)


@dataclass
class Config:
    primary_form: str = "undecided"
    secondary_form: str = "none"
    research_area: str = ""
    tradition: str = ""
    workflow: str = "build_from_materials"
    venue: str = ""
    tier: str = "pro"
    output_language: str = "zh"
    materials_dir: str = ""
    draft_path: str = ""
    user_motivation: str = ""
    codex_roles: list = field(default_factory=lambda: ["review"])
    reference_mode: str = "local_first"
    reference_paths: list = field(default_factory=lambda: ["."])
    citation_target_count: int = 25

    def as_dict(self) -> dict:
        return {k: getattr(self, k) for k in FIELD_ORDER}


def validate_config(cfg) -> list:
    """Return a list of human-readable validation errors ([] == valid).

    Accepts a Config or a plain dict. Enforces: closed-enum membership for choice
    fields, non-empty codex_roles all drawn from CODEX_ROLES, reference_paths a
    non-empty list, citation_target_count a positive int.
    """
    d = cfg.as_dict() if isinstance(cfg, Config) else dict(cfg)
    errors: list = []
    for field_name, allowed in CHOICE_FIELDS.items():
        val = d.get(field_name)
        if val not in allowed:
            errors.append(f"{field_name}={val!r} not in {allowed}")
    if d.get("secondary_form") not in (None, "none") and d.get("secondary_form") == d.get("primary_form"):
        errors.append("secondary_form must differ from primary_form (or be 'none')")
    if d.get("primary_form") == "undecided" and d.get("secondary_form") not in (None, "none"):
        errors.append("primary_form=undecided cannot carry a secondary_form (choose the form at lock)")
    roles = d.get("codex_roles") or []
    if not isinstance(roles, list) or not roles:
        errors.append("codex_roles must be a non-empty list")
    else:
        bad = [r for r in roles if r not in CODEX_ROLES]
        if bad:
            errors.append(f"codex_roles has unknown values {bad}; allowed {CODEX_ROLES}")
        if len(set(roles)) != len(roles):
            errors.append("codex_roles has duplicates")
    rp = d.get("reference_paths")
    if not isinstance(rp, list) or not rp:
        errors.append("reference_paths must be a non-empty list")
    ctc = d.get("citation_target_count")
    if not isinstance(ctc, int) or isinstance(ctc, bool) or ctc <= 0:
        errors.append(f"citation_target_count must be a positive int, got {ctc!r}")
    return errors


# --------------------------------------------------------------------------- #
# Output writers
# --------------------------------------------------------------------------- #
def write_config(cfg: Config, output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "hci_spine_config.json"
    md_path = output_dir / "hci_spine_config.md"
    json_path.write_text(json.dumps(cfg.as_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    rows = "\n".join(
        f"| `{k}` | {format_value(getattr(cfg, k))} |" for k in FIELD_ORDER
    )
    md = (
        "# hci-spine configuration\n\n"
        "| Field | Value |\n|---|---|\n"
        f"{rows}\n\n"
        f"Contribution form **{cfg.primary_form}**"
        + (f" + **{cfg.secondary_form}** (mixed)" if cfg.secondary_form != "none" else "")
        + " — playbook loaded from "
        "`references/contribution-form-playbooks.md`.\n"
    )
    md_path.write_text(md, encoding="utf-8")
    return json_path, md_path


def format_value(v) -> str:
    if isinstance(v, list):
        return ", ".join(v) if v else "(none)"
    return str(v) if v != "" else "(empty)"


# --------------------------------------------------------------------------- #
# In-place numbered prompts
# --------------------------------------------------------------------------- #
def ask_choice(name: str, options: tuple, default: str) -> str:
    print(f"\n{name}:")
    for i, opt in enumerate(options, 1):
        helptext = CHOICE_HELP.get(name, {}).get(opt, "")
        marker = " (默认)" if opt == default else ""
        print(f"  {i}. {opt}{marker}  {('- ' + helptext) if helptext else ''}")
    raw = input(f"选择 1-{len(options)} [回车=默认 {default}]: ").strip()
    if not raw:
        return default
    try:
        idx = int(raw) - 1
        if 0 <= idx < len(options):
            return options[idx]
    except ValueError:
        pass
    print("  无效输入,使用默认。")
    return default


def ask_text(name: str, default: str) -> str:
    raw = input(f"\n{name} [回车=「{default or '空'}」]: ").strip()
    return raw if raw else default


def ask_int(name: str, default: int) -> int:
    raw = input(f"\n{name} [回车=默认 {default}]: ").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        print("  无效数字,使用默认。")
        return default


def ask_codex_roles(default: list) -> list:
    print("\ncodex_roles (Codex 角色,可多选):")
    for i, role in enumerate(CODEX_ROLES, 1):
        print(f"  {i}. {role}")
    print("  review=跨模型审稿 · dual_write=双写对照 · cite_verify=引用核验 · data_audit=数据审计")
    raw = input(f"输入编号,逗号分隔 [回车=默认 {','.join(default)}]: ").strip()
    if not raw:
        return default
    chosen = []
    for tok in raw.split(","):
        tok = tok.strip()
        try:
            idx = int(tok) - 1
            if 0 <= idx < len(CODEX_ROLES) and CODEX_ROLES[idx] not in chosen:
                chosen.append(CODEX_ROLES[idx])
        except ValueError:
            continue
    return chosen or default


def run_in_place(output_dir: Path) -> Config:
    print("=" * 60)
    print("  hci-spine intake — HCI 论文全流程配置")
    print("=" * 60)
    cfg = Config()
    cfg.primary_form = ask_choice("primary_form", PRIMARY_FORM_CHOICES, cfg.primary_form)
    # Re-default codex roles based on the chosen primary form before asking.
    cfg.codex_roles = DEFAULT_CODEX_ROLES.get(cfg.primary_form, ["review"])
    cfg.secondary_form = ask_choice("secondary_form", SECONDARY_FORMS, cfg.secondary_form)
    cfg.research_area = ask_text("research_area (如 human-AI interaction / tangible)", cfg.research_area)
    cfg.tradition = ask_text("tradition (如 systems-building / research-through-design)", cfg.tradition)
    cfg.workflow = ask_choice("workflow", WORKFLOWS, cfg.workflow)
    cfg.venue = ask_text("venue (如 TEI 2027 / CHI 2027)", cfg.venue)
    cfg.tier = ask_choice("tier", TIERS, cfg.tier)
    cfg.output_language = ask_choice("output_language", LANGUAGES, cfg.output_language)
    cfg.materials_dir = ask_text("materials_dir (素材文件夹路径)", cfg.materials_dir)
    cfg.draft_path = ask_text("draft_path (已有初稿路径,可空)", cfg.draft_path)
    cfg.user_motivation = ask_text("user_motivation (一句话动机,可空)", cfg.user_motivation)
    cfg.codex_roles = ask_codex_roles(cfg.codex_roles)
    cfg.reference_mode = ask_choice("reference_mode", REFERENCE_MODES, cfg.reference_mode)
    ref = ask_text("reference_paths (逗号分隔,默认当前目录)", ".")
    cfg.reference_paths = [p.strip() for p in ref.split(",") if p.strip()] or ["."]
    cfg.citation_target_count = ask_int("citation_target_count", cfg.citation_target_count)
    return cfg


# --------------------------------------------------------------------------- #
# curses keyboard UI (optional; degrades to in-place)
# --------------------------------------------------------------------------- #
def run_keyboard_ui(output_dir: Path) -> Config:
    try:
        import curses
    except Exception:
        return run_in_place(output_dir)
    if not sys.stdin.isatty():
        return run_in_place(output_dir)

    cfg = Config()

    def _ui(stdscr):
        curses.curs_set(0)
        idx = 0
        choice_pos = {}
        while True:
            stdscr.clear()
            h, w = stdscr.getmaxyx()
            stdscr.addstr(0, 2, "hci-spine intake — ↑/↓ 选字段 · ←/→ 改选项 · Enter 编辑文本 · S 保存 · Q 退出", curses.A_BOLD)
            for row, name in enumerate(FIELD_ORDER, start=2):
                sel = "→ " if row - 2 == idx else "  "
                val = format_value(getattr(cfg, name))
                attr = curses.A_REVERSE if row - 2 == idx else curses.A_NORMAL
                stdscr.addstr(row, 2, f"{sel}{name:22} {val[:w-30]}", attr)
            name = FIELD_ORDER[idx]
            help_lines = []
            if name in CHOICE_FIELDS:
                for opt in CHOICE_FIELDS[name]:
                    help_lines.append(f"  {opt}: {CHOICE_HELP.get(name, {}).get(opt, '')}")
            elif name == "codex_roles":
                help_lines = [f"  {r}" for r in CODEX_ROLES] + ["  (Enter 输入逗号分隔编号)"]
            base = len(FIELD_ORDER) + 4
            for j, line in enumerate(help_lines[: h - base - 1]):
                stdscr.addstr(base + j, 2, line[: w - 4])
            stdscr.refresh()

            key = stdscr.getch()
            if key in (ord("q"), ord("Q")):
                raise KeyboardInterrupt
            if key in (ord("s"), ord("S")):
                return
            if key == curses.KEY_UP:
                idx = (idx - 1) % len(FIELD_ORDER)
            elif key == curses.KEY_DOWN:
                idx = (idx + 1) % len(FIELD_ORDER)
            elif key in (curses.KEY_LEFT, curses.KEY_RIGHT) and name in CHOICE_FIELDS:
                opts = CHOICE_FIELDS[name]
                cur = opts.index(getattr(cfg, name))
                cur = (cur + (1 if key == curses.KEY_RIGHT else -1)) % len(opts)
                setattr(cfg, name, opts[cur])
                if name == "primary_form":
                    cfg.codex_roles = DEFAULT_CODEX_ROLES.get(opts[cur], ["review"])
            elif key in (curses.KEY_ENTER, 10, 13):
                curses.echo()
                curses.curs_set(1)
                stdscr.addstr(h - 1, 2, f"{name} = ")
                stdscr.clrtoeol()
                raw = stdscr.getstr(h - 1, len(name) + 5).decode("utf-8").strip()
                curses.noecho()
                curses.curs_set(0)
                if name in INT_FIELDS:
                    try:
                        setattr(cfg, name, int(raw))
                    except ValueError:
                        pass
                elif name == "reference_paths":
                    cfg.reference_paths = [p.strip() for p in raw.split(",") if p.strip()] or ["."]
                elif name == "codex_roles":
                    chosen = []
                    for tok in raw.split(","):
                        try:
                            k = int(tok.strip()) - 1
                            if 0 <= k < len(CODEX_ROLES) and CODEX_ROLES[k] not in chosen:
                                chosen.append(CODEX_ROLES[k])
                        except ValueError:
                            continue
                    if chosen:
                        cfg.codex_roles = chosen
                elif raw:
                    setattr(cfg, name, raw)

    try:
        curses.wrapper(_ui)
    except KeyboardInterrupt:
        print("已取消,未保存。")
        sys.exit(1)
    return cfg


# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser(description="hci-spine intake wizard")
    ap.add_argument("--output-dir", default="hci_spine_output")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--keyboard-ui", action="store_true")
    mode.add_argument("--in-place", action="store_true")
    mode.add_argument("--print-defaults", action="store_true", help="write defaults without prompting")
    args = ap.parse_args()
    output_dir = Path(args.output_dir)

    if args.print_defaults:
        cfg = Config()
    elif args.keyboard_ui:
        cfg = run_keyboard_ui(output_dir)
    else:
        cfg = run_in_place(output_dir)

    errors = validate_config(cfg)
    if errors:
        print("\n⚠ 配置校验未通过:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 2

    json_path, md_path = write_config(cfg, output_dir)
    print(f"\n✅ 写入:\n  {json_path}\n  {md_path}")
    sec = "" if cfg.secondary_form == "none" else f" + {cfg.secondary_form}"
    print(f"\nprimary_form = {cfg.primary_form}{sec} → 加载对应 playbook。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
