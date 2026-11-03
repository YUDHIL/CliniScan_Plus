"""
CliniScan+ Centralized Gemini AI Service
Provides unified, resilient access to Google GenAI with automatic exponential backoff,
structured JSON and conversational text generation, and credential-safe logging.
"""

import os
import sys
import time
import logging
from typing import Optional, Dict, Any

# Ensure root .env is loaded
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_FILE = os.path.join(PROJECT_ROOT, ".env")
try:
    from dotenv import load_dotenv
    if os.path.exists(ENV_FILE):
        load_dotenv(dotenv_path=ENV_FILE, override=False)
except ImportError:
    pass

logger = logging.getLogger("CliniScanGemini")

# Default verified model ID based on live API inspection
DEFAULT_MODEL = "gemini-3.6-flash"


def mask_key(key: Optional[str]) -> str:
    """Mask API key for safe diagnostics."""
    if not key or len(key) < 8:
        return "<not set or invalid>"
    return f"{key[:4]}...{key[-4:]}"


class GeminiService:
    """
    Centralized Google GenAI singleton client supporting:
    - Text and JSON generation
    - Exponential backoff on temporary capacity spikes (HTTP 503 / 429)
    - Fast fail on permanent errors (400, 401, 404)
    - Safe credential handling
    """

    def __init__(self):
        self.api_key: Optional[str] = None
        self.primary_model: str = DEFAULT_MODEL
        self.client = None
        self._initialized = False
        self._init_client()

    def _init_client(self):
        """Read configuration and initialize the GenAI client with explicit timeout."""
        raw_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.api_key = raw_key if len(raw_key) > 10 else None
        
        configured_model = os.getenv("GEMINI_MODEL", "").strip()
        self.primary_model = configured_model if configured_model else DEFAULT_MODEL

        if not self.api_key:
            logger.warning("[GeminiService] GEMINI_API_KEY not configured. LLM calls will use offline fallbacks.")
            self.client = None
            self._initialized = False
            return

        try:
            from google import genai
            self.client = genai.Client(api_key=self.api_key)
            self._initialized = True
            logger.info(
                f"[GeminiService] Client initialized. Primary Model: '{self.primary_model}' (Key: {mask_key(self.api_key)})"
            )
        except Exception as err:
            logger.error(f"[GeminiService] Failed initializing GenAI client: {type(err).__name__} - {err}")
            self.client = None
            self._initialized = False

    def is_available(self) -> bool:
        """Check whether Gemini is ready for queries."""
        if not self._initialized or self.client is None:
            raw_key = os.getenv("GEMINI_API_KEY", "").strip()
            if raw_key and len(raw_key) > 10:
                self._init_client()
        return bool(self._initialized and self.client is not None)

    def _is_transient_error(self, err: Exception) -> bool:
        """Determine if an error is temporary (503 capacity spike or 429 rate limit)."""
        err_str = str(err).lower()
        err_type = type(err).__name__.lower()
        
        transient_codes = ["503", "429", "unavailable", "resource_exhausted", "deadline_exceeded", "timeout", "timed out"]
        return any(code in err_str or code in err_type for code in transient_codes)

    def _is_permanent_error(self, err: Exception) -> bool:
        """Determine if an error is permanent (400 bad request, 401 unauthenticated, 404 model not found)."""
        err_str = str(err).lower()
        err_type = type(err).__name__.lower()

        permanent_codes = ["400", "401", "403", "404", "not_found", "unauthenticated", "permission_denied", "invalid_argument"]
        return any(code in err_str or code in err_type for code in permanent_codes)

    def _execute_with_retry(
        self,
        contents: str,
        config: Optional[Any] = None,
        max_retries: int = 2
    ) -> Optional[str]:
        """
        Execute generate_content with exponential backoff on 503 / 429.
        Fast-fails on permanent errors.
        """
        if not self.is_available():
            self._init_client()
            if not self.is_available():
                return None

        model_id = self.primary_model

        for attempt in range(1, max_retries + 1):
            try:
                kwargs = {"model": model_id, "contents": contents}
                if config is not None:
                    kwargs["config"] = config

                response = self.client.models.generate_content(**kwargs)
                if response and response.text:
                    return response.text.strip()
                return None

            except Exception as ex:
                # Permanent errors (e.g. 404 model not found, 401 bad key) -> do not retry
                if self._is_permanent_error(ex):
                    logger.warning(
                        f"[GeminiService] Permanent error on model '{model_id}': {type(ex).__name__}"
                    )
                    break

                # Transient errors (503 Unavailable / 429 Rate Limit) -> back off and retry
                if self._is_transient_error(ex) and attempt < max_retries:
                    backoff = 1.0 * attempt  # 1.0s, 2.0s
                    logger.info(
                        f"[GeminiService] Temporary spike ({type(ex).__name__}) on '{model_id}'. Retrying in {backoff:.1f}s..."
                    )
                    time.sleep(backoff)
                    continue

                logger.warning(
                    f"[GeminiService] Call failed on model '{model_id}' (attempt {attempt}/{max_retries}): {type(ex).__name__}"
                )
                break

        return None

    def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.4
    ) -> Optional[str]:
        """
        Generate conversational medical text response.
        """
        from google.genai import types

        config_args = {"temperature": temperature}
        if system_instruction:
            config_args["system_instruction"] = system_instruction

        config = types.GenerateContentConfig(**config_args)
        return self._execute_with_retry(contents=prompt, config=config)

    def generate_json(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2
    ) -> Optional[str]:
        """
        Generate structured JSON response.
        """
        from google.genai import types

        config_args = {
            "response_mime_type": "application/json",
            "temperature": temperature,
        }
        if system_instruction:
            config_args["system_instruction"] = system_instruction

        config = types.GenerateContentConfig(**config_args)
        return self._execute_with_retry(contents=prompt, config=config)


# Global singleton service
gemini_service = GeminiService()
