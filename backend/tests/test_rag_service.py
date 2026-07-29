from app.rag_service import chat_knowledge, search_knowledge


def test_rag_index_returns_policy_context():
    result = search_knowledge("病假醫療證明", top_k=2)
    assert result["matches"]
    assert "醫療證明" in result["answer"]


def test_chatbot_returns_answer_and_sources_without_external_provider(monkeypatch):
    monkeypatch.delenv("CHATBOT_API_URL", raising=False)
    monkeypatch.delenv("CHATBOT_MODEL", raising=False)
    result = chat_knowledge(
        "病假需要醫療證明嗎？",
        history=[{"role": "user", "content": "我想了解病假規定"}],
        language="zh-TW",
    )
    assert result["answer"]
    assert result["sources"]
    assert result["mode"] == "rag-fallback"
