# Documents & Workspace

Agents and users can create simple local documents — **Markdown**, **plain text**,
or a basic **HTML report** — saved safely inside the Evano Studio **workspace**.
Everything is local; nothing is uploaded.

## The workspace

- Default location: `<EVANO_DATA_DIR>/workspace` (default `~/.evano-studio/workspace`).
- Configurable from the desktop **Settings** page (stored as the `workspace_dir`
  setting). It's the **only** place documents and file tools can read or write.

## Creating documents

- From **Chat**, save an assistant response as a document.
- Via agent **tools** (`create_markdown_document`, `create_text_report`) when the
  agent has them enabled.
- The **Documents** page lists files; you can preview, open the file location, or
  delete them.

## Security boundaries

- Files are written **only inside the workspace**. Every path is resolved and
  checked so it can't escape the workspace root.
- File names are **sanitized** (path separators and `..` removed); directory
  traversal is rejected.
- Existing files are **not overwritten** unless explicitly allowed.
- Reads are limited to text files within a size cap.

See [SECURITY.md](SECURITY.md) for the full model and the tool permission system.
