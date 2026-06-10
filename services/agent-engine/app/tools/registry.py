"""Tool registry — the catalog of safe, local tools agents may be granted.

This is a static, curated catalog. There is intentionally NO browser/internet
tool, NO shell execution, and NO general computer-control tool in V1. Every tool
is local and operates only within the configured workspace or local services.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ToolParam:
    name: str
    type: str  # "string" | "text" | "integer"
    required: bool = False
    description: str = ""


@dataclass(frozen=True)
class ToolSpec:
    id: str
    name: str
    description: str
    category: str
    parameters: list[ToolParam] = field(default_factory=list)
    # When True, an AGENT may not run this tool automatically — it proposes the
    # action and a human must approve it first (human-in-the-loop). Manual runs
    # from the Tools page are already human-initiated, so they execute directly.
    requires_approval: bool = False


TOOLS: dict[str, ToolSpec] = {
    "create_folder": ToolSpec(
        id="create_folder",
        name="Create folder",
        description="Create a folder inside the workspace (optionally within a subfolder).",
        category="Files",
        parameters=[
            ToolParam("folder_name", "string", True, "Name of the folder to create."),
            ToolParam("parent", "string", False, "Optional parent subfolder (e.g. 'Projects')."),
        ],
    ),
    "list_files": ToolSpec(
        id="list_files",
        name="List files",
        description="List files and folders inside the workspace (or a subfolder).",
        category="Files",
        parameters=[
            ToolParam("path", "string", False, "Optional subfolder to list (default: workspace root)."),
        ],
    ),
    "create_text_file": ToolSpec(
        id="create_text_file",
        name="Create text file",
        description="Create a new file in the workspace. Fails if it already exists.",
        category="Files",
        parameters=[
            ToolParam("file_name", "string", True, "File name (e.g. 'notes.txt')."),
            ToolParam("content", "text", False, "Text content (optional; empty file if omitted)."),
            ToolParam("folder", "string", False, "Optional subfolder to create it in."),
        ],
    ),
    "read_text_file": ToolSpec(
        id="read_text_file",
        name="Read text file",
        description="Read a UTF-8 text file (.txt/.md/.html) from the workspace or a subfolder.",
        category="Files",
        parameters=[
            ToolParam("path", "string", True, "Path to the file inside the workspace."),
        ],
    ),
    "write_text_file": ToolSpec(
        id="write_text_file",
        name="Write text file",
        description="Create or overwrite a text file in the workspace with new content.",
        category="Files",
        parameters=[
            ToolParam("path", "string", True, "Path to the file inside the workspace."),
            ToolParam("content", "text", True, "Text content to write."),
        ],
    ),
    "search_workspace": ToolSpec(
        id="search_workspace",
        name="Search workspace",
        description="Search text files in the workspace by file name and content.",
        category="Files",
        parameters=[
            ToolParam("query", "string", True, "Text to search for."),
        ],
    ),
    "list_allowed_files": ToolSpec(
        id="list_allowed_files",
        name="List allowed files",
        description="List files in the workspace root folder.",
        category="Files",
        parameters=[],
    ),
    "read_allowed_text_file": ToolSpec(
        id="read_allowed_text_file",
        name="Read root text file",
        description="Read a UTF-8 text file (.txt/.md/.html) from the workspace root.",
        category="Files",
        parameters=[
            ToolParam("file_name", "string", True, "Name of the file inside the workspace root."),
        ],
    ),
    "create_markdown_document": ToolSpec(
        id="create_markdown_document",
        name="Create Markdown document",
        description="Create a Markdown (.md) document in the workspace.",
        category="Documents",
        parameters=[
            ToolParam("title", "string", True, "Document title (used for the file name)."),
            ToolParam("content", "text", True, "Markdown content."),
        ],
    ),
    "create_text_report": ToolSpec(
        id="create_text_report",
        name="Create text report",
        description="Create a plain-text (.txt) report in the workspace.",
        category="Documents",
        parameters=[
            ToolParam("title", "string", True, "Report title (used for the file name)."),
            ToolParam("content", "text", True, "Plain-text content."),
        ],
    ),
    "create_word_document": ToolSpec(
        id="create_word_document",
        name="Create Word document (.docx)",
        description="Create a real Microsoft Word (.docx) document in the workspace.",
        category="Documents",
        parameters=[
            ToolParam("title", "string", True, "Document title (used for the file name + heading)."),
            ToolParam("content", "text", False, "Body text (supports # headings and - bullets)."),
            ToolParam("folder", "string", False, "Optional subfolder to create it in."),
        ],
    ),
    "create_pdf_document": ToolSpec(
        id="create_pdf_document",
        name="Create PDF document (.pdf)",
        description="Create a real PDF document in the workspace.",
        category="Documents",
        parameters=[
            ToolParam("title", "string", True, "Document title (used for the file name + heading)."),
            ToolParam("content", "text", False, "Body text (supports # headings and - bullets)."),
            ToolParam("folder", "string", False, "Optional subfolder to create it in."),
        ],
    ),
    "search_knowledge_base": ToolSpec(
        id="search_knowledge_base",
        name="Search knowledge base",
        description="Search the local knowledge base for relevant snippets.",
        category="Knowledge",
        parameters=[
            ToolParam("query", "string", True, "What to search for."),
            ToolParam("top_k", "integer", False, "How many snippets to return (default 4)."),
        ],
    ),
    "generate_image_prompt": ToolSpec(
        id="generate_image_prompt",
        name="Generate image prompt",
        description="Compose a detailed image-generation prompt (no image is generated).",
        category="Images",
        parameters=[
            ToolParam("subject", "string", True, "Main subject of the image."),
            ToolParam("style", "string", False, "Art style (e.g. photorealistic, watercolor)."),
            ToolParam("details", "text", False, "Extra details, mood, lighting, etc."),
        ],
    ),
    # ---- Computer control (require human approval when used by an agent) ---- #
    "open_application": ToolSpec(
        id="open_application",
        name="Open application",
        description="Open an installed application on the computer (e.g. Safari, Calculator).",
        category="Computer",
        parameters=[ToolParam("app_name", "string", True, "Name of the app to open.")],
        requires_approval=True,
    ),
    "open_url": ToolSpec(
        id="open_url",
        name="Open URL",
        description="Open a web address in the default browser.",
        category="Computer",
        parameters=[ToolParam("url", "string", True, "The http/https URL to open.")],
        requires_approval=True,
    ),
    "run_command": ToolSpec(
        id="run_command",
        name="Run command",
        description="Run a shell command on the computer and return its output. "
        "Powerful — every run is shown and must be approved by a person.",
        category="Computer",
        parameters=[ToolParam("command", "string", True, "The shell command to run.")],
        requires_approval=True,
    ),
}


def list_tools() -> list[ToolSpec]:
    return list(TOOLS.values())


def get_tool(tool_id: str) -> ToolSpec | None:
    return TOOLS.get(tool_id)


def tool_exists(tool_id: str) -> bool:
    return tool_id in TOOLS
