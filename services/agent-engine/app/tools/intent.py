"""Deterministic tool-intent detection for agent chat (English + Spanish).

This maps a natural-language message to a single, unambiguous tool call using
narrow regular expressions — NOT a language model. It is intentionally
conservative: it only fires on clear, imperative requests so ordinary chat is
never hijacked. There is NO autonomous multi-step loop; a message resolves to at
most one tool call.

A detected intent may carry a :class:`ContentDirective` describing how the
backend should obtain the document/file content (the orchestrator resolves it):

- ``literal``      — the user gave the content verbatim ("that says ...").
- ``generate``     — the model should write content about a topic ("about ...").
- ``from_history`` — save the previous assistant reply ("save this as a doc").

See docs/TOOLS.md.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ContentDirective:
    mode: str  # "literal" | "generate" | "from_history"
    text: str = ""
    topic: str = ""


@dataclass(frozen=True)
class ToolIntent:
    tool_id: str
    params: dict = field(default_factory=dict)
    # For document/file/report tools: the requested name and how to get content.
    name: str = ""
    content: ContentDirective | None = None


# ---- shared vocabulary ---------------------------------------------------- #

_CREATE_VERBS = (
    r"(?:create|make|write|generate|build|add|"
    r"crea|cr[eé]ame|creame|crear|haz|hazme|genera|generar|gen[eé]rame|"
    r"escribe|escribir|escr[ií]beme|redacta|redactar|a[nñ]ade|a[nñ]adir|agrega|agregar|"
    r"guarda|guardar|nuevo|nueva|quiero|necesito|deseo|dame|ponme|pon)"
)
# An optional middle verb (incl. Spanish subjunctive), e.g. "quiero que CREES una
# carpeta", "necesito que HAGAS un archivo", "quiero CREAR un documento".
_MID_VERB = (
    r"(?:crear|crea|crees|cree|cr[eé]ame|creame|hacer|haz|hagas|haga|hazme|"
    r"generar|genera|generes|genere|gen[eé]rame|escribir|escribe|escribas|escr[ií]beme|"
    r"create|make|generate|write|guardar|guarda|guardes|a[nñ]adir|add)"
)
_POLITE = r"(?:please\s+|por\s+favor\s+)?(?:can you\s+|could you\s+|puedes\s+|podr[ií]as\s+|me\s+)?"
_ARTICLE = r"(?:a\s+|an\s+|the\s+|one\s+|un\s+|una\s+|el\s+|la\s+|unos\s+|unas\s+)?"
_NEW = r"(?:new\s+|nuev[oa]\s+)?"

_NAME_AFTER = re.compile(
    r"(?:called|named|titled|with name|with the name|with the title|"
    r"llamad[oa]|titulad[oa]|de nombre|con nombre|con el nombre|con el t[ií]tulo)\s+(?P<name>.+)$",
    re.IGNORECASE,
)
_CONTENT_MARKER = re.compile(
    r"\b(?:that says|saying|which says|with (?:the )?content|with (?:the )?text|"
    r"containing|that contains|with body|que dig[ae]|que dice|con (?:el )?contenido|"
    r"con (?:el )?texto|que contenga|que contiene|cuyo contenido sea)\s+(?P<content>.+)$",
    re.IGNORECASE,
)
_TOPIC_MARKER = re.compile(
    r"\b(?:about|regarding|on the topic of|with a summary of|summari[sz]ing|"
    r"sobre|acerca de|que trate sobre|que hable de|del tema|"
    r"con un resumen de|con un resumen sobre|con un resumen acerca de|que resuma)\s+(?P<topic>.+)$",
    re.IGNORECASE,
)

_KIND_TOOL = {
    "folder": "create_folder",
    "directory": "create_folder",
    "subfolder": "create_folder",
    "carpeta": "create_folder",
    "directorio": "create_folder",
    "subcarpeta": "create_folder",
    "markdown document": "create_markdown_document",
    "md document": "create_markdown_document",
    "document": "create_markdown_document",
    "documento": "create_markdown_document",
    "note": "create_markdown_document",
    "nota": "create_markdown_document",
    "text file": "create_text_file",
    "file": "create_text_file",
    "archivo": "create_text_file",
    "fichero": "create_text_file",
    "report": "create_text_report",
    "reporte": "create_text_report",
    "informe": "create_text_report",
}
# Longest kinds first so "markdown document" wins over "document".
_KINDS_ALT = "|".join(sorted((re.escape(k) for k in _KIND_TOOL), key=len, reverse=True))

_CREATE_HEAD = re.compile(
    rf"^{_POLITE}{_CREATE_VERBS}\s+(?:que\s+)?(?:me\s+)?(?:{_MID_VERB}\s+)?(?:me\s+)?"
    rf"{_ARTICLE}{_NEW}(?P<kind>{_KINDS_ALT})(?P<rest>\b.*)$",
    re.IGNORECASE,
)

# "save this as a document", "guarda esto como un documento"
_SAVE_AS = re.compile(
    r"^" + _POLITE +
    r"(?:save|store|guarda|guardar|almacena)\s+"
    r"(?:this|that|it|the (?:last )?(?:reply|answer|response|message)|"
    r"esto|eso|la (?:[uú]ltima )?respuesta|el (?:[uú]ltimo )?mensaje)\s+"
    r"(?:as|como)\s+" + _ARTICLE +
    r"(?P<kind>markdown document|document|md|note|text file|file|report|"
    r"documento|nota|archivo|reporte|informe)\b(?P<rest>.*)$",
    re.IGNORECASE,
)

_LIST = re.compile(
    r"^" + _POLITE +
    r"(?:list|show|display|lista|listar|muestra|mostrar|ver|enumera)\s+"
    r"(?:me\s+)?(?:the\s+|my\s+|all\s+(?:the\s+)?|mis\s+|los\s+|las\s+|todos\s+(?:los\s+)?)?"
    r"(?:workspace\s+|del\s+workspace\s+)?(?:files|archivos|ficheros|documents|documentos)\b"
    r"(?:\s+(?:in|inside|under|within|en|dentro de)\s+(?:the\s+|la\s+|el\s+)?(?P<path>.+?))?[.!?]?$",
    re.IGNORECASE,
)

_READ = re.compile(
    r"^" + _POLITE +
    r"(?:read|open|lee|leer|abre|abrir|muestrame|mu[eé]strame|show me)\s+"
    r"(?:me\s+)?(?:the\s+|el\s+|la\s+)?(?:contents?\s+of\s+|contenido de\s+)?(?:text\s+)?"
    r"(?:file|archivo|fichero)\s+[\"']?(?P<path>[\w .\-/\\]+?)[\"']?[.!?]?$",
    re.IGNORECASE,
)

_SEARCH = re.compile(
    r"^" + _POLITE +
    r"(?:search|find|look|busca|buscar|encuentra)\s+"
    r"(?:(?:in\s+|through\s+|en\s+)?(?:the\s+|el\s+)?(?:workspace|espacio de trabajo)\s+(?:for\s+|por\s+|de\s+)?"
    r"|(?:for\s+)?(?:files?|archivos?)\s+(?:containing|with|que contengan|con)\s+)"
    r"[\"']?(?P<query>.+?)[\"']?[.!?]?$",
    re.IGNORECASE,
)

_PARENT_SPLIT = re.compile(
    r"^(?P<name>.+?)\s+(?:in|inside|under|within|dentro de|en)\s+(?:the\s+|la\s+|el\s+)?(?P<parent>.+?)(?:\s+folder|\s+carpeta)?$",
    re.IGNORECASE,
)

_DOC_EXT = re.compile(r"\.(md|markdown)$", re.IGNORECASE)


def _clean(value: str) -> str:
    return (value or "").strip().strip("\"'").strip(" .")


def _split_parent(name: str) -> tuple[str, str]:
    m = _PARENT_SPLIT.match(name)
    if m:
        return _clean(m.group("name")), _clean(m.group("parent"))
    return _clean(name), ""


def _parse_doc_command(rest: str, tool_id: str) -> ToolIntent | None:
    """Parse the tail of a create-document/file/report command."""
    content: ContentDirective | None = None
    residual = rest

    mc = _CONTENT_MARKER.search(residual)
    if mc:
        content = ContentDirective(mode="literal", text=_clean(mc.group("content")))
        residual = residual[: mc.start()]
    else:
        mt = _TOPIC_MARKER.search(residual)
        if mt:
            content = ContentDirective(mode="generate", topic=_clean(mt.group("topic")))
            residual = residual[: mt.start()]

    residual = residual.strip()
    name = ""
    mn = _NAME_AFTER.search(residual)
    if mn:
        name = _clean(mn.group("name"))
    elif residual:
        cand = _clean(residual)
        # A bare leftover is only treated as a name if it's short (avoids junk).
        if cand and len(cand.split()) <= 6:
            name = cand

    # If there is no explicit content but we do have a name or topic, generate
    # content for it. With nothing at all, fall through to normal chat.
    if content is None:
        if name:
            content = ContentDirective(mode="generate", topic=_DOC_EXT.sub("", name))
        else:
            return None

    return ToolIntent(tool_id=tool_id, name=name, content=content)


def _parse_folder_command(rest: str) -> ToolIntent | None:
    residual = rest.strip()
    mn = _NAME_AFTER.search(residual)
    if mn:
        raw = _clean(mn.group("name"))
    elif residual:
        cand = _clean(residual)
        # Bare "folder X" only if short, to avoid creating junk folders.
        raw = cand if cand and len(cand.split()) <= 5 else ""
    else:
        raw = ""
    if not raw:
        return None
    name, parent = _split_parent(raw)
    if not name:
        return None
    params = {"folder_name": name}
    if parent:
        params["parent"] = parent
    return ToolIntent(tool_id="create_folder", params=params)


def detect_tool_intent(message: str) -> ToolIntent | None:
    """Return a single ToolIntent for a clear tool request, else None."""
    text = (message or "").strip()
    if not text or len(text) > 600:
        return None

    # "save this as a document" → save the previous assistant reply.
    m = _SAVE_AS.match(text)
    if m:
        kind = m.group("kind").lower()
        tool_id = _KIND_TOOL.get(kind, "create_markdown_document")
        if tool_id == "create_folder":  # nonsensical for "save as"
            tool_id = "create_markdown_document"
        name = ""
        mn = _NAME_AFTER.search(m.group("rest").strip())
        if mn:
            name = _clean(mn.group("name"))
        return ToolIntent(tool_id=tool_id, name=name, content=ContentDirective(mode="from_history"))

    # create folder / document / file / report
    m = _CREATE_HEAD.match(text)
    if m:
        tool_id = _KIND_TOOL[m.group("kind").lower()]
        rest = m.group("rest") or ""
        if tool_id == "create_folder":
            return _parse_folder_command(rest)
        return _parse_doc_command(rest, tool_id)

    m = _LIST.match(text)
    if m:
        path = _clean(m.group("path") or "")
        return ToolIntent("list_files", {"path": path} if path else {})

    m = _SEARCH.match(text)
    if m:
        query = _clean(m.group("query"))
        if query:
            return ToolIntent("search_workspace", {"query": query})

    m = _READ.match(text)
    if m:
        path = _clean(m.group("path"))
        if path:
            return ToolIntent("read_text_file", {"path": path})

    return None
