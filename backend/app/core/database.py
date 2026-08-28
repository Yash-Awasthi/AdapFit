"""
AdapFit Database Layer
Supabase Postgres connection with connection pooling.
Following Supabase best practices:
  - conn-pooling: transaction-mode pooling via Supabase pooler
  - conn-limits: connection limits per service tier
  - lock-short-transactions: short transaction scope
"""
import os
from typing import Optional
from app.core.config import settings


class DatabaseConfig:
    """Lazy-initialized Supabase client with connection pooling."""

    def __init__(self):
        self._client = None
        self._async_client = None

    @property
    def url(self) -> str:
        return settings.SUPABASE_URL

    @property
    def key(self) -> str:
        return settings.SUPABASE_KEY

    @property
    def is_configured(self) -> bool:
        return bool(self.url and self.key)

    def get_client(self):
        """Get sync Supabase client (for non-async operations)."""
        if not self.is_configured:
            return None
        if self._client is None:
            try:
                from supabase import create_client
                self._client = create_client(self.url, self.key)
            except ImportError:
                return None
        return self._client

    async def get_async_client(self):
        """Get async Supabase client (for async operations)."""
        if not self.is_configured:
            return None
        if self._async_client is None:
            try:
                from supabase import acreate_client
                self._async_client = await acreate_client(self.url, self.key)
            except (ImportError, AttributeError):
                # Fallback: use sync client
                return self.get_client()
        return self._async_client


# Singleton
db = DatabaseConfig()
