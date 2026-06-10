# Website (evanostudio.com)

This document defines the purpose and requirements for the official website. The site is built with **Next.js + React + TypeScript** as `apps/website` (see [ARCHITECTURE.md](ARCHITECTURE.md)).

> The website is a separate concern from the desktop app. It ships independently and shares no sensitive data with the app.

---

## Purpose

`evanostudio.com` exists to:

1. **Explain what Evano Studio is** — clearly, for non-technical people.
2. **Let people download the app** (when releases exist).
3. **Host the documentation** so users can learn and troubleshoot.
4. **Answer common questions** via an FAQ.
5. **Represent the project honestly** — local-first, free, open source, and currently early-stage.

The site is mostly static, fast, privacy-respecting (no tracking by default), and cheap to host.

---

## Landing page requirements

The landing page must clearly communicate:

- **The one-line promise:** "Create local AI agents for your business — without paid APIs, without cloud lock-in, and without touching the terminal."
- **What it is:** a free, open-source, local-first desktop app for creating and managing local AI agents.
- **Who it's for:** creators, startups, and small businesses who want private AI without the cloud.
- **The three pillars:** Free by default · Local-first · Privacy-first.
- **Key features** at a high level: agents, chat, documents, knowledge base, image prompts/generation, routines + calendar.
- **What users need locally:** their computer, Ollama, a local model, optional ComfyUI (link to [FREE_BY_DEFAULT.md](FREE_BY_DEFAULT.md) content).
- **An honest status badge** (e.g., "Alpha — in active development").
- A clear call to action to **Download** (or "Get notified" before releases exist).

It must **not** use hype, fake testimonials, fake metrics, or imply the product is finished.

---

## Download page requirements

- **macOS first.** Clearly state supported platforms; don't list platforms that aren't built.
- **Honest prerequisites.** Plainly explain that the user needs Ollama and at least one local model, with links to setup steps. Optional: ComfyUI for images.
- **System guidance.** Set realistic expectations about hardware (RAM/CPU/GPU affecting model size and speed).
- **No silent installers.** Link to the official Ollama / ComfyUI downloads; do not bundle or auto-run third-party installers (see [SECURITY.md](SECURITY.md)).
- **Version + changelog** for each release.
- **Clear alpha warning** until the product is stable: this is early software and may have rough edges.
- If no release exists yet, the page should say so honestly and offer a way to follow progress instead of a fake download button.

---

## Documentation requirements

- Host user-facing documentation (getting started, creating agents, knowledge base, routines, images, troubleshooting).
- Mirror or derive from the `docs/` in this repository where appropriate, written for **non-technical users**.
- Cover the **"what you need locally"** setup clearly.
- Include a **troubleshooting** section (Ollama not detected, no model installed, ComfyUI not configured) that matches the app's actual behavior.
- Keep docs versioned alongside releases so instructions match the installed app.

---

## FAQ requirements

The FAQ must answer, honestly:

- **Is it really free?** Yes — no paid APIs, no cloud, no subscription. You need your own computer and free local tools. (Link to [FREE_BY_DEFAULT.md](FREE_BY_DEFAULT.md).)
- **Does my data go to the cloud?** No, not by default. Everything is local. (Link to [SECURITY.md](SECURITY.md).)
- **Do I need to use the terminal?** No — the app is a desktop control center. (Installing Ollama is a normal app install; the app guides you.)
- **What hardware do I need?** Honest guidance on RAM/CPU/GPU and model sizes.
- **Which models are supported?** Gemma (recommended), Qwen, Llama, Mistral, DeepSeek distill — via Ollama.
- **Do I need ComfyUI?** Only for optional local image generation; everything else works without it.
- **Is it production-ready?** No — it's early/alpha. Be explicit.
- **Is it open source?** Yes (license finalized before public release).

---

## Honest marketing rules

These are binding for all website copy:

- ✅ Describe what the app **actually does today**, matching the real [ROADMAP.md](ROADMAP.md) status.
- ✅ Be upfront about the **local hardware trade-off** (results depend on the user's machine and chosen model).
- ✅ Use plain language a non-technical small-business owner understands.
- ❌ **Do not claim production-ready** until it genuinely is.
- ❌ Do not claim cloud-grade quality or speed.
- ❌ No fabricated testimonials, user counts, benchmarks, or awards.
- ❌ Do not list features, platforms, or models that aren't actually shipped/working.
- ❌ Do not imply "no setup" — be honest that Ollama + a model are required.

When in doubt, **understate and be accurate** rather than overpromise.

---

## Privacy of the website itself

- No tracking, no third-party analytics that profile visitors, by default.
- No dark patterns.
- The site practices the same privacy-first values the product preaches.
