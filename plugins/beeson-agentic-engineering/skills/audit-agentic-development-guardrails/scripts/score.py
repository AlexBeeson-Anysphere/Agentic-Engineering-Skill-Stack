#!/usr/bin/env python3
"""Score an agentic-development guardrails audit and render its report.

Usage:
  score.py template [--repo ROOT] [--out scores.json]
  score.py rubric [--category A,T]
  score.py validate SCORES
  score.py report SCORES [--discover DISCOVER_JSON] [--out report.md] [--json result.json]

rubric.json in the skill directory is the single source of truth for items, anchors,
category weights, and level gates. All arithmetic happens here, so the auditing agent
never computes totals or the level by hand. Stdlib only.
"""
import argparse
import datetime
import json
import os
import subprocess
import sys
from collections import defaultdict

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUBRIC_PATH = os.path.join(SKILL_DIR, "rubric.json")
EVIDENCE_KINDS = ("ran", "cited", "attested", "searched")
ESCAPE_CAP = 2
VALID_SCORES = (0, 1, 2, 3, 4)


def git(root, *args):
    try:
        out = subprocess.run(["git", "-C", root, *args], capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return out.stdout.strip() if out.returncode == 0 else None


def req_ids(req):
    return list(req["any_of"]) if "any_of" in req else [req["item"]]


def check_rubric(rubric):
    errors = []
    cat_ids = [c["id"] for c in rubric["categories"]]
    if len(set(cat_ids)) != len(cat_ids):
        errors.append("duplicate category ids")
    total = sum(c["weight"] for c in rubric["categories"])
    if total != 100:
        errors.append(f"category weights sum to {total}, expected 100")
    item_ids = [i["id"] for i in rubric["items"]]
    if len(set(item_ids)) != len(item_ids):
        errors.append("duplicate item ids")
    for item in rubric["items"]:
        if item["category"] not in cat_ids:
            errors.append(f"{item['id']}: unknown category {item['category']}")
        if "anchors" in item:
            if set(item["anchors"]) != {"0", "1", "2", "3", "4"}:
                errors.append(f"{item['id']}: anchors must define 0 through 4")
        elif not item.get("hard_gate"):
            errors.append(f"{item['id']}: needs either anchors or hard_gate")
    for cid in cat_ids:
        if not any(i["category"] == cid for i in rubric["items"]):
            errors.append(f"category {cid} has no items")
    levels = sorted(rubric["levels"], key=lambda lvl: lvl["level"])
    if [lvl["level"] for lvl in levels] != list(range(len(levels))):
        errors.append("levels must be numbered 0..N without gaps")
    for lvl in levels:
        for req in lvl["gates"]:
            for iid in req_ids(req):
                if iid not in item_ids:
                    errors.append(f"level {lvl['level']} gate references unknown item {iid}")
    return errors


def load_rubric():
    with open(RUBRIC_PATH) as f:
        rubric = json.load(f)
    errors = check_rubric(rubric)
    if errors:
        sys.exit("rubric.json is inconsistent:\n" + "\n".join(f"  - {e}" for e in errors))
    rubric["levels"] = sorted(rubric["levels"], key=lambda lvl: lvl["level"])
    return rubric


def gate_items(rubric):
    """Map item id -> (level, min) for every item a level gate depends on."""
    out = {}
    for lvl in rubric["levels"]:
        for req in lvl["gates"]:
            for iid in req_ids(req):
                out.setdefault(iid, (lvl["level"], req["min"]))
    return out


def anchor_text(rubric, item, score):
    if "anchors" in item:
        return item["anchors"][str(score)]
    if score == 3:
        return item["hard_gate"]
    return rubric["scale"][str(score)]["meaning"]


def load_json(path):
    with open(path) as f:
        return json.load(f)


# ---------------------------------------------------------------- template / rubric


def cmd_template(args):
    rubric = load_rubric()
    repo = {"name": "", "root": "", "commit": "", "branch": ""}
    if args.repo:
        root = os.path.abspath(args.repo)
        repo = {
            "name": os.path.basename(root),
            "root": root,
            "commit": git(root, "rev-parse", "--short", "HEAD") or "nogit",
            "branch": git(root, "rev-parse", "--abbrev-ref", "HEAD") or "",
        }
    doc = {
        "rubric_version": rubric["version"],
        "repo": repo,
        "audited_at": datetime.date.today().isoformat(),
        "auditor": "",
        "scope": "whole repository",
        "window": "",
        "summary": "",
        "level_rationale": "",
        "items": {
            i["id"]: {"score": None, "rationale": "", "evidence": [], "na_reason": None, "next_step": ""}
            for i in rubric["items"]
        },
        "escapes": [],
        "limits": [],
    }
    text = json.dumps(doc, indent=2) + "\n"
    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w") as f:
            f.write(text)
        print(f"Wrote {args.out} with {len(rubric['items'])} items to score.")
    else:
        sys.stdout.write(text)


def cmd_rubric(args):
    rubric = load_rubric()
    wanted = set(args.category.split(",")) if args.category else None
    gates = gate_items(rubric)
    out = [f"# Guardrails rubric v{rubric['version']}", "", "## Scale (items without their own anchors)", ""]
    for k in sorted(rubric["scale"]):
        s = rubric["scale"][k]
        out.append(f"- **{k} {s['name']}:** {s['meaning']}")
    out += ["", "## Agent habits each item defeats", ""]
    out += [f"- **{k}:** {v}" for k, v in rubric["habits"].items()]
    out += ["", "## Levels", ""]
    for lvl in rubric["levels"]:
        reqs = "; ".join(f"{' or '.join(req_ids(r))} >= {r['min']}" for r in lvl["gates"]) or "none"
        out.append(f"- **Level {lvl['level']}, {lvl['name']}.** {lvl['description']} Gates: {reqs}.")
    for cat in rubric["categories"]:
        if wanted and cat["id"] not in wanted:
            continue
        out += ["", f"## {cat['id']}. {cat['name']} (weight {cat['weight']})", "", cat["why"]]
        for item in rubric["items"]:
            if item["category"] != cat["id"]:
                continue
            out += ["", f"### {item['id']} {item['name']}", ""]
            if item["id"] in gates:
                lvl, mn = gates[item["id"]]
                out.append(f"- **Level {lvl} gate item:** needs {mn} or higher.")
            out.append(f"- **Defeats:** {item['defeats']}. **Source:** {item['source']}.")
            out.append(f"- **Look for:** {item['look_for']}")
            if "anchors" in item:
                for k in sorted(item["anchors"]):
                    out.append(f"  - **{k}:** {item['anchors'][k]}")
            else:
                out.append(f"- **Hard gate (3):** {item['hard_gate']}")
            if item.get("proof") == "runtime":
                out.append("- **Proof:** 3 or higher needs `ran` or `attested` evidence; config alone can't show it.")
            out.append(f"- **N/A when:** {item['na_when'] or 'never; score it.'}")
    sys.stdout.write("\n".join(out) + "\n")


# ---------------------------------------------------------------- validate


def validate(rubric, doc):
    errors, warnings = [], []
    items = {i["id"]: i for i in rubric["items"]}
    if doc.get("rubric_version") != rubric["version"]:
        errors.append(f"rubric_version is {doc.get('rubric_version')!r}, expected {rubric['version']!r}")
    entries = doc.get("items") or {}
    for iid in items:
        if iid not in entries:
            errors.append(f"{iid}: missing from items")
    for iid in entries:
        if iid not in items:
            errors.append(f"{iid}: not a rubric item")
    for iid, e in entries.items():
        if iid not in items:
            continue
        item = items[iid]
        s = e.get("score")
        if isinstance(s, bool) or (s not in VALID_SCORES and s != "na"):
            errors.append(f"{iid}: score must be 0-4 or \"na\", got {s!r}")
            continue
        if not str(e.get("rationale") or "").strip():
            errors.append(f"{iid}: rationale is empty")
        evidence = e.get("evidence") or []
        for k, ev in enumerate(evidence):
            if ev.get("kind") not in EVIDENCE_KINDS:
                errors.append(f"{iid}: evidence[{k}] kind must be one of {', '.join(EVIDENCE_KINDS)}")
            if not str(ev.get("ref") or "").strip():
                errors.append(f"{iid}: evidence[{k}] needs a ref (file:line, command, URL, or search)")
            if ev.get("kind") == "attested" and not str(ev.get("by") or "").strip():
                errors.append(f"{iid}: evidence[{k}] is attested, so it needs 'by' (who attested)")
        kinds = {ev.get("kind") for ev in evidence}
        if s == "na":
            if not str(e.get("na_reason") or "").strip():
                errors.append(f"{iid}: N/A needs na_reason")
            if item.get("na_when") is None:
                warnings.append(f"{iid}: the rubric never expects N/A for this item, so the reason must be strong")
            continue
        if not evidence:
            errors.append(f"{iid}: needs evidence; for a 0, add a 'searched' entry naming where you looked")
        elif s >= 1 and not kinds & {"ran", "cited", "attested"}:
            errors.append(f"{iid}: a score above 0 needs ran, cited, or attested evidence")
        if s == 4 and "anchors" not in item and "ran" not in kinds:
            errors.append(f"{iid}: 4 means the gate is proven to bite, so it needs 'ran' evidence (probe or canary run)")
        if item.get("proof") == "runtime" and s >= 3 and not kinds & {"ran", "attested"}:
            errors.append(f"{iid}: 3 or higher needs 'ran' or 'attested' evidence; config alone can't show it")
        if s < 4 and not str(e.get("next_step") or "").strip():
            warnings.append(f"{iid}: no next_step; the roadmap will fall back to the next anchor")
    for k, esc in enumerate(doc.get("escapes") or []):
        if not str(esc.get("class") or "").strip():
            errors.append(f"escapes[{k}]: needs a class")
        occ = esc.get("occurrences")
        if isinstance(occ, bool) or not isinstance(occ, int) or occ < 2:
            errors.append(f"escapes[{k}]: occurrences must be an integer of 2 or more; one-offs aren't escapes")
        if esc.get("item") is not None and esc.get("item") not in items:
            errors.append(f"escapes[{k}]: item {esc.get('item')!r} isn't a rubric item (use null for unmapped)")
        if not esc.get("evidence"):
            errors.append(f"escapes[{k}]: needs evidence (PR URLs, commit SHAs, or comment links)")
    if not str(doc.get("summary") or "").strip():
        warnings.append("summary is empty")
    if not str(doc.get("level_rationale") or "").strip():
        warnings.append("level_rationale is empty")
    return errors, warnings


def cmd_validate(args):
    rubric = load_rubric()
    doc = load_json(args.scores)
    errors, warnings = validate(rubric, doc)
    for w in warnings:
        print(f"warning: {w}")
    for e in errors:
        print(f"error: {e}")
    print(f"{len(errors)} errors, {len(warnings)} warnings")
    sys.exit(1 if errors else 0)


# ---------------------------------------------------------------- compute


def eval_req(req, eff):
    ids = req_ids(req)
    values = {i: eff[i] for i in ids}
    applicable = [i for i in ids if values[i] is not None]
    if applicable:
        met = any(values[i] >= req["min"] for i in applicable)
    else:
        met = True
    return {
        "ids": ids,
        "label": " or ".join(ids),
        "min": req["min"],
        "values": values,
        "met": met,
        "na_pass": not applicable,
    }


def compute(rubric, doc):
    items = {i["id"]: i for i in rubric["items"]}
    cats = {c["id"]: c for c in rubric["categories"]}
    entries = doc["items"]

    escapes_by_item = defaultdict(list)
    for esc in doc.get("escapes") or []:
        if esc.get("item"):
            escapes_by_item[esc["item"]].append(esc)

    eff, caps = {}, {}
    for iid in items:
        s = entries[iid]["score"]
        if s == "na":
            eff[iid] = None
            continue
        if s > ESCAPE_CAP and escapes_by_item.get(iid):
            caps[iid] = s
            s = ESCAPE_CAP
        eff[iid] = s

    cat_results = {}
    for cid in cats:
        ids = [i for i in items if items[i]["category"] == cid]
        applicable = [i for i in ids if eff[i] is not None]
        pct = sum(eff[i] for i in applicable) / (4 * len(applicable)) if applicable else None
        cat_results[cid] = {"pct": pct, "items": len(ids), "applicable": len(applicable), "na": len(ids) - len(applicable)}

    applicable_weight = sum(cats[c]["weight"] for c in cats if cat_results[c]["pct"] is not None)
    overall = (
        sum(cats[c]["weight"] * cat_results[c]["pct"] for c in cats if cat_results[c]["pct"] is not None)
        / applicable_weight
        if applicable_weight
        else 0.0
    )

    share, gain = {}, {}
    for iid, item in items.items():
        cr = cat_results[item["category"]]
        if eff[iid] is None or not applicable_weight:
            share[iid] = gain[iid] = 0.0
            continue
        share[iid] = 100.0 * cats[item["category"]]["weight"] / applicable_weight / cr["applicable"]
        gain[iid] = share[iid] * (4 - eff[iid]) / 4

    level_results = []
    for lvl in rubric["levels"]:
        reqs = [eval_req(r, eff) for r in lvl["gates"]]
        level_results.append({
            "level": lvl["level"],
            "name": lvl["name"],
            "description": lvl["description"],
            "requirements": reqs,
            "own_met": all(r["met"] for r in reqs),
        })
    achieved = 0
    for lr in level_results[1:]:
        if not lr["own_met"]:
            break
        achieved = lr["level"]
    next_level = achieved + 1 if achieved + 1 < len(level_results) else None
    blockers = [r for r in level_results[next_level]["requirements"] if not r["met"]] if next_level is not None else []

    blocker_ids = {i for r in blockers for i in r["ids"]}
    others = sorted(
        (i for i in items if eff[i] is not None and eff[i] < 4 and i not in blocker_ids),
        key=lambda i: (-gain[i], i),
    )[:8]

    unprobed = [
        i for i in items
        if "anchors" not in items[i]
        and eff[i] is not None
        and eff[i] >= 3
        and not any(ev.get("kind") == "ran" for ev in entries[i].get("evidence") or [])
    ]

    na_gate_passes = sorted({i for lr in level_results for r in lr["requirements"] if r["na_pass"] for i in r["ids"]})

    return {
        "effective": eff,
        "caps": caps,
        "escapes_by_item": escapes_by_item,
        "categories": cat_results,
        "overall": overall,
        "share": share,
        "gain": gain,
        "levels": level_results,
        "achieved": achieved,
        "next_level": next_level,
        "blockers": blockers,
        "others": others,
        "unprobed": unprobed,
        "na_gate_passes": na_gate_passes,
    }


# ---------------------------------------------------------------- render


def fmt_score(v):
    return "N/A" if v is None else f"{v}/4"


def pct(v):
    return "N/A" if v is None else f"{round(v * 100)}%"


def render(rubric, doc, res, discover=None):
    items = {i["id"]: i for i in rubric["items"]}
    cats = {c["id"]: c for c in rubric["categories"]}
    entries = doc["items"]
    eff = res["effective"]
    gates = gate_items(rubric)
    repo = doc.get("repo") or {}
    L = []

    L.append(f"# Agentic development guardrails audit: {repo.get('name') or 'repository'}")
    L.append("")
    meta = []
    if repo.get("commit"):
        meta.append(f"Commit `{repo['commit']}`")
    if repo.get("branch"):
        meta.append(f"branch `{repo['branch']}`")
    if doc.get("audited_at"):
        meta.append(f"audited {doc['audited_at']}")
    if doc.get("auditor"):
        meta.append(f"by {doc['auditor']}")
    meta.append(f"rubric v{rubric['version']}")
    if doc.get("scope"):
        meta.append(f"scope: {doc['scope']}")
    if doc.get("window"):
        meta.append(f"history window: {doc['window']}")
    L.append(" · ".join(meta))
    L.append("")
    if str(doc.get("summary") or "").strip():
        L += [doc["summary"].strip(), ""]

    achieved = res["achieved"]
    lvl = res["levels"][achieved]
    L += [f"## Level {achieved}: {lvl['name']}", "", lvl["description"], "", "### Why this level", ""]
    if str(doc.get("level_rationale") or "").strip():
        L += [doc["level_rationale"].strip(), ""]
    for lr in res["levels"][1:achieved + 1]:
        parts = []
        for r in lr["requirements"]:
            vals = ", ".join(f"{i} {fmt_score(r['values'][i])}" for i in r["ids"])
            parts.append(f"{r['label']} needs {r['min']} ({vals})")
        L.append(f"- Level {lr['level']} gates pass: {'; '.join(parts)}.")
    if achieved == 0:
        lr = res["levels"][1]
        parts = [f"{r['label']} needs {r['min']} ({', '.join(f'{i} {fmt_score(r['values'][i])}' for i in r['ids'])})" for r in lr["requirements"]]
        L.append(f"- No Level 1 gate passes: {'; '.join(parts)}.")
    L.append("")

    if res["next_level"] is not None:
        nl = res["levels"][res["next_level"]]
        L += [f"### What blocks Level {nl['level']}: {nl['name']}", ""]
        for r in res["blockers"]:
            if len(r["ids"]) > 1:
                vals = ", ".join(f"{i} scores {fmt_score(r['values'][i])}" for i in r["ids"])
                L.append(f"- **{r['label']}** (either one): {vals}. One of them needs {r['min']}.")
                continue
            iid = r["ids"][0]
            step = str(entries[iid].get("next_step") or "").strip() or f"Target: {anchor_text(rubric, items[iid], r['min'])}"
            capped = f" Capped from {res['caps'][iid]} by escapes." if iid in res["caps"] else ""
            L.append(f"- **{iid} {items[iid]['name']}:** scores {fmt_score(eff[iid])}, needs {r['min']}.{capped} {step}")
        L.append("")

    L += ["### The ladder", ""]
    for lr in res["levels"]:
        box = "x" if lr["level"] <= achieved else " "
        note = ""
        if lr["level"] > achieved and lr["own_met"] and lr["level"] > 0:
            note = " *Its own gates already pass; a lower level is what holds the repo back.*"
        L.append(f"- [{box}] **Level {lr['level']}, {lr['name']}.** {lr['description']}{note}")
    L.append("")

    L += [f"## Rubric score: {pct(res['overall'])}", ""]
    L.append("The score measures how much of the full rubric is enforced, weighted by category. The level comes only from gate items, so a high score can't hide a missing fundamental.")
    L += ["", "| Category | Weight | Score | Items | N/A |", "| --- | --- | --- | --- | --- |"]
    for cat in rubric["categories"]:
        cr = res["categories"][cat["id"]]
        L.append(f"| {cat['id']}. {cat['name']} | {cat['weight']} | {pct(cr['pct'])} | {cr['items']} | {cr['na']} |")
    L.append("")

    L += ["## Roadmap", ""]
    n = 0
    seen = set()
    for r in res["blockers"]:
        ordered = sorted(r["ids"], key=lambda i: -res["gain"].get(i, 0))
        for iid in ordered[:1] if len(ordered) > 1 else ordered:
            if iid in seen or eff[iid] is None:
                continue
            seen.add(iid)
            n += 1
            step = str(entries[iid].get("next_step") or "").strip() or f"Target: {anchor_text(rubric, items[iid], r['min'])}"
            alt = f" (or raise {', '.join(i for i in r['ids'] if i != iid)})" if len(r["ids"]) > 1 else ""
            L.append(f"{n}. **{iid} {items[iid]['name']}** — Level {res['next_level']} blocker, now {fmt_score(eff[iid])}{alt}. {step}")
    for iid in res["others"]:
        if iid in seen:
            continue
        n += 1
        step = str(entries[iid].get("next_step") or "").strip() or f"Target: {anchor_text(rubric, items[iid], eff[iid] + 1)}"
        L.append(f"{n}. **{iid} {items[iid]['name']}** — now {fmt_score(eff[iid])}, worth up to {res['gain'][iid]:.1f} points. {step}")
    if n == 0:
        L.append("Nothing left to raise.")
    L.append("")

    escapes = doc.get("escapes") or []
    if escapes:
        L += ["## Escapes found", "", "Mistake classes that showed up at least twice in the history window. An escape against an item scored 3 or higher caps it at 2, because the gate leaks.", ""]
        for esc in sorted(escapes, key=lambda e: -e.get("occurrences", 0)):
            iid = esc.get("item")
            where = f"{iid} {items[iid]['name']}" if iid else "no rubric item; a candidate for the repo ban list (S1)"
            refs = ", ".join(str(x) for x in esc.get("evidence", [])[:6])
            more = f" (+{len(esc['evidence']) - 6} more)" if len(esc.get("evidence", [])) > 6 else ""
            L.append(f"- **{esc['class']}:** {esc['occurrences']} times, maps to {where}. Evidence: {refs}{more}")
        L.append("")

    L += ["## Rubric detail", ""]
    for cat in rubric["categories"]:
        cr = res["categories"][cat["id"]]
        L += [f"### {cat['id']}. {cat['name']}: {pct(cr['pct'])} (weight {cat['weight']})", "", cat["why"], ""]
        for item in rubric["items"]:
            if item["category"] != cat["id"]:
                continue
            iid = item["id"]
            e = entries[iid]
            v = eff[iid]
            label = "N/A" if v is None else f"{v}/4, {rubric['scale'][str(v)]['name']}"
            L += [f"#### {iid} {item['name']}: {label}", ""]
            notes = []
            if iid in gates:
                glvl, gmin = gates[iid]
                notes.append(f"Level {glvl} gate item; needs {gmin}.")
            if iid in res["caps"]:
                notes.append(f"Scored {res['caps'][iid]}, capped at {ESCAPE_CAP} because escapes in the window show the gate leaks.")
            if notes:
                L += [" ".join(notes), ""]
            if v is None:
                L += [f"Not applicable: {e.get('na_reason')}", ""]
            else:
                L += [f"*Anchor:* {anchor_text(rubric, item, v)}", ""]
            L += [str(e.get("rationale") or "").strip(), ""]
            ev = e.get("evidence") or []
            if ev:
                L.append("Evidence:")
                for x in ev:
                    by = f" (attested by {x['by']})" if x.get("kind") == "attested" else ""
                    note = f" — {x['note']}" if x.get("note") else ""
                    L.append(f"- `{x.get('kind')}` {x.get('ref')}{by}{note}")
                L.append("")
            if v is not None and v < 4 and str(e.get("next_step") or "").strip():
                L += [f"Next step: {e['next_step'].strip()}", ""]

    if res["unprobed"]:
        L += ["## Unprobed hard gates", "", "These items scored 3 or higher without a probe or canary run, so their scores rest on config or the operator's word rather than a gate seen failing.", ""]
        for iid in res["unprobed"]:
            L.append(f"- {iid} {items[iid]['name']}")
        L.append("")

    if res["na_gate_passes"]:
        L += ["## N/A gate items", "", "These gate items were marked N/A, which counts as passing their gate. Check the reasons before trusting the level.", ""]
        for iid in res["na_gate_passes"]:
            L.append(f"- {iid} {items[iid]['name']}: {entries[iid].get('na_reason')}")
        L.append("")

    if discover:
        L += render_discover(discover)

    limits = doc.get("limits") or []
    if limits:
        L += ["## Audit limits", ""]
        L += [f"- {x}" for x in limits]
        L.append("")

    L += ["## Method", ""]
    L.append(
        "Each item scores 0 to 4 on anchored descriptions, backed by evidence: `ran` (a command the audit executed), "
        "`cited` (a file, config, or URL), `attested` (the operator said so), or `searched` (where the audit looked and found nothing). "
        "Category scores are the mean item score over applicable items. The overall score weights categories as follows: "
        + ", ".join(f"{c['name']} {c['weight']}" for c in rubric["categories"])
        + ". N/A items drop out, and their category's weight is spread over the rest. "
        f"An escape (a mistake class seen twice or more) mapped to an item scored above {ESCAPE_CAP} caps that item at {ESCAPE_CAP}."
    )
    L.append("")
    L.append("The level is the highest rung whose gates pass, along with every rung below it:")
    L.append("")
    for lvl in rubric["levels"][1:]:
        reqs = "; ".join(f"{' or '.join(req_ids(r))} at {r['min']} or higher" for r in lvl["gates"])
        L.append(f"- Level {lvl['level']}: {reqs}.")
    L.append("")
    return "\n".join(L)


def render_discover(d):
    L = ["## Discovery signals", ""]
    ci = d.get("ci") or {}
    soft = [s for f in ci.get("files", []) for s in f.get("soft_fail", [])]
    L.append(f"- **CI files:** {len(ci.get('files', []))}. Soft-fail patterns: {len(soft)}.")
    for s in soft[:8]:
        L.append(f"  - `{s.get('path')}:{s.get('line')}` {s.get('text')}")
    gh = d.get("github") or {}
    if gh.get("available"):
        req = sorted(set((gh.get("rules") or {}).get("required_status_checks", []) + (gh.get("protection") or {}).get("required_status_checks", [])))
        L.append(f"- **Required status checks on `{gh.get('default_branch')}`:** {', '.join(req) if req else 'none found'}.")
        rc = gh.get("review_comments") or {}
        if rc:
            L.append(f"- **Review comments read:** {rc.get('count', 0)} ({rc.get('bot_count', 0)} from bots), back to {rc.get('oldest') or 'n/a'}.")
    else:
        L.append(f"- **GitHub settings:** not read ({gh.get('error') or 'run discover.py with --github'}).")
    st = d.get("structure") or {}
    if st.get("largest_files"):
        top = ", ".join(f"`{f['path']}` ({f['lines']})" for f in st["largest_files"][:5])
        L.append(f"- **Largest files:** {top}. Over 1,000 lines: {st.get('over_1000', 0)}; over 3,000: {st.get('over_3000', 0)}.")
    g = d.get("git") or {}
    if g.get("commits"):
        hs = ", ".join(f"`{h['path']}` ({h['commits']})" for h in g.get("hotspots", [])[:5])
        L.append(f"- **Commits in window:** {g['commits']}. Hotspots: {hs}.")
        sp = g.get("dir_spread") or {}
        if sp:
            L.append(f"- **Directories touched per commit:** median {sp.get('median')}, 90th percentile {sp.get('p90')}.")
        L.append(f"- **Reverts:** {g.get('reverts', {}).get('count', 0)}. Fix commits: {g.get('fix_commits', 0)}.")
        ac = g.get("added_comments") or {}
        if ac:
            L.append(f"- **Comment lines added:** {ac.get('comment_lines', 0)} of {ac.get('added_lines', 0)} added lines; {len(ac.get('narration_samples', []))} look like history narration.")
    sup = d.get("suppressions") or {}
    if sup.get("total") is not None:
        by = ", ".join(f"{k} {v['count']}" for k, v in sorted(sup.get("by_pattern", {}).items(), key=lambda kv: -kv[1]["count"])[:8])
        L.append(f"- **Suppressions:** {sup['total']} ({sup.get('with_reason', 0)} with a reason, {sup.get('with_expiry', 0)} with an expiry). {by}.")
    eh = d.get("escape_hatches") or {}
    if eh:
        L.append(f"- **Type escape hatches:** {', '.join(f'{k} {v}' for k, v in eh.items())}.")
    L.append("")
    return L


def cmd_report(args):
    rubric = load_rubric()
    doc = load_json(args.scores)
    errors, warnings = validate(rubric, doc)
    for w in warnings:
        print(f"warning: {w}", file=sys.stderr)
    if errors:
        for e in errors:
            print(f"error: {e}", file=sys.stderr)
        sys.exit(f"{len(errors)} validation errors; fix scores before rendering the report.")
    res = compute(rubric, doc)
    discover = load_json(args.discover) if args.discover else None
    text = render(rubric, doc, res, discover)
    if args.out:
        with open(args.out, "w") as f:
            f.write(text)
    else:
        sys.stdout.write(text)
    if args.json:
        result = {
            "repo": doc.get("repo"),
            "audited_at": doc.get("audited_at"),
            "rubric_version": rubric["version"],
            "level": res["achieved"],
            "level_name": res["levels"][res["achieved"]]["name"],
            "overall_pct": round(res["overall"] * 100, 1),
            "categories": {c: (None if v["pct"] is None else round(v["pct"] * 100, 1)) for c, v in res["categories"].items()},
            "items": res["effective"],
            "caps": res["caps"],
            "blockers": [r["label"] for r in res["blockers"]],
            "unprobed": res["unprobed"],
            "escapes": len(doc.get("escapes") or []),
        }
        with open(args.json, "w") as f:
            json.dump(result, f, indent=2)
    level = res["levels"][res["achieved"]]
    print(f"Level {res['achieved']} ({level['name']}), score {pct(res['overall'])}, {len(res['blockers'])} blockers to the next level.", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("template", help="write a blank scores.json for every rubric item")
    t.add_argument("--repo", help="repo root, to fill name, commit, and branch")
    t.add_argument("--out", help="output path (default: stdout)")
    r = sub.add_parser("rubric", help="print the rubric as markdown")
    r.add_argument("--category", help="comma-separated category ids to print, such as A,T")
    v = sub.add_parser("validate", help="check scores.json against the rubric")
    v.add_argument("scores")
    p = sub.add_parser("report", help="validate, compute, and render the report")
    p.add_argument("scores")
    p.add_argument("--discover", help="discover.json, to add discovery signals")
    p.add_argument("--out", help="report path (default: stdout)")
    p.add_argument("--json", help="also write computed results as JSON")
    args = ap.parse_args()
    {"template": cmd_template, "rubric": cmd_rubric, "validate": cmd_validate, "report": cmd_report}[args.cmd](args)


if __name__ == "__main__":
    main()
