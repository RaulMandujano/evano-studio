# Free by Default

This document explains a core promise of Evano Studio: it is **free by default** and stays that way. "Free" here means no paid services are required to use the product — not a free trial, not a freemium upsell.

> **User promise:** Create local AI agents for your business — without paid APIs, without cloud lock-in, and without touching the terminal.

---

## What "free by default" means

- **No paid API requirement.** Evano Studio never requires a paid LLM API key. All language-model inference runs locally through [Ollama](https://ollama.com).
- **No cloud database requirement.** There is no hosted database to sign up for. App data lives in a local SQLite file on your machine.
- **No Chroma Cloud.** The knowledge base uses ChromaDB in **local persistent mode only**. The hosted Chroma Cloud product is never used or required. See [RAG_WITH_CHROMADB.md](RAG_WITH_CHROMADB.md).
- **No paid vector database.** No Pinecone, Weaviate Cloud, or any metered vector service. Embeddings and vectors are stored locally.
- **No paid image API.** No DALL·E, Midjourney API, or any paid image service. Image generation is optional and runs locally through a ComfyUI instance you control. See [COMFYUI_INTEGRATION.md](COMFYUI_INTEGRATION.md).
- **No subscription, no metering, no usage caps** imposed by Evano Studio itself.

The app is also intended to be **open source**, so you can verify all of the above.

---

## Why this matters

Most "AI for your business" tools route your data through paid cloud APIs. That means recurring cost, vendor lock-in, and your private business data leaving your machine. Evano Studio takes the opposite stance: the value is in the **professional, easy-to-use experience** wrapped around free, local, open tools — not in reselling cloud access.

---

## What users still need (locally)

Evano Studio is free, but AI still needs to run somewhere. That somewhere is **your own computer**. To use the app you provide:

1. **Your own computer.** Local AI models need a reasonably capable machine. More RAM and a better GPU/CPU mean larger, faster models. Small models run on modest hardware.
2. **Ollama.** The local AI runtime. You install it once. Evano Studio detects it and guides you — it does **not** install it silently (see [SECURITY.md](SECURITY.md)).
3. **At least one local model.** Pulled through Ollama. Recommended: **Gemma (3/4 class)** when available; also supported: Qwen, Llama, Mistral, DeepSeek distill. These models are free to download and run locally.
4. **(Optional) ComfyUI** — only if you want local image generation. You install and run it yourself and point Evano Studio at its local URL. Without it, every other feature still works.

That's the full cost: your hardware and free, open tools. **No bills, no API keys, no cloud account.**

---

## What this is NOT

- It is **not** a free trial of a paid product.
- It is **not** "free up to N requests, then pay."
- It does **not** secretly call a cloud service to make features work.
- It does **not** require you to create any online account.

---

## Honesty about the trade-off

Free and local means the quality and speed of results depend on **your hardware and the local models you choose**, not on a powerful cloud model. This is a deliberate trade: privacy, zero cost, and no lock-in in exchange for running within your machine's limits.

The website and app must communicate this honestly and never imply cloud-grade performance on modest local hardware. See [WEBSITE.md](WEBSITE.md) for the honest-marketing rules.

---

## Rules for contributors

To keep this promise intact, any change must respect:

- ❌ Do not add a required paid API, paid database, or paid image/embedding service.
- ❌ Do not add Chroma Cloud or any hosted vector database.
- ❌ Do not add cloud uploads or remote inference as a default.
- ✅ Optional integrations are acceptable **only if** the app is fully usable without them and they are off by default.
- ✅ If a feature genuinely cannot be done locally for free, it does not belong in V1.

See the V1 "not included" list in [ROADMAP.md](ROADMAP.md).
