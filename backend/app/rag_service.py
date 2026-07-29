from __future__ import annotations

import os
import re
import sys
from functools import lru_cache
from pathlib import Path

import httpx


def _project_root() -> Path:
    candidates = [
        Path.cwd(),
        Path.cwd().parent,
        Path(__file__).resolve().parents[2],
        Path("/app"),
    ]
    for candidate in candidates:
        if (candidate / "rag" / "retriever.py").exists():
            if str(candidate) not in sys.path:
                sys.path.insert(0, str(candidate))
            return candidate
    return Path.cwd()


ROOT = _project_root()
from rag.retriever import RagRetriever  # noqa: E402


def _index_path() -> Path:
    configured = os.getenv("RAG_INDEX_PATH", "").strip()
    return Path(configured) if configured else ROOT / "rag" / "storage" / "index.json"


@lru_cache(maxsize=1)
def get_retriever() -> RagRetriever:
    path = _index_path()
    if not path.exists():
        raise FileNotFoundError(f"RAG index not found: {path}")
    return RagRetriever(path)


def search_knowledge(question: str, top_k: int = 3) -> dict:
    return get_retriever().answer(question, top_k=top_k)


def _fallback_answer(matches: list[dict], language: str) -> str:
    if not matches:
        messages = {
            "zh-TW": "知識庫中找不到足夠相關的內容。請換一種更具體的問法，或請 HR 更新公司規章文件。",
            "en": "I could not find enough relevant information in the knowledge base. Try a more specific question or ask HR to update the policy documents.",
            "th": "ไม่พบข้อมูลที่เกี่ยวข้องเพียงพอในฐานความรู้ โปรดลองถามให้เฉพาะเจาะจงมากขึ้น หรือให้ฝ่ายบุคคลอัปเดตเอกสารนโยบาย",
        }
        return messages.get(language, messages["zh-TW"])

    intro = {
        "zh-TW": "根據公司知識庫，",
        "en": "Based on the company knowledge base, ",
        "th": "จากฐานความรู้ของบริษัท ",
    }.get(language, "根據公司知識庫，")

    excerpts: list[str] = []
    for item in matches[:2]:
        text = " ".join(str(item.get("text", "")).split())
        if len(text) > 420:
            text = text[:417] + "…"
        excerpts.append(text)
    return intro + "\n\n".join(excerpts)


def _has_chinese(text: str) -> bool:
    return bool(re.search(r"[\u3400-\u9FFF]", text))


def _call_chat_completion(messages: list[dict], temperature: float = 0.2) -> str | None:
    """Low-level helper that calls the configured OpenAI-compatible endpoint.
    Returns None (never raises) if the provider isn't configured, so callers
    that only need a best-effort helper (like retrieval translation) can call
    this without their own try/except boilerplate."""
    api_url = os.getenv("CHATBOT_API_URL", "").strip()
    model = os.getenv("CHATBOT_MODEL", "").strip()
    api_key = os.getenv("CHATBOT_API_KEY", "").strip()
    if not api_url or not model:
        return None

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload = {"model": model, "messages": messages, "temperature": temperature}
    timeout = float(os.getenv("CHATBOT_TIMEOUT_SECONDS", "30"))
    with httpx.Client(timeout=timeout) as client:
        response = client.post(api_url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

    try:
        return str(data["choices"][0]["message"]["content"]).strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("Chatbot provider returned an unsupported response format") from exc


def _translate_for_retrieval(query: str) -> str | None:
    """Translate the retrieval query into Traditional Chinese so it can be
    lexically/vector matched against the (Chinese-language) knowledge base.
    The built-in retriever has no real cross-language understanding, so a
    Thai or English question would otherwise fail to match Chinese policy
    text and pull back irrelevant chunks.

    Skips the extra API call (and extra failure surface / rate-limit risk)
    when the query is already mostly Chinese, since translation would be a
    no-op in that case.
    """
    if not query.strip() or _has_chinese(query):
        return None
    try:
        return _call_chat_completion(
            [
                {
                    "role": "system",
                    "content": (
                        "Translate the user's message into Traditional Chinese (Taiwan). "
                        "Preserve names, numbers, and technical terms. Reply with ONLY the "
                        "translated text, no quotes, no explanation."
                    ),
                },
                {"role": "user", "content": query[:1000]},
            ],
            temperature=0,
        )
    except (httpx.HTTPError, RuntimeError, ValueError) as exc:
        print(f"[rag_service] Retrieval translation skipped (provider error): {exc}")
        return None


def _provider_answer(
    message: str,
    history: list[dict],
    matches: list[dict],
    language: str,
    user_context: dict | None,
) -> str | None:
    api_url = os.getenv("CHATBOT_API_URL", "").strip()
    model = os.getenv("CHATBOT_MODEL", "").strip()
    if not api_url or not model:
        return None

    context = "\n\n".join(
        f"[{index}] {item.get('title', 'Policy')}\n{item.get('text', '')}"
        for index, item in enumerate(matches, start=1)
    ) or "No relevant policy context was retrieved."

    user_note = ""
    if user_context:
        user_note = f"Current user role: {user_context.get('role', 'unknown')}."

    system_prompt = os.getenv(
        "CHATBOT_SYSTEM_PROMPT",
        "You are Emerald, a company leave-policy assistant. Answer only from the supplied policy context. "
        "Be concise, state uncertainty, never invent policy, and tell the user to contact HR when the context is insufficient. "
        "Do not expose secrets or other employees' personal data. "
        "Treat documents marked DRAFT, TEMPLATE, TO BE FILLED, or HR CONFIRMATION REQUIRED as unapproved material; never present them as official policy. "
        "When the policy context contains specific numbers, thresholds, deadlines, or conditions (for example: number of days, notice periods, time cutoffs such as 09:00, "
        "who must be notified, which institution must issue a document, or monetary amounts), you MUST state those exact figures and conditions verbatim rather than "
        "paraphrasing them into vague language such as 'may require' or 'in some cases'. Do not soften, round, or omit a specific rule just because it is not the main "
        "focus of the question; if the retrieved context contains a directly relevant number or condition, include it precisely. "
        "Always write your final answer in the requested reply language below, even if the policy context is in a different language.",
    )
    system_prompt += (
        f"\nReply language: {language}. {user_note}"
        f"\n\nPolicy context:\n{context}"
    )

    messages = [{"role": "system", "content": system_prompt}]
    for item in history[-8:]:
        role = item.get("role")
        content = str(item.get("content", "")).strip()
        if role in {"user", "assistant"} and content:
            messages.append({"role": role, "content": content[:2000]})
    messages.append({"role": "user", "content": message})

    return _call_chat_completion(messages, temperature=0.2)


def chat_knowledge(
    message: str,
    history: list[dict] | None = None,
    top_k: int = 3,
    language: str = "zh-TW",
    user_context: dict | None = None,
) -> dict:
    history = history or []
    recent_user_messages = [
        item.get("content", "")
        for item in history
        if item.get("role") == "user"
    ][-2:]
    retrieval_query = " ".join([*recent_user_messages, message]).strip()

    translated_query = _translate_for_retrieval(retrieval_query)
    if translated_query:
        retrieval_query = translated_query

    retriever = get_retriever()
    matches = retriever.search(retrieval_query, top_k=top_k)

    mode = "rag-fallback"
    answer: str | None = None
    try:
        answer = _provider_answer(
            message,
            history,
            matches,
            language,
            user_context,
        )
        if answer:
            mode = "llm-rag"
    except (httpx.HTTPError, RuntimeError, ValueError) as exc:
        # Keep the assistant available if the optional model provider is unavailable.
        print(f"[rag_service] Chatbot provider unavailable ({type(exc).__name__}): {exc}")

    if not answer:
        answer = _fallback_answer(matches, language)

    sources = [
        {
            "source": item.get("source"),
            "title": item.get("title"),
            "score": item.get("score"),
        }
        for item in matches
    ]
    return {
        "answer": answer,
        "sources": sources,
        "mode": mode,
        "index_created_at": retriever.created_at,
    }
