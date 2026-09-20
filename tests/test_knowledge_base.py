from app.knowledge.service import KnowledgeService


def test_faq_ingestion_and_retrieval(tmp_path):
    service = KnowledgeService(storage_path=str(tmp_path / "knowledge.db"))

    service.reindex_agent(
        "agent-1",
        [
            {
                "id": "faq-1",
                "type": "faq",
                "name": "How long do refunds take?",
                "value": "Refunds take 3 to 5 business days to appear.",
                "status": "ready",
            }
        ],
    )

    results = service.retrieve("agent-1", "refunds take 3 to 5 business days", limit=3)

    assert len(results) >= 1
    assert any("3 to 5 business days" in result["content"] for result in results)
    assert results[0]["source_name"] == "How long do refunds take?"


def test_agent_isolation(tmp_path):
    service = KnowledgeService(storage_path=str(tmp_path / "knowledge.db"))

    service.reindex_agent(
        "agent-1",
        [
            {
                "id": "faq-a",
                "type": "faq",
                "name": "What is the refund policy?",
                "value": "Refunds take 5 business days.",
                "status": "ready",
            }
        ],
    )

    service.reindex_agent(
        "agent-2",
        [
            {
                "id": "faq-b",
                "type": "faq",
                "name": "What is the refund policy?",
                "value": "Refunds take 5 business days.",
                "status": "ready",
            }
        ],
    )

    results_agent_1 = service.retrieve("agent-1", "shipping takes 2 days", limit=3)
    results_agent_2 = service.retrieve("agent-2", "refunds take 5 business days", limit=3)

    assert results_agent_1 == []
    assert any("Refunds take 5 business days." in result["content"] for result in results_agent_2)


def test_no_result_behavior(tmp_path):
    service = KnowledgeService(storage_path=str(tmp_path / "knowledge.db"))

    service.reindex_agent(
        "agent-1",
        [
            {
                "id": "faq-1",
                "type": "faq",
                "name": "What is the refund policy?",
                "value": "Refunds take 5 business days.",
                "status": "ready",
            }
        ],
    )

    results = service.retrieve("agent-1", "what is the weather", limit=3)

    assert results == []
