/**
 * Central content + configuration for the Evano Studio website.
 *
 * Keeping copy here (rather than scattered across components) makes it easy to
 * review wording before launch and to keep the marketing message consistent and
 * honest. See docs/WEBSITE.md for the honest-marketing rules this content follows.
 */

export const siteConfig = {
  name: "Evano Studio",
  tagline: "Your own AI team — 100% free, in one app",
  description:
    "Evano Studio is a free, open-source desktop app for building AI agents that work for you — they chat, form teams, follow an org chart, and report to you on Discord. Everything runs locally on your Mac or Windows PC. No API keys, no subscriptions.",
  url: "https://evanostudio.com",
  /** The project is early-stage. This is shown honestly across the site. */
  status: "Alpha",

  /**
   * Set `github` to the real repository URL to activate the GitHub buttons and
   * the release download links across the whole site (one line, everything
   * lights up). Until then the site honestly offers "build from source".
   */
  links: {
    github: "https://github.com/RaulMandujano/evano-studio",
    docs: "/docs",
  },
} as const;

/** True once the GitHub link is real — drives download buttons site-wide. */
export const hasRepo = (siteConfig.links.github as string) !== "#";

/** GitHub releases page (the download source for macOS/Windows builds). */
export const releasesUrl = hasRepo ? `${siteConfig.links.github}/releases/latest` : "#";

/**
 * Direct download links — clicking these starts the download immediately.
 * GitHub's `/releases/latest/download/<asset>` always serves the newest
 * release; the asset names are stable (set in apps/desktop/electron-builder.yml).
 */
export const downloadUrls = {
  mac: hasRepo ? `${siteConfig.links.github}/releases/latest/download/Evano-Studio-mac-arm64.dmg` : "#",
  windows: hasRepo ? `${siteConfig.links.github}/releases/latest/download/Evano-Studio-Setup.exe` : "#",
} as const;

export const navLinks = [
  { href: "/", label: "Home" },
  { href: "/docs", label: "Docs" },
  { href: "/roadmap", label: "Roadmap" },
  { href: "/faq", label: "FAQ" },
  { href: "/download", label: "Download" },
] as const;

export type Feature = {
  icon: string;
  title: string;
  description: string;
};

export const features: Feature[] = [
  {
    icon: "🤖",
    title: "Create AI employees",
    description:
      "Spin up agents from templates — give them a name, an emoji, and a mission. They run on free local models (Gemma via Ollama). No code, no terminal.",
  },
  {
    icon: "🤝",
    title: "Teams that hand off work",
    description:
      "Chain agents into workflows: one researches, the next writes, the next reviews — even passing a working file from agent to agent.",
  },
  {
    icon: "🏛️",
    title: "A real org chart",
    description:
      "Give agents managers. Ask the boss for something big and it delegates to its team — enforced as real permissions, not a drawing.",
  },
  {
    icon: "🏢",
    title: "Watch them work",
    description:
      "The Office view shows your agents live: at their desk when they're busy, in the break room when they're idle.",
  },
  {
    icon: "🟣",
    title: "Your team on Discord",
    description:
      "Connect each agent as its own Discord bot with a guided flow — then manage your whole AI team from your phone.",
  },
  {
    icon: "📚",
    title: "They learn your business",
    description:
      "Import your documents into a local knowledge base (ChromaDB). Agents answer from them in the app and on Discord.",
  },
  {
    icon: "🗂️",
    title: "Tidy files (AFM)",
    description:
      "Agent File Management gives every agent a folder you choose — everything they create lands there, organized and easy to back up.",
  },
  {
    icon: "🎨",
    title: "Local image generation",
    description:
      "Agents craft prompts and generate images through a local ComfyUI — on your GPU, with no paid image APIs.",
  },
  {
    icon: "🗓️",
    title: "Routines & calendar",
    description:
      "Schedule a single agent or a whole team workflow (once, daily, weekly) and manage everything on a visual calendar.",
  },
];

export type Faq = {
  question: string;
  answer: string;
};

export const faqs: Faq[] = [
  {
    question: "Is Evano Studio really free?",
    answer:
      "Yes. There are no paid APIs, no cloud subscription, and no usage metering. You provide your own computer and free, local, open tools (Ollama and at least one local model). Optional image generation uses your own ComfyUI install.",
  },
  {
    question: "Does my data go to the cloud?",
    answer:
      "No, not by default. Models, documents, embeddings, chats, and logs stay on your machine. Nothing is uploaded unless you explicitly choose to.",
  },
  {
    question: "Do I need to use the terminal?",
    answer:
      "No. Evano Studio is a desktop control center, not a developer tool. Installing Ollama is a normal app install, and the app guides you from there. It never runs commands silently on your behalf.",
  },
  {
    question: "Which models can I use?",
    answer:
      "Any model you run through Ollama. We recommend Gemma 4 when it is available on your system, and also support Qwen, Llama, Mistral, and DeepSeek distill models.",
  },
  {
    question: "What hardware do I need?",
    answer:
      "Local AI runs on your computer, so results and speed depend on your machine. More RAM and a better GPU/CPU let you run larger, faster models. Smaller models run on more modest hardware.",
  },
  {
    question: "Do I need ComfyUI?",
    answer:
      "Only if you want local image generation. You install and run ComfyUI yourself and point Evano Studio at its local address. Everything else works without it.",
  },
  {
    question: "Is it production-ready?",
    answer:
      "Not yet — Evano Studio is in early alpha and under active development. Alpha installers for macOS and Windows are available, but they're unsigned and rough edges are expected.",
  },
  {
    question: "Is it open source?",
    answer:
      "Yes. Evano Studio is licensed under the GNU AGPL-3.0: you can use, study, modify, and share it freely. If you run a modified version as a service for others, you must share your changes under the same license — that keeps the project free for everyone.",
  },
];

export const techStack = [
  { name: "Ollama", role: "Local AI runtime for running models on your machine." },
  { name: "Gemma 4", role: "Recommended local model when available (others supported too)." },
  { name: "SQLite", role: "Stores local app data — agents, routines, and history." },
  { name: "ChromaDB (local)", role: "Powers the local knowledge base / RAG. No Chroma Cloud." },
  { name: "ComfyUI (local)", role: "Optional, user-run local image generation." },
] as const;
