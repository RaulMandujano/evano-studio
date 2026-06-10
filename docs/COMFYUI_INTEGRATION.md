# ComfyUI Integration

Evano Studio can generate images locally through **ComfyUI**, treated as an **optional external local service**. This is a design document — **no code exists yet**.

---

## ComfyUI as an optional external local service

- Image generation is **entirely optional**. Every other feature of Evano Studio works without it.
- ComfyUI is an **external local service** that the **user installs and runs themselves**.
- Evano Studio talks to it over its **local HTTP API** through a thin adapter (`adapters/comfyui.py`, see [ARCHITECTURE.md](ARCHITECTURE.md)).
- If ComfyUI is **not configured**, image-generation features are cleanly **disabled** in the UI — no errors, no broken screens.

## No copied ComfyUI source

- Evano Studio **does not copy, bundle, fork, or reimplement ComfyUI source code.**
- It only **communicates with** a separately installed ComfyUI instance.
- This keeps licensing clean, keeps Evano Studio lean, and lets users update ComfyUI independently.

## No paid image API

- **No DALL·E, Midjourney API, Stability API, or any paid/cloud image service** is used (see [FREE_BY_DEFAULT.md](FREE_BY_DEFAULT.md)).
- All image generation runs **locally** through the user's own ComfyUI.

---

## Local URL configuration

- The user configures ComfyUI's **local URL** in Evano Studio settings (e.g., `http://127.0.0.1:8188`).
- The backend uses this URL to reach ComfyUI; it expects a **local/loopback address** by design.
- On configuration (and on startup), the backend **checks whether ComfyUI is reachable** and reports a clear status.
- If unreachable, the app shows plain-language guidance instead of failing silently (see [DEVELOPMENT_RULES.md](DEVELOPMENT_RULES.md) error-handling expectations).

---

## Prompt workflow

1. An agent (or the user) produces an **image prompt** — this prompt-generation step works even without ComfyUI.
2. If the user chooses to generate an image and ComfyUI is configured, the backend sends a **workflow/prompt request** to ComfyUI's local API.
3. The backend **polls ComfyUI for completion**.
4. On success, the resulting image is retrieved and **saved to the workspace**.

- V1 ships with a **sensible default workflow** so non-technical users can generate an image from a prompt without building a ComfyUI graph themselves.
- Advanced, fully custom ComfyUI workflows are not a V1 requirement (kept simple to avoid overbuilding — see [ROADMAP.md](ROADMAP.md)).

---

## Image storage

- Generated images are saved under the user's **local workspace** (`data/workspace/`, or the per-user app dir when packaged).
- Images stay within the **agent's approved workspace scope** — directory traversal is prevented (see [SECURITY.md](SECURITY.md)).
- Image metadata (prompt used, agent, timestamp) may be recorded so the user can find and reuse results.
- **No image is uploaded anywhere.** Everything stays on the machine.

---

## User setup requirements

To use image generation, the user must:

1. **Install ComfyUI** themselves (Evano Studio does not install it — no silent installs, see [SECURITY.md](SECURITY.md)).
2. **Download at least one image model** that their ComfyUI setup uses.
3. **Run ComfyUI locally.**
4. **Enter the local ComfyUI URL** in Evano Studio settings.
5. Grant the relevant agent the **image-generation permission/tool** (see [AGENTS.md](AGENTS.md)).

The website download/docs pages must explain this honestly and link to official ComfyUI resources (see [WEBSITE.md](WEBSITE.md)).

---

## Limitations

- **Optional and self-managed:** if ComfyUI isn't installed/running/configured, image generation is unavailable — by design.
- **Performance depends on the user's hardware** and the image models they installed (image generation is GPU-intensive).
- **Evano Studio does not manage ComfyUI's models or workflows** beyond sending requests to it.
- **Compatibility** depends on the user's ComfyUI version; the adapter targets its stable local API and the default workflow.
- **No cloud fallback** — there is no paid service to fall back to if local generation is slow or unavailable.
