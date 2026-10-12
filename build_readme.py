#!/usr/bin/env python3
"""Build noumanshakeil profile README: digit portrait + curated catalog."""
from __future__ import annotations

import json
from pathlib import Path

from descriptions import DESCRIPTIONS, SKIP, SKIP_PREFIXES

ROOT = Path(__file__).parent

public = json.loads((ROOT / "repos.json").read_text(encoding="utf-8"))
private = []
priv_path = ROOT / "private_repos.json"
if priv_path.exists():
    private = json.loads(priv_path.read_text(encoding="utf-8"))

by_name: dict[str, dict] = {}
for r in public + private:
    by_name[r["name"]] = r


def should_skip(name: str) -> bool:
    if name in SKIP:
        return True
    for p in SKIP_PREFIXES:
        if name.startswith(p):
            return True
    return False


def esc(s: str) -> str:
    return (s or "").replace("|", "\\|").replace("\n", " ").strip()


def clean_gh_desc(d: str) -> str:
    d = esc(d)
    # fix mojibake leftovers from prior UTF-16 mishaps
    for bad in ("ΓÇö", "ΓÇô", "ΓåÆ", "â€”", "â€“", "â†’", "Ã¢â‚¬â€"):
        d = d.replace(bad, "—")
    d = d.replace("ΓÇö", "—")
    return d


def desc_for(name: str) -> str:
    if name in DESCRIPTIONS:
        d = DESCRIPTIONS[name]
    else:
        d = clean_gh_desc(by_name.get(name, {}).get("description") or "")
        if not d or d.lower().startswith("hands-on project"):
            nice = name.replace("-", " ").replace("_", " ")
            d = f"{nice[0].upper() + nice[1:]} — applied AI/ML project (see repo README)."
        elif d.lower() in {"capstone project"}:
            d = DESCRIPTIONS.get(name, "Capstone Generative AI project — see FinSight-AI README for the full RAG + Bedrock story.")
    if len(d) > 170:
        d = d[:167] + "…"
    return d


def link(name: str) -> str:
    return f"[`{name}`](https://github.com/noumanshakeil/{name})"


CATEGORIES: list[tuple[str, str, list[str]]] = [
    (
        "Products & platforms",
        "Things people can open and use",
        [
            "PocketMind-HybridAI",
            "PocketMind",
            "PocketMind-AI-Motivation",
            "pocketmind-linkedin-agent",
            "code-review-assistant",
            "PULSE-AI-News-Intelligence-Platform",
            "ai-receptionist-platform",
            "harborline-receptionist",
            "cold-outreach",
            "FinSight-AI",
            "NEXUSAI",
            "nexus-ai-mac",
            "Intelligent-Phone-Recommendation-Chatbot",
            "Samsung-sales-chatbot",
            "AI-Resume-Matcher",
            "DBS-Project",
            "price-fighter",
            "chess-project",
            "OOP-semester-project-LLM",
        ],
    ),
    (
        "RAG · retrieval · knowledge",
        "Grounded generation you can run locally",
        [
            "local-rag-ollama",
            "pdf-qa-rag",
            "rag-with-citations",
            "hybrid-bm25-vector-rag",
            "retrieval-reranker",
            "document-chunking-lab",
            "knowledge-graph-rag",
            "semantic-cache-llm",
            "local-embedding-server",
            "vector-db-benchmark",
        ],
    ),
    (
        "Agents · tools · orchestration",
        "Agents that plan, call tools, and remember",
        [
            "agentic-web-researcher",
            "multi-agent-debate",
            "tool-calling-agent",
            "sql-agent-text2sql",
            "agent-memory-store",
            "function-calling-router",
            "ai-interview-coach",
            "ai-code-debugger",
            "streaming-llm-chat",
            "fastapi-llm-guardrails",
            "prompt-injection-lab",
            "llm-eval-harness",
        ],
    ),
    (
        "Computer vision · perception",
        "Detection, recognition, imaging",
        [
            "AI-Powered-Smart-Surveillance-System",
            "CodeAlpha_object-detection-system",
            "Face-detection-system",
            "Image-Recognition-Model",
            "AI-hand-gesture-recognition",
            "medical-image-segmentation",
            "cartoonify-image",
            "handwritten-digit-recognizer",
            "CodeAlpha_Handwritten_character_recognition",
            "multimodal-clip-search",
            "vision-qa-pipeline",
            "pose-estimation-demo",
            "ocr-llm-extractor",
            "yolo-custom-train-template",
            "edge-tflite-classifier",
            "diffusion-image-cli",
            "augmented-reality-project",
            "point-sparse-segmentation",
        ],
    ),
    (
        "ML · NLP · speech · forecasting",
        "Classical ML, language, audio, and time series",
        [
            "iris-flower-classification",
            "house-price-predictor",
            "spam-email-detector",
            "CodeAlpha_credit-scoring-model",
            "time-series-forecasting",
            "anomaly-detection-timeseries",
            "recommendation-engine-cf",
            "tabular-automl-baseline",
            "lora-finetune-demo",
            "mlops-model-registry",
            "CodeAlpha_faq-chatbot",
            "CodeAlpha_Music-generation-AI",
            "CodeAlpha_language-translator",
            "CodeAlpha_emotion-recognition-from-speech",
            "whisper-meeting-notes",
            "voice-agent-local",
            "audio-event-classifier",
            "ner-spacy-api",
            "text-summarization-api",
            "sentiment-stream-dashboard",
        ],
    ),
]

used: set[str] = set()
sections: list[str] = []
for title, subtitle, names in CATEGORIES:
    rows = []
    i = 1
    for n in names:
        if should_skip(n):
            continue
        if n not in by_name:
            # still list curated product repos even if private / missing from dump
            if n not in DESCRIPTIONS:
                continue
        used.add(n)
        rows.append(f"| {i}. | {link(n)} | {desc_for(n)} |")
        i += 1
    if not rows:
        continue
    sections.append(
        f"### {title}\n"
        f"*{subtitle}*\n\n"
        f"| # | Project | Description |\n"
        f"|---|---------|-------------|\n" + "\n".join(rows)
    )

# Remaining public repos that aren't skipped / already used
remaining = sorted(
    (
        r["name"]
        for r in public
        if r["name"] not in used and not should_skip(r["name"])
    ),
    key=str.lower,
)
if remaining:
    rows = []
    for i, n in enumerate(remaining, 1):
        rows.append(f"| {i}. | {link(n)} | {desc_for(n)} |")
    sections.append(
        "### More builds\n"
        "*Other public repos worth a look*\n\n"
        "| # | Project | Description |\n"
        "|---|---------|-------------|\n" + "\n".join(rows)
    )

catalog = "\n\n".join(sections)

header = r'''<div align="center">

<picture>
  <source media="(max-width: 768px)" srcset="./assets/hero-mobile.png" />
  <img src="./assets/hero.png" alt="Muhammad Nouman Shakeel — digit portrait and profile" width="100%" />
</picture>

</div>

# Muhammad Nouman Shakeel

**Founder of PocketMind · Co-founder of CodexBridge · AI Engineer @ Zindex · BS Artificial Intelligence @ NUST**

[![Email](https://img.shields.io/badge/Email-nouman.shakeel555%40gmail.com-161b22?style=for-the-badge&logo=gmail&logoColor=ea4335)](mailto:nouman.shakeel555@gmail.com)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-noumanshakeil-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/noumanshakeil)
[![Microsoft Store](https://img.shields.io/badge/Microsoft%20Store-PocketMind%20AI-107C10?style=for-the-badge&logo=microsoftstore&logoColor=white)](https://apps.microsoft.com/detail/9nz7wf9vxf5r)
[![Google Play](https://img.shields.io/badge/Google%20Play-PocketMind%20AI%3A%20Offline%20AI%20Labs-414141?style=for-the-badge&logo=googleplay&logoColor=white)](https://play.google.com/store/search?q=PocketMind%20AI%20Offline%20AI%20Labs&c=apps)

---

## Who I am

I build AI people can actually run — offline-first products, agent systems, retrieval pipelines, and vision stacks. Not notebook demos. Things that ship.

- **PocketMind AI** — desktop AI workspace (Microsoft Store) and **PocketMind AI: Offline AI Labs** on Android
- **Agents & RAG** — tool-calling agents, hybrid retrieval, citations, memory
- **Vision & ML** — detection, recognition, surveillance, classical pipelines
- **Product engineering** — FastAPI / Next.js / Flutter surfaces on top of real models

ETEA '25 CS KPK topper. Building in public from Islamabad.

> *"The worst code is often left public."* — so I leave the useful parts public too.

---

## On the stores

| App | Where |
|-----|--------|
| **PocketMind AI** (Windows) | [Microsoft Store](https://apps.microsoft.com/detail/9nz7wf9vxf5r) |
| **PocketMind AI: Offline AI Labs** (Android) | [Google Play](https://play.google.com/store/search?q=PocketMind%20AI%20Offline%20AI%20Labs&c=apps) |

---

## Tech I actually use

**Languages** · `Python` `TypeScript` `JavaScript` `C++` `SQL` `Kotlin`

**AI / ML / CV** · `PyTorch` `scikit-learn` `OpenCV` `YOLO` `MediaPipe` `Whisper` `llama.cpp`

**LLM · RAG · Agents** · `LangChain` `Ollama` `Groq` `OpenAI` `DeepSeek` `RAG` `tool-calling`

**App / Backend** · `FastAPI` `Next.js` `Node.js` `Flutter` `Postgres` `SQLite` `Tauri`

---

## Live telemetry

<div align="center">

<img src="https://github-readme-stats.vercel.app/api?username=noumanshakeil&show_icons=true&theme=radical&hide_border=true&bg_color=0d1117&title_color=58a6ff&icon_color=39d353&text_color=c9d1d9" height="165" alt="GitHub stats" />
<img src="https://streak-stats.demolab.com/?user=noumanshakeil&theme=radical&hide_border=true&background=0d1117&ring=58a6ff&fire=39d353&currStreakLabel=c9d1d9" height="165" alt="GitHub streak" />

<img src="https://github-readme-stats.vercel.app/api/top-langs/?username=noumanshakeil&layout=compact&theme=radical&hide_border=true&bg_color=0d1117&title_color=58a6ff&text_color=c9d1d9" height="165" alt="Top languages" />

<br/>

<img src="https://ghchart.rshah.org/39d353/noumanshakeil" width="100%" alt="GitHub contribution chart" />

</div>

---

## Architecture I keep shipping

```text
                 ┌──────────────────┐
   Users / Apps  │  Mobile · Web ·  │
                 │  Desktop clients │
                 └────────┬─────────┘
                          │
              ┌───────────▼───────────┐
              │  Agents / Orchestrator │──── tools · memory · routing
              └───────────┬───────────┘
                          │
         ┌────────────────┼────────────────┐
         ▼                ▼                ▼
   ┌──────────┐    ┌────────────┐   ┌────────────┐
   │   RAG    │    │  Vision /  │   │  Local LLM │
   │ retrieve │    │ Perception │   │  Ollama    │
   └────┬─────┘    └─────┬──────┘   └─────┬──────┘
        │                │                │
        └────────────────┼────────────────┘
                         ▼
                 grounded answers · actions · alerts
```

---

## Featured orbit

| Signal | Repo | Why it matters |
|--------|------|----------------|
| Product | [`PocketMind-HybridAI`](https://github.com/noumanshakeil/PocketMind-HybridAI) | PocketMind AI + Offline AI Labs — store apps for desktop & Android |
| Intelligence | [`PULSE-AI-News-Intelligence-Platform`](https://github.com/noumanshakeil/PULSE-AI-News-Intelligence-Platform) | Summarize, bias-check, and fact-check news in one pipeline |
| Voice / Biz | [`harborline-receptionist`](https://github.com/noumanshakeil/harborline-receptionist) | AI receptionist with knowledge Q&A + booking |
| Growth | [`cold-outreach`](https://github.com/noumanshakeil/cold-outreach) | Multi-sender outreach with drafts, lists, campaigns |
| Content | [`pocketmind-linkedin-agent`](https://github.com/noumanshakeil/pocketmind-linkedin-agent) | LinkedIn campaigns & dated outbox packages |
| Vision | [`AI-Powered-Smart-Surveillance-System`](https://github.com/noumanshakeil/AI-Powered-Smart-Surveillance-System) | Real-time surveillance with alerts & evidence |

---

## Full lab — projects & repositories

'''

footer = r'''

---

## Connect

- **Email:** [nouman.shakeel555@gmail.com](mailto:nouman.shakeel555@gmail.com)
- **LinkedIn:** [linkedin.com/in/noumanshakeil](https://www.linkedin.com/in/noumanshakeil)
- **GitHub:** [github.com/noumanshakeil](https://github.com/noumanshakeil)
- **PocketMind AI (Microsoft Store):** [apps.microsoft.com](https://apps.microsoft.com/detail/9nz7wf9vxf5r)
- **PocketMind AI: Offline AI Labs (Play Store):** [Google Play](https://play.google.com/store/search?q=PocketMind%20AI%20Offline%20AI%20Labs&c=apps)

<div align="center">

<br/>

<img src="https://hits.sh/github.com/noumanshakeil/noumanshakeil.svg?style=for-the-badge&label=Profile%20views&color=58a6ff" alt="Profile views" />
<br/>
<img src="https://visitor-badge.laobi.icu/badge?page_id=noumanshakeil.noumanshakeil&left_color=gray&right_color=blue" alt="Visitors" />

<br/><br/>

*Building AI that stays useful when the demo ends.*

</div>
'''

readme = header + catalog + footer
(ROOT / "README.md").write_text(readme, encoding="utf-8")
print(f"Wrote README.md ({len(readme)} chars, {len(used)} curated repos)")
print("Skipped noise:", ", ".join(sorted(SKIP)[:12]), "…")
