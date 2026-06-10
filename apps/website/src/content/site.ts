/**
 * Central content + configuration for the Evano Studio website.
 *
 * Keeping copy here (rather than scattered across components) makes it easy to
 * review wording before launch and to keep the marketing message consistent and
 * honest. See docs/WEBSITE.md for the honest-marketing rules this content follows.
 */

export const siteConfig = {
  name: "Evano Studio",
  tagline: "Local AI agents without the terminal",
  description:
    "Evano Studio is a free, open-source, local-first desktop app for creating and managing local AI agents for your business — without paid APIs, cloud lock-in, or the terminal.",
  url: "https://evanostudio.com",
  /** The project is early-stage. This is shown honestly across the site. */
  status: "Alpha",

  /**
   * Placeholder links. These are intentionally not real downloads/repos yet.
   * Replace before public launch. See docs/WEBSITE.md.
   */
  links: {
    github: "#", // TODO: real GitHub URL before launch
    download: "#", // TODO: real release/download before launch (none exists yet)
    docs: "/docs",
  },
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
    title: "Local AI agents",
    description:
      "Create AI agents with a role, a local model, and explicit, deny-by-default permissions and tools. They run on your machine, not in the cloud.",
  },
  {
    icon: "💬",
    title: "Agent chat",
    description:
      "Talk to your agents through a clean desktop interface, powered entirely by local models running in Ollama.",
  },
  {
    icon: "📚",
    title: "Knowledge base (RAG)",
    description:
      "Import your own .txt/.md files into a local ChromaDB knowledge base with local embeddings, and let agents answer from them.",
  },
  {
    icon: "📄",
    title: "Documents & safe tools",
    description:
      "Agents create local documents and use a small set of approved, workspace-bound tools — no shell, no internet, no arbitrary file access.",
  },
  {
    icon: "🎨",
    title: "Image generation",
    description:
      "Agents help craft image prompts; generate images locally through your own ComfyUI when configured. No paid image APIs.",
  },
  {
    icon: "🗓️",
    title: "Routines & calendar",
    description:
      "Schedule agent tasks (manual, once, daily, weekly) and manage them on a visual calendar. Runs only while the app is open.",
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
      "No. Evano Studio is in early alpha and under active development. There is no public download yet. Expect rough edges and changes.",
  },
  {
    question: "Is it open source?",
    answer:
      "Yes. Evano Studio is being built as an open-source project. The license will be finalized before the first public release.",
  },
];

export const techStack = [
  { name: "Ollama", role: "Local AI runtime for running models on your machine." },
  { name: "Gemma 4", role: "Recommended local model when available (others supported too)." },
  { name: "SQLite", role: "Stores local app data — agents, routines, and history." },
  { name: "ChromaDB (local)", role: "Powers the local knowledge base / RAG. No Chroma Cloud." },
  { name: "ComfyUI (local)", role: "Optional, user-run local image generation." },
] as const;
