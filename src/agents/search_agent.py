import pandas as pd
from langchain_core.tools import tool
from src.embedder.embedd_texts import VectorStore
from src.fpl import fpl_api as fpl

_vector_store: VectorStore | None = None


def _get_vector_store() -> VectorStore:
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store


def _get_gw_window() -> tuple[str, str]:
    try:
        start_gw, end_gw = fpl.get_between_gw()
        return pd.Timestamp(start_gw).isoformat(), pd.Timestamp(end_gw).isoformat()
    except Exception:
        return "2025-08-01", "2099-12-31"


@tool
def search_transcripts(query: str) -> str:
    """Search FPL podcast transcripts for opinions and analysis.
    Use this to find what podcasters and content creators have said about
    players, teams, strategies, transfers, captaincy picks, etc.
    """
    vs = _get_vector_store()
    min_date, max_date = _get_gw_window()
    chunks = vs.hybrid_query(
        query, k=10, min_date=min_date, max_date=max_date,
    )
    if not chunks:
        return "No relevant podcast transcripts found for this query."

    results = []
    for i, c in enumerate(chunks, 1):
        meta = c.get("metadata", {})
        title = meta.get("title", "Unknown")
        channel = meta.get("channel_name", "")
        published = meta.get("published_at", "")[:10]
        content = c.get("content", "")
        results.append(
            f"[{i}] {title} ({channel}, {published}):\n{content}"
        )
    return "\n\n---\n\n".join(results)
