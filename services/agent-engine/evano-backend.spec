# PyInstaller spec for the Evano Studio backend (packaged desktop builds).
#
# "Lite" bundle: ChromaDB/onnxruntime (knowledge base) and discord.py are
# EXCLUDED — their services import them lazily and degrade gracefully, so the
# core (agents, tools, documents incl. .docx/.pdf, computer control) works fully
# while keeping the bundle small and reliable to freeze. Build:
#   pyinstaller --noconfirm evano-backend.spec
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

hiddenimports = []
hiddenimports += collect_submodules("app")
hiddenimports += collect_submodules("uvicorn")
hiddenimports += [
    "uvicorn.lifespan.on",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.loops.auto",
]

datas = []
datas += collect_data_files("fpdf")  # font metrics
datas += collect_data_files("docx")  # default .docx template

excludes = [
    "chromadb",
    "onnxruntime",
    "discord",
    "torch",
    "sentence_transformers",
    "tokenizers",
    "transformers",
    "tkinter",
    "matplotlib",
]

a = Analysis(
    ["run_server.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    excludes=excludes,
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="evano-backend",
    console=True,
)
coll = COLLECT(exe, a.binaries, a.datas, name="evano-backend")
