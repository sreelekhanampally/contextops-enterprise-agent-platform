from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_retrieval_service
from app.schemas import DocumentIngestResponse
from app.services.retrieval import RetrievalService

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])


@router.post("/ingest", response_model=DocumentIngestResponse)
async def ingest_document(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db),
    retrieval: RetrievalService = Depends(get_retrieval_service),
):
    try:
        doc_id, count = await retrieval.ingest_upload(session, file)
        return DocumentIngestResponse(document_id=doc_id, filename=file.filename or "upload", chunks_created=count)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
