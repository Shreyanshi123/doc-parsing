"""Central configuration. Everything is read from environment variables (.env supported)."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # dotenv is optional
    pass


def _csv(name: str, default: str = "") -> list[str]:
    return [x.strip() for x in os.getenv(name, default).split(",") if x.strip()]


@dataclass
class Settings:
    data_dir: Path = field(default_factory=lambda: Path(os.getenv("DATA_DIR", "./data")).resolve())
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    # storage
    local_allowed_roots: list[str] = field(
        default_factory=lambda: _csv("LOCAL_ALLOWED_ROOTS", "./data/uploads,./samples")
    )
    azure_conn_str: str = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "")
    allowed_url_hosts: list[str] = field(default_factory=lambda: _csv("ALLOWED_URL_HOSTS"))
    output_backend: str = os.getenv("OUTPUT_BACKEND", "local")
    azure_output_container: str = os.getenv("AZURE_OUTPUT_CONTAINER", "parsed-output")

    # OCR
    tesseract_cmd: str = os.getenv("TESSERACT_CMD", "")
    ocr_lang: str = os.getenv("OCR_LANG", "eng")
    ocr_dpi: int = int(os.getenv("OCR_DPI", "200"))

    # VLM (Ollama)
    ollama_url: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
    vlm_model: str = os.getenv("VLM_MODEL", "qwen2.5vl:7b")
    vlm_max_pages: int = int(os.getenv("VLM_MAX_PAGES", "10"))
    vlm_timeout: int = int(os.getenv("VLM_TIMEOUT_SEC", "300"))

    # Figure reader (charts / diagrams -> text). Used by the smart_pdf parser.
    #   VISION_BACKEND = auto | azure_openai | ollama | off
    #   auto = Azure OpenAI if its three settings below are filled, else local Ollama if reachable, else off
    vision_backend: str = os.getenv("VISION_BACKEND", "auto")
    azure_openai_endpoint: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    azure_openai_key: str = os.getenv("AZURE_OPENAI_KEY", "")
    azure_openai_deployment: str = os.getenv("AZURE_OPENAI_DEPLOYMENT", "")
    azure_openai_api_version: str = os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21")
    max_figures: int = int(os.getenv("MAX_FIGURES", "8"))   # per document - caps vision calls (cost)

    # Paid engines (optional)
    azure_di_endpoint: str = os.getenv("AZURE_DI_ENDPOINT", "")
    azure_di_key: str = os.getenv("AZURE_DI_KEY", "")

    # LlamaParse (cloud)
    llama_api_key: str = os.getenv("LLAMA_CLOUD_API_KEY", "")

    # Compare: heavy engines run in a child process and are stopped after this many seconds (0 = no limit)
    parser_timeout_sec: int = int(os.getenv("PARSER_TIMEOUT_SEC", "600"))

    # worker
    worker_threads: int = int(os.getenv("WORKER_THREADS", "1"))
    worker_poll_sec: float = float(os.getenv("WORKER_POLL_SEC", "1.0"))

    @property
    def uploads_dir(self) -> Path:
        p = self.data_dir / "uploads"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def outputs_dir(self) -> Path:
        p = self.data_dir / "outputs"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def db_path(self) -> Path:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        return self.data_dir / "jobs.db"


settings = Settings()
