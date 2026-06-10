"""Ready-made agent templates for non-technical users.

One-click starting points so someone who doesn't know tech can create a useful
agent without writing a system prompt or picking tools. The desktop pre-fills
the create form from a template; the user can still tweak everything. Tools are
referenced by id from ``tools/registry.py`` and remain deny-by-default + (for
computer control) approval-gated.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .schemas.agent import AgentTemplate


# Defined as plain dicts so this module has no import-time dependencies on the
# schema package ordering; the API layer validates them into AgentTemplate.
AGENT_TEMPLATES: list[dict] = [
    {
        "id": "office-assistant",
        "name": "Asistente de oficina",
        "icon": "🗂️",
        "description": "Organiza archivos, crea carpetas y documentos en tu workspace.",
        "system_prompt": (
            "Eres un asistente de oficina práctico y amable. Ayudas a organizar "
            "archivos y a redactar documentos. Cuando el usuario te pida crear "
            "carpetas, archivos o documentos, usa las herramientas disponibles. "
            "Responde en el idioma del usuario."
        ),
        "temperature": 0.4,
        "knowledge_enabled": False,
        "enabled_tools": [
            "create_folder",
            "list_files",
            "create_text_file",
            "read_text_file",
            "create_markdown_document",
            "search_workspace",
        ],
    },
    {
        "id": "writer",
        "name": "Redactor de documentos",
        "icon": "✍️",
        "description": "Escribe informes, resúmenes y documentos y los guarda por ti.",
        "system_prompt": (
            "Eres un redactor profesional. Escribes textos claros y bien "
            "estructurados. Cuando el usuario quiera guardar lo que escribes, usa "
            "las herramientas para crear el documento. Responde en el idioma del usuario."
        ),
        "temperature": 0.7,
        "knowledge_enabled": False,
        "enabled_tools": ["create_markdown_document", "create_text_report"],
    },
    {
        "id": "researcher",
        "name": "Investigador (base de conocimiento)",
        "icon": "📚",
        "description": "Responde usando tus documentos importados y guarda hallazgos.",
        "system_prompt": (
            "Eres un asistente de investigación. Respondes apoyándote en la base "
            "de conocimiento local cuando es relevante y citas de dónde sale la "
            "información. Responde en el idioma del usuario."
        ),
        "temperature": 0.3,
        "knowledge_enabled": True,
        "enabled_tools": ["search_knowledge_base", "create_markdown_document"],
    },
    {
        "id": "computer-assistant",
        "name": "Asistente de PC (con permiso)",
        "icon": "🖥️",
        "description": "Abre apps, abre páginas y ejecuta comandos — siempre pidiendo tu permiso.",
        "system_prompt": (
            "Eres un asistente que puede operar la computadora del usuario. Antes "
            "de cada acción sensible, propones lo que harás y esperas la "
            "aprobación del usuario. Sé claro sobre qué vas a ejecutar. Responde "
            "en el idioma del usuario."
        ),
        "temperature": 0.2,
        "knowledge_enabled": False,
        "enabled_tools": ["open_application", "open_url", "run_command"],
    },
]


def list_templates() -> list["AgentTemplate"]:
    from .schemas.agent import AgentTemplate as _AgentTemplate

    return [_AgentTemplate(**t) for t in AGENT_TEMPLATES]
