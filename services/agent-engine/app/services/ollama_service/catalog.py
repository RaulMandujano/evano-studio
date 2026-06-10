"""Curated free local models the user can choose to install (never auto-installed)."""
from __future__ import annotations

RECOMMENDED_MODELS: list[dict] = [
    {
        "model": "gemma4",
        "min_ram_gb": 8, "size_gb": 3.3,
        "name": "Gemma 4",
        "category": "Recommended",
        "notes": "Google's recommended general-purpose model. If gemma4 isn't "
        "available yet in your Ollama, try another model below.",
        "family": "gemma",
        "size_estimate": "varies",
        "min_ram": "8 GB+",
        "recommended": True,
    },
    {
        "model": "qwen2.5-coder:7b",
        "min_ram_gb": 8, "size_gb": 4.7,
        "name": "Qwen2.5 Coder 7B",
        "category": "Coding",
        "notes": "Strong local model for coding and technical tasks.",
        "family": "qwen",
        "size_estimate": "~4.7 GB",
        "min_ram": "8 GB+",
    },
    {
        "model": "llama3.2:3b",
        "min_ram_gb": 6, "size_gb": 2.0,
        "name": "Llama 3.2 3B",
        "category": "General chat",
        "notes": "Lightweight general chat model that runs on modest hardware.",
        "family": "llama",
        "size_estimate": "~2.0 GB",
        "min_ram": "8 GB",
    },
    {
        "model": "mistral:7b",
        "min_ram_gb": 8, "size_gb": 4.1,
        "name": "Mistral 7B",
        "category": "General",
        "notes": "Well-rounded general-purpose model.",
        "family": "mistral",
        "size_estimate": "~4.1 GB",
        "min_ram": "8 GB+",
    },
    {
        "model": "deepseek-r1:7b",
        "min_ram_gb": 8, "size_gb": 4.7,
        "name": "DeepSeek-R1 7B (distill)",
        "category": "Reasoning",
        "notes": "Distilled reasoning model for step-by-step tasks.",
        "family": "deepseek",
        "size_estimate": "~4.7 GB",
        "min_ram": "8 GB+",
    },
]
