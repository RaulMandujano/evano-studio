/**
 * Documentation content as data (no MDX dependency).
 *
 * Each article is a list of simple blocks rendered by components/docs/DocBody.
 * Keep wording honest and aligned with what the app actually does — alpha,
 * local-first, and clear that Ollama/ComfyUI may need local installation.
 */

export type DocBlock =
  | { type: "p"; text: string }
  | { type: "h"; text: string }
  | { type: "ul"; items: string[] }
  | { type: "ol"; items: string[] }
  | { type: "code"; code: string }
  | { type: "callout"; text: string };

export interface DocArticle {
  slug: string;
  title: string;
  description: string;
  blocks: DocBlock[];
}

export interface DocGroup {
  title: string;
  slugs: string[];
}

export const docArticles: DocArticle[] = [
  {
    slug: "getting-started",
    title: "Getting started",
    description: "What Evano Studio is and what you need before you begin.",
    blocks: [
      {
        type: "callout",
        text: "Evano Studio is in alpha. It's not production-ready — expect rough edges and changes.",
      },
      {
        type: "p",
        text: "Evano Studio is a free, open-source, local-first desktop app for creating and managing local AI agents — without paid APIs, cloud lock-in, or the terminal.",
      },
      { type: "h", text: "What you need" },
      {
        type: "ul",
        items: [
          "Your own computer (more RAM/GPU means larger, faster local models).",
          "Ollama installed, plus at least one local model (the app helps you install models).",
          "Optional: ComfyUI installed locally, only if you want image generation.",
        ],
      },
      {
        type: "p",
        text: "No paid AI API is required by default. Your models, documents, and data stay on your machine.",
      },
      { type: "h", text: "First steps" },
      {
        type: "ol",
        items: [
          "Install Ollama and a local model (see the next two guides).",
          "Open Evano Studio — the Dashboard shows the status of each local service.",
          "Create your first agent and chat with it.",
        ],
      },
    ],
  },
  {
    slug: "install-ollama",
    title: "Install Ollama",
    description: "Ollama is the free local runtime that powers Evano Studio's AI.",
    blocks: [
      {
        type: "p",
        text: "Ollama runs AI models locally on your machine. Evano Studio talks to it over localhost — it never installs software for you silently.",
      },
      { type: "h", text: "Install" },
      {
        type: "ol",
        items: [
          "Download Ollama from ollama.com and run the installer for your OS.",
          "Start Ollama (it runs a local service at http://localhost:11434).",
          "In Evano Studio, open the Dashboard or Settings — the Ollama status should show as running.",
        ],
      },
      {
        type: "callout",
        text: "Installing Ollama is a normal app install — not a terminal task. Evano Studio guides you and links to the official download.",
      },
    ],
  },
  {
    slug: "install-model",
    title: "Install a local model",
    description: "Pull a free local model so your agents have a brain.",
    blocks: [
      {
        type: "p",
        text: "Models are downloaded once and run locally. In Evano Studio you can install recommended models from the Models page — no terminal needed.",
      },
      { type: "h", text: "From the app" },
      {
        type: "ol",
        items: [
          "Open the Models page.",
          "Pick a recommended model (e.g. Gemma, Qwen for coding, Llama for chat, Mistral, or a DeepSeek distill).",
          "Click Install and watch the progress. Models are large (often 2–5 GB) — make sure you have disk space and RAM.",
        ],
      },
      { type: "h", text: "Advanced (optional)" },
      {
        type: "p",
        text: "If you prefer the terminal, you can also pull a model directly with Ollama:",
      },
      { type: "code", code: "ollama pull gemma3:4b" },
      {
        type: "callout",
        text: "Use the exact model tag (e.g. gemma3:4b) when configuring an agent — a family name alone may not match an installed model.",
      },
    ],
  },
  {
    slug: "first-agent",
    title: "Create your first agent",
    description: "Configure a local AI agent and chat with it.",
    blocks: [
      {
        type: "p",
        text: "An agent is a named AI helper with a role, a model, and an explicit set of permissions and tools. It runs entirely on your machine.",
      },
      { type: "h", text: "Create an agent" },
      {
        type: "ol",
        items: [
          "Open the Agents page and click New Agent.",
          "Give it a name and a system prompt that describes how it should behave.",
          "Choose an installed model and set a temperature.",
          "Turn on only the tools and capabilities it needs (deny-by-default).",
          "Save, then open the Chat page to talk to it.",
        ],
      },
      {
        type: "p",
        text: "Responses are streamed from your local model — nothing is sent to the cloud.",
      },
    ],
  },
  {
    slug: "documents",
    title: "Create documents",
    description: "Let agents draft documents saved to your local workspace.",
    blocks: [
      {
        type: "p",
        text: "Agents (and you) can create simple local documents — Markdown, plain text, or a basic HTML report — saved safely inside your Evano Studio workspace.",
      },
      { type: "h", text: "How it works" },
      {
        type: "ul",
        items: [
          "Documents are written only inside the workspace folder; file names are sanitized and directory traversal is blocked.",
          "From the Chat page you can save an assistant response as a document.",
          "The Documents page lists your files; you can preview, open the file location, or delete them.",
        ],
      },
      {
        type: "p",
        text: "You can change the workspace folder on the Settings page.",
      },
    ],
  },
  {
    slug: "import-knowledge",
    title: "Import knowledge base documents",
    description: "Add your own .txt/.md files to a local knowledge base.",
    blocks: [
      {
        type: "p",
        text: "The knowledge base lets your agents answer from your own content using local retrieval (RAG), powered by a local ChromaDB — no cloud, no paid vector database.",
      },
      { type: "h", text: "Import a document" },
      {
        type: "ol",
        items: [
          "Open the Knowledge Base page.",
          "Click Import and choose a .txt or .md file (plain-text extraction for V1).",
          "Evano Studio chunks and embeds it locally and adds it to the knowledge base.",
        ],
      },
      {
        type: "callout",
        text: "The first import downloads a small local embedding model (about 80 MB) once. It runs on your machine — no API key, no cloud.",
      },
    ],
  },
  {
    slug: "rag",
    title: "Use local ChromaDB RAG",
    description: "Ground an agent's answers in your knowledge base.",
    blocks: [
      {
        type: "p",
        text: "Retrieval-augmented generation (RAG) finds the most relevant snippets from your knowledge base and adds them to the agent's prompt, so answers are grounded in your documents.",
      },
      { type: "h", text: "Enable it" },
      {
        type: "ol",
        items: [
          "Import documents into the knowledge base.",
          "Edit an agent and turn on Knowledge base (RAG).",
          "Chat with the agent — relevant snippets are retrieved locally and the reply shows its sources.",
        ],
      },
      {
        type: "p",
        text: "Everything stays local: embeddings, search, and storage all happen on your machine. ChromaDB runs in local persistent mode only — never Chroma Cloud.",
      },
    ],
  },
  {
    slug: "comfyui",
    title: "Set up ComfyUI (local)",
    description: "Optional local image generation through your own ComfyUI.",
    blocks: [
      {
        type: "callout",
        text: "ComfyUI is optional and external — you install and run it yourself. Every other Evano Studio feature works without it.",
      },
      { type: "h", text: "Set up" },
      {
        type: "ol",
        items: [
          "Install and run ComfyUI locally, with at least one image model/checkpoint.",
          "In Evano Studio, open the Images page, enter your local ComfyUI URL (e.g. http://127.0.0.1:8188), enable it, and save.",
          "For best results, export your own workflow from ComfyUI (Save in API format) and point Evano Studio at it.",
        ],
      },
      {
        type: "p",
        text: "When configuring your own workflow, include the tokens %positive_prompt% and %negative_prompt% in the prompt nodes so Evano Studio can inject your prompts.",
      },
      {
        type: "p",
        text: "No paid image API is ever used. If ComfyUI isn't configured, image generation is simply disabled.",
      },
    ],
  },
  {
    slug: "images",
    title: "Generate images",
    description: "Craft image prompts and generate locally with ComfyUI.",
    blocks: [
      {
        type: "p",
        text: "Agents can help you write strong image prompts, and — when ComfyUI is configured and the agent is image-enabled — you can generate images locally.",
      },
      { type: "h", text: "Generate" },
      {
        type: "ol",
        items: [
          "On the Images page (or in Chat's image tools), describe an idea and create a prompt.",
          "Edit the prompt if you like.",
          "Click Generate — the image is created by your local ComfyUI and saved to your workspace.",
        ],
      },
      {
        type: "callout",
        text: "Nothing generates automatically. Image generation only happens when you explicitly click Generate.",
      },
    ],
  },
  {
    slug: "routines",
    title: "Create routines",
    description: "Schedule repeatable agent tasks locally.",
    blocks: [
      {
        type: "p",
        text: "Routines run an agent task on a schedule: manual (on demand), once, daily, or weekly.",
      },
      { type: "h", text: "Create a routine" },
      {
        type: "ol",
        items: [
          "Open the Routines page and click New Routine.",
          "Pick an agent, write the task prompt, and choose a schedule.",
          "Use Run now to test it; runs are logged with their output.",
        ],
      },
      {
        type: "callout",
        text: "Routines only run while Evano Studio is open. It is not a background cloud service — runs missed while the app was closed are recorded as 'missed', not run late.",
      },
    ],
  },
  {
    slug: "calendar",
    title: "Use the visual calendar",
    description: "See and manage routines on a calendar.",
    blocks: [
      {
        type: "p",
        text: "The Calendar shows your scheduled routines and past runs at a glance — in plain language, no cron syntax.",
      },
      { type: "h", text: "What you can do" },
      {
        type: "ul",
        items: [
          "Switch between Month and Week views and navigate with Today / arrows.",
          "See upcoming runs and past runs colored by outcome (success, error, missed).",
          "Click an event to view a routine, run it now, enable/disable, edit, or delete it.",
          "Create a new routine directly from the calendar.",
        ],
      },
    ],
  },
  {
    slug: "troubleshooting",
    title: "Troubleshooting",
    description: "Common issues and how to fix them locally.",
    blocks: [
      { type: "h", text: "Agent Engine offline" },
      {
        type: "p",
        text: "Evano Studio's local backend isn't running. Start it (Settings → Local services), then refresh.",
      },
      { type: "h", text: "Ollama not detected" },
      {
        type: "p",
        text: "Make sure Ollama is installed and running. The Dashboard and Settings show its status; the Models page links to the official download.",
      },
      { type: "h", text: "No models installed" },
      {
        type: "p",
        text: "Install a model from the Models page. Set your agent's model to an exact installed tag (e.g. gemma3:4b).",
      },
      { type: "h", text: "Knowledge base unavailable" },
      {
        type: "p",
        text: "ChromaDB couldn't initialize locally, or the first embedding model download needs network access. Evano Studio shows a clear local-setup message and never falls back to the cloud.",
      },
      { type: "h", text: "Images won't generate" },
      {
        type: "p",
        text: "Confirm ComfyUI is installed, running, reachable at the configured URL, and that your agent is image-enabled.",
      },
      { type: "h", text: "Reporting a problem" },
      {
        type: "p",
        text: "Use Logs → Export support bundle. It collects non-sensitive diagnostics (versions, statuses, recent logs) and excludes your chats, documents, and secrets by default. Nothing is uploaded.",
      },
    ],
  },
  {
    slug: "privacy",
    title: "Privacy",
    description: "Local-first and privacy-first by design.",
    blocks: [
      {
        type: "p",
        text: "Evano Studio runs on your computer. Your models, documents, knowledge base, chats, and logs stay on your machine. Nothing is uploaded to the cloud by default.",
      },
      {
        type: "ul",
        items: [
          "AI inference runs locally via Ollama — no remote model calls.",
          "The knowledge base uses local ChromaDB and local embeddings.",
          "Support bundles exclude private chat and document contents by default.",
          "No tracking, no account, no paid API calls.",
        ],
      },
      {
        type: "p",
        text: "See the full Privacy page for more detail.",
      },
    ],
  },
  {
    slug: "free-by-default",
    title: "Free by default",
    description: "No paid APIs, no cloud database, no lock-in.",
    blocks: [
      {
        type: "p",
        text: "Evano Studio is free by default — not a trial, not freemium. No paid AI API, no cloud database, no Chroma Cloud, no paid vector DB, and no paid image API are required.",
      },
      { type: "h", text: "What you still provide locally" },
      {
        type: "ul",
        items: [
          "Your own computer — local AI runs on your hardware.",
          "Ollama and at least one local model (free to download).",
          "Optional ComfyUI, only for local image generation.",
        ],
      },
      {
        type: "callout",
        text: "Results and speed depend on your hardware and the local models you choose — this is the trade-off for privacy, zero cost, and no lock-in.",
      },
    ],
  },
];

export const docGroups: DocGroup[] = [
  { title: "Getting started", slugs: ["getting-started", "install-ollama", "install-model", "first-agent"] },
  { title: "Working locally", slugs: ["documents", "import-knowledge", "rag"] },
  { title: "Images & automation", slugs: ["comfyui", "images", "routines", "calendar"] },
  { title: "Reference", slugs: ["troubleshooting", "privacy", "free-by-default"] },
];

export function getDoc(slug: string): DocArticle | undefined {
  return docArticles.find((d) => d.slug === slug);
}
