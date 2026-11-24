"""Diagram for Improvement 1 (stop scattering a conversation across models).

    python3 build_improvement1.py   # writes improvement1.svg here
    node render.js                  # renders ../improvement1.png

Behaviour of "today" is taken from enterprise-inference@723fe6e:
roles/litellm/files/router/custom_hybrid_router.py:153,157 and
router_strategy/hybrid_router/hybrid_router.py:136,206,234-236.
Tier candidates follow the example in agent-toolkit docs/hybrid-router.md.
"""
import os

from svglib import SVG

HERE = os.path.dirname(os.path.abspath(__file__))

LLAMA = ("#DBEAFE", "#2563EB", "#1E3A8A")
QWEN = ("#EDE9FE", "#7C3AED", "#4C1D95")
WARM = ("#DCFCE7", "#16A34A", "#14532D")
COLD = ("#FEE2E2", "#DC2626", "#7F1D1D")
PART = ("#FEF3C7", "#D97706", "#78350F")
NEUT = ("#F1F5F9", "#64748B", "#1E293B")


def cell(s, x, y, w, h, colours, title, line=None, size=12.5):
    fill, stroke, tcol = colours
    s.rect(x, y, w, h, fill, stroke, rx=8, sw=1.5)
    s.text(x + 10, y + 21, title, size=size, weight=700, fill=tcol)
    if line:
        s.text(x + 10, y + 40, line, size=11.5, fill="#334155")


def bar(s, x, y, frac, colour, label):
    s.rect(x, y, 270, 14, "#F1F5F9", "#CBD5E1", rx=4, sw=1)
    s.rect(x, y, max(8, 270 * frac), 14, colour, colour, rx=4, sw=0)
    s.text(x, y + 30, label, size=11, fill="#475569")


def diamond(s, cx, cy, w, h, lines, colours=PART):
    fill, stroke, tcol = colours
    pts = f"{cx},{cy - h / 2} {cx + w / 2},{cy} {cx},{cy + h / 2} {cx - w / 2},{cy}"
    s.parts.append(f'<polygon points="{pts}" fill="{fill}" stroke="{stroke}" stroke-width="1.6"/>')
    for i, ln in enumerate(lines):
        s.text(cx, cy - 6 + i * 16 - (len(lines) - 1) * 4, ln, size=12, weight=700, fill=tcol, anchor="middle")


def node(s, x, y, w, h, title, line=None, colours=NEUT):
    cell(s, x, y, w, h, colours, title, line, size=12.5)


def timeline(s, top, label, rows, turns, summary, theme):
    s.container(30, top, 1740, 380, label, theme=theme)
    labels = ["Turn", rows[0], rows[1], rows[2], rows[3]]
    ys = [top + 32, top + 82, top + 148, top + 214, top + 280]
    hs = [40, 56, 56, 56, 46]
    for lbl, y, h in zip(labels, ys, hs):
        s.text(48, y + 26, lbl, size=12.5, weight=700, fill="#334155")
    x0, w, gap = 250, 290, 10
    for i, t in enumerate(turns):
        x = x0 + i * (w + gap)
        cell(s, x, ys[0], w, hs[0], NEUT, t["turn"], size=13)
        cell(s, x, ys[1], w, hs[1], NEUT, t["in1"], t["in2"], size=12)
        cell(s, x, ys[2], w, hs[2], t["mcol"], t["m1"], t["m2"], size=12.5)
        cell(s, x, ys[3], w, hs[3], t["ccol"], t["c1"], t["c2"], size=12.5)
        t["last"](s, x + 10, ys[4] + 6)
        if i < len(turns) - 1:
            s.arrow([(x + w + 1, ys[2] + 28), (x + w + gap - 1, ys[2] + 28)], colour="grey", sw=1.2)
    s.text(250, top + 362, summary, size=13, weight=700, fill="#0F172A")


def build():
    s = SVG(1800, 1560)
    s.text(40, 42, "Improvement 1 — Stop scattering a conversation across models", size=24, weight=800)
    s.text(40, 66, "One agent conversation, five turns. Tier candidates as in docs/hybrid-router.md: "
                   "SIMPLE/MEDIUM → llama-3-1-8b or qwen3-coder-30b · COMPLEX → qwen3-coder-30b.",
           size=13.5, fill="#475569")

    # ---------------- A: today ----------------
    today = [
        dict(turn="Turn 1 · “list the files”", in1="joined user text ≈ 300 chars", in2="(len // 4 ≈ 75 tokens)",
             mcol=LLAMA, m1="SIMPLE → llama-3-1-8b", m2="bandit pick",
             ccol=NEUT, c1="first turn", c2="reads turn 1",
             last=lambda s, x, y: bar(s, x, y, 0.15, "#94A3B8", "normal prefill")),
        dict(turn="Turn 2 · “show the parser”", in1="joined ≈ 700 chars", in2="still SIMPLE",
             mcol=QWEN, m1="SIMPLE → qwen3-coder-30b", m2="bandit explores another arm",
             ccol=COLD, c1="COLD: never saw turn 1", c2="re-reads turns 1–2",
             last=lambda s, x, y: bar(s, x, y, 0.45, "#DC2626", "extra re-read")),
        dict(turn="Turn 3 · “explain this loop”", in1="joined ≈ 1,200 chars", in2="score rises → MEDIUM",
             mcol=LLAMA, m1="MEDIUM → llama-3-1-8b", m2="bandit pick",
             ccol=PART, c1="PARTIAL: has turn 1 only", c2="re-reads turns 2–3",
             last=lambda s, x, y: bar(s, x, y, 0.45, "#D97706", "extra re-read")),
        dict(turn="Turn 4 · “refactor the parser”", in1="joined ≈ 1,700 chars > 1,600", in2="token signal → +1 (line 136)",
             mcol=QWEN, m1="COMPLEX → qwen3-coder-30b", m2="only COMPLEX candidate",
             ccol=PART, c1="PARTIAL: has turns 1–2", c2="re-reads turns 3–4",
             last=lambda s, x, y: bar(s, x, y, 0.55, "#D97706", "extra re-read")),
        dict(turn="Turn 5 · “thanks!”", in1="newest turn is tiny, but", in2="joined ≈ 1,750 chars → COMPLEX",
             mcol=QWEN, m1="COMPLEX → qwen3-coder-30b", m2="30B model for “thanks”",
             ccol=WARM, c1="WARM: has turns 1–4", c2="reads only turn 5",
             last=lambda s, x, y: bar(s, x, y, 0.08, "#16A34A", "cheap")),
    ]
    timeline(s, 86, "A · TODAY — the router decides every request from ALL user messages joined together "
                    "(custom_hybrid_router.py:153 → hybrid_router.py:136)",
             ["Router input", "Tier → model", "KV cache on that model", "Prefill work"], today,
             "Result: 3 model changes in 4 steps → 3 extra re-reads; a 30B model answers “thanks”; "
             "the bandit's latency mixes warm and cold turns (it partly learns cache luck).", "danger")

    # ---------------- B: after ----------------
    after = [
        dict(turn="Turn 1 · “list the files”", in1="newest turn → SIMPLE", in2="session tier = SIMPLE",
             mcol=LLAMA, m1="pin llama-3-1-8b", m2="first choice by bandit",
             ccol=NEUT, c1="first turn", c2="reads turn 1",
             last=lambda s, x, y: s.label(x, y + 18, "✓ bandit updated", colour="#16A34A", size=12)),
        dict(turn="Turn 2 · “show the parser”", in1="newest turn → SIMPLE", in2="session tier = SIMPLE",
             mcol=LLAMA, m1="stay llama-3-1-8b", m2="pinned model still fits",
             ccol=WARM, c1="WARM", c2="reads only turn 2",
             last=lambda s, x, y: s.label(x, y + 18, "✓ bandit updated", colour="#16A34A", size=12)),
        dict(turn="Turn 3 · “explain this loop”", in1="newest turn → MEDIUM", in2="session tier ↑ MEDIUM",
             mcol=LLAMA, m1="stay llama-3-1-8b", m2="llama is a MEDIUM candidate",
             ccol=WARM, c1="WARM", c2="reads only turn 3",
             last=lambda s, x, y: s.label(x, y + 18, "✓ bandit updated", colour="#16A34A", size=12)),
        dict(turn="Turn 4 · “refactor the parser”", in1="newest turn → COMPLEX", in2="session tier ↑ COMPLEX",
             mcol=QWEN, m1="escalate → qwen3-coder-30b", m2="llama can't serve COMPLEX",
             ccol=COLD, c1="COLD once (the only switch)", c2="re-reads turns 1–4",
             last=lambda s, x, y: s.label(x, y + 18, "✗ skipped: switched turn", colour="#DC2626", size=12)),
        dict(turn="Turn 5 · “thanks!”", in1="newest turn → SIMPLE", in2="session tier stays COMPLEX",
             mcol=QWEN, m1="stay qwen3-coder-30b", m2="never bounce back down",
             ccol=WARM, c1="WARM", c2="reads only turn 5",
             last=lambda s, x, y: s.label(x, y + 18, "✓ bandit updated", colour="#16A34A", size=12)),
    ]
    timeline(s, 486, "B · AFTER — classify the NEWEST turn, keep a session tier that only goes up, "
                     "stay on the pinned model while it can serve that tier",
             ["Router input", "Model decision", "KV cache", "Learning signal"], after,
             "Result: 1 model change (a deliberate escalation) → 1 re-read; "
             "the bandit learns only from like-for-like turns (step 4).", "infer")

    # ---------------- C: new router logic ----------------
    s.container(30, 886, 1010, 620, "C · New logic inside HybridRouterProxy.async_pre_routing_hook (steps 2–4)",
                theme="gateway")
    node(s, 60, 920, 440, 50, "1  Request arrives", "session_id from the agent (request metadata)")
    node(s, 60, 990, 440, 50, "2  Classify the NEWEST user turn → turn_tier", "not all user messages joined")
    node(s, 60, 1060, 440, 50, "3  session_tier = max(session_tier, turn_tier)", "it can only go up")
    for y in (970, 1040):
        s.arrow([(280, y), (280, y + 20)], colour="blue")
    s.arrow([(280, 1110), (280, 1128)], colour="blue")
    diamond(s, 280, 1175, 360, 92, ["Pinned model is a", "candidate of session_tier?"])
    node(s, 570, 1150, 440, 50, "YES → use the pinned model", "KV cache warm · switched = false", WARM)
    s.arrow([(460, 1175), (570, 1175)], colour="green", label="yes", label_at=(500, 1167))
    node(s, 60, 1250, 440, 56, "NO → bandit picks for session_tier", "pin the new model · switched = true", COLD)
    s.arrow([(280, 1221), (280, 1250)], colour="red", label="no", label_at=(290, 1240))
    node(s, 570, 1250, 440, 50, "4  Model answers", "latency and tokens recorded")
    s.arrow([(790, 1200), (790, 1250)], colour="default")
    s.arrow([(500, 1278), (570, 1278)], colour="default")
    s.arrow([(790, 1300), (790, 1326)], colour="default")
    diamond(s, 790, 1370, 260, 84, ["switched?"])
    node(s, 60, 1345, 440, 50, "YES → don't update the bandit", "this latency includes a cold re-read", PART)
    s.arrow([(660, 1370), (500, 1370)], colour="#D97706", label="yes", label_at=(560, 1362))
    node(s, 570, 1436, 440, 50, "NO → update bandit with the reward", "clean, like-for-like sample", WARM)
    s.arrow([(790, 1412), (790, 1436)], colour="green", label="no", label_at=(800, 1428))

    # ---------------- D: measure gate + Xeon strengths ----------------
    s.container(1070, 886, 700, 620, "D · Step 1 (measure first) and Step 5 (play to Xeon's strengths)",
                theme="repo")
    s.box(1086, 918, 668, 176, "Step 1 — Measure first: a go / no-go gate ⚠️", [
        "switch rate = turns whose model ≠ previous turn's model ÷ all turns",
        "penalty = median TTFT(switched turns) − median TTFT(stayed turns)",
        "daily waste ≈ switch rate × penalty × turns per day",
        "Small → stop here (don't build steps 2–4).  Large → build them.",
        "Needs session_id in request metadata → visible in Langfuse traces.",
    ], theme="note", title_size=13.5, line_size=12, line_gap=24)
    s.text(1086, 1124, "Step 5 — play to Xeon's strengths", size=14, weight=800, fill="#9A3412")
    s.box(1086, 1138, 668, 112, "a · Keep KV caches longer (big DRAM, 📚 CXL)", [
        "GPU memory is tens–hundreds of GB; a Xeon server has terabytes of DRAM.",
        "Longer-lived caches → resumed sessions and repeated system prompts stay warm.",
        "Turn Xeon's capacity into fewer re-reads, the step CPUs find most expensive.",
    ], theme="white", title_size=13, line_size=12, line_gap=22)
    s.box(1086, 1262, 668, 112, "b · Quantised agent models, behind an accuracy gate", [
        "int8 / int4 weights → fewer bytes read per token → faster generation.",
        "Gate: ship only if tool-call JSON validity and task success match bf16.",
        "Catalog already supports AWQ and OpenVINO int4 (models.yaml:103, :109).",
    ], theme="white", title_size=13, line_size=12, line_gap=22)
    s.box(1086, 1386, 668, 108, "c · Keep sandboxes on separate machines", [
        "CPU pinning separates cores, NOT shared cache and memory bandwidth.",
        "A busy sandbox can slow token generation on the same socket.",
        "First: nodeSelector for sandboxes. Intel RDT only if they must share.",
    ], theme="white", title_size=13, line_size=12, line_gap=22)

    s.text(40, 1540, "Today's behaviour from enterprise-inference@723fe6e: custom_hybrid_router.py:153,157,162 · "
           "hybrid_router.py:136,206,234–236 · models.yaml:416 (prefix caching on). Drawn for study.",
           size=11.5, fill="#64748B", italic=True)
    s.save(os.path.join(HERE, "improvement1.svg"))


if __name__ == "__main__":
    build()
    print("wrote improvement1.svg")
