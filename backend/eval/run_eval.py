"""Small, reproducible evaluation harness for ContextOps.

Run inside the backend container after the database has been seeded:
    python -m eval.run_eval

The script intentionally reports simple, interpretable metrics rather than an
opaque LLM-as-judge score: routing accuracy and retrieval hit@k.
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

from app.db.session import SessionLocal
from app.dependencies import get_llm_service, get_retrieval_service

CASES_PATH = Path(__file__).with_name("cases.json")


async def main() -> None:
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    llm = get_llm_service()
    retrieval = get_retrieval_service()

    routing_hits = 0
    for case in cases["routing"]:
        decision = await llm.route(case["question"])
        ok = decision.route == case["expected"]
        routing_hits += int(ok)
        print(f"[route] {'PASS' if ok else 'FAIL'} {case['question']} -> {decision.route}")

    retrieval_hits = 0
    async with SessionLocal() as session:
        for case in cases["retrieval"]:
            chunks = await retrieval.retrieve(session, case["question"])
            sources = {chunk.source for chunk in chunks}
            ok = case["expected_source"] in sources
            retrieval_hits += int(ok)
            print(f"[rag]   {'PASS' if ok else 'FAIL'} {case['question']} -> {sorted(sources)}")

    route_total = len(cases["routing"])
    retrieval_total = len(cases["retrieval"])
    print("\n=== ContextOps evaluation ===")
    print(f"Routing accuracy : {routing_hits}/{route_total} = {routing_hits / route_total:.1%}")
    print(f"Retrieval Hit@K  : {retrieval_hits}/{retrieval_total} = {retrieval_hits / retrieval_total:.1%}")


if __name__ == "__main__":
    asyncio.run(main())
