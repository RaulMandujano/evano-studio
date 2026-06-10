# Agents

Agents are the core concept of Evano Studio. This document defines what an agent is, how it's configured, and the permission/tool model that keeps it safe. It is a design document — **no agent code exists yet**.

---

## What is an agent?

An **agent** is a configured, named AI helper that a user creates to do a specific kind of work — a local AI "employee" for their business. Each agent:

- Is powered by a **local model** running in Ollama (no cloud).
- Has a **role and a system prompt** that shape how it behaves.
- Has an **explicit, limited set of permissions and tools** — it can do nothing beyond chatting unless the user grants more.
- Runs entirely on the user's machine.

Agents are meant to feel approachable to non-technical users: you describe what you want the agent to do, pick what it's allowed to access, and talk to it.

---

## Agent config fields

An agent definition (stored in SQLite) includes at least:

| Field | Description |
| --- | --- |
| `id` | Unique identifier. |
| `name` | Human-friendly name (e.g., "Marketing Assistant"). |
| `description` / `role` | What the agent is for, in plain language. |
| `model` | Which locally installed Ollama model to use (validated against installed models). |
| `system_prompt` | Instructions that define the agent's behavior and tone. |
| `permissions` | The set of capabilities granted to this agent (deny-by-default). |
| `enabled_tools` | The specific tools this agent may use. |
| `workspace_scope` | Which approved workspace folder(s) the agent may access. |
| `knowledge_bases` | Which knowledge base collections (if any) the agent may search. |
| `created_at` / `updated_at` | Timestamps. |

Defaults are conservative: a new agent starts with **no tools and no permissions** beyond chat.

---

## Permissions model

Permissions are **deny-by-default** and enforced **in the backend** (see [SECURITY.md](SECURITY.md)).

- An agent can only do what it has been explicitly granted.
- Permissions are **per-agent** — granting one agent a capability never affects another.
- Permissions gate **categories** of capability, for example:
  - **Chat** (always available).
  - **Read/write documents** in the agent's workspace scope.
  - **Search the knowledge base** (RAG).
  - **Generate image prompts.**
  - **Generate images** (requires ComfyUI configured).
- The UI makes permissions visible and easy to toggle, in language non-technical users understand.
- The backend re-checks permissions on **every** request — the UI is never trusted to enforce them.

---

## Tools model

A **tool** is a concrete capability the agent can invoke during a task (e.g., "save a document", "search knowledge base", "request an image generation"). The tool model is intentionally constrained:

- **An agent can only use tools that are explicitly enabled for it.** A disabled tool is unreachable.
- **Tools can only access approved workspace folders.** File tools are confined to the agent's `workspace_scope`; directory traversal is blocked.
- **Tools that use external services** (knowledge base via ChromaDB, image generation via ComfyUI) are gated both by their permission and by that service being available/configured.
- **There is no arbitrary-command or shell tool** in V1. Agents cannot run system commands (see [SECURITY.md](SECURITY.md)).
- Tool invocations are **validated and logged** (without sensitive content) so users can see what an agent did.

Tools are kept small and composable so new ones can be added in later phases without expanding the agent's reach unexpectedly.

---

## Agent examples for businesses

Illustrative V1-scope agents (these are examples of what users could create, not prebuilt promises):

- **Knowledge Assistant** — given a knowledge base of company documents, answers staff questions by searching it (RAG) and drafting responses.
- **Document Drafter** — writes proposals, summaries, or product descriptions and saves them to the workspace.
- **Marketing Helper** — turns a product idea into social copy and **image prompts**, and (if ComfyUI is configured) generates images.
- **Onboarding Buddy** — answers new-hire questions from an internal handbook stored in the knowledge base.
- **Weekly Report Routine** — paired with a routine, drafts a recurring summary document on a schedule (see [ROUTINES_AND_CALENDAR.md](ROUTINES_AND_CALENDAR.md)).

Each of these is just an agent config (model + system prompt + permissions + tools), not special-cased code.

---

## What agents CAN do

- Chat with the user using a local model.
- Read/write documents **within their approved workspace folders** (when permitted).
- Search a knowledge base the user has given them (when permitted).
- Generate image prompts (when permitted).
- Generate images via a configured local ComfyUI (when permitted and available).
- Run as part of a scheduled routine (when set up).

## What agents CANNOT do

- ❌ Execute arbitrary system or shell commands.
- ❌ Access files outside their approved workspace scope.
- ❌ Use tools that haven't been explicitly enabled for them.
- ❌ Reach the network/cloud or call paid APIs.
- ❌ Install software or change system settings.
- ❌ Bypass permissions via the UI — the backend is the enforcer.
- ❌ Read another agent's granted capabilities or scope.

This conservative model is what makes it safe to let a local model act on the user's behalf.
