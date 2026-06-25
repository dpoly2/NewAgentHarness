from __future__ import annotations

import sqlite3
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from core.auth import get_current_user
from core.config import AGENTS_DIR, DB_PATH, HARNESS

try:
    from ah_logging import get_logger
except ImportError:
    import logging

    def get_logger(name: str):
        return logging.getLogger(f"archonhub.{name}")

logger = get_logger("files")
router = APIRouter()

@router.post("/files/upload")
async def upload_file(
    file: bytes = None,
    filename: str = None,
    mime_type: str = None,
    conversation_id: Optional[str] = None,
    message_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    """Upload a file for processing."""
    try:
        user_id = current_user.get("username", "default_user")
        from file_processor import FileProcessor
        
        # Initialize processor
        upload_dir = AGENTS_DIR / "data" / "uploads"
        processor = FileProcessor(DB_PATH, upload_dir)
        
        # Save file
        result = await processor.save_file(
            file_content=file,
            filename=filename,
            mime_type=mime_type,
            user_id=user_id,
            conversation_id=conversation_id,
            message_id=message_id,
            uploaded_via="ios"
        )
        
        # Trigger async parsing
        try:
            parse_result = await processor.parse_file(result["file_id"])
            result["parsing"] = parse_result
        except Exception as parse_error:
            logger.error(f"Parsing error: {parse_error}")
            result["parsing"] = {"status": "failed", "error": str(parse_error)}
        
        return {
            "success": True,
            "file": result
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"File upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/files/{file_id}")
async def get_file(file_id: str, _: dict = Depends(get_current_user)):
    """Get file metadata and parsed content."""
    try:
        from file_processor import FileProcessor
        
        upload_dir = AGENTS_DIR / "data" / "uploads"
        processor = FileProcessor(DB_PATH, upload_dir)
        
        file_data = processor.get_file_metadata(file_id)
        if not file_data:
            raise HTTPException(status_code=404, detail="File not found")
        
        return {
            "success": True,
            "file": file_data
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get file error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/files")
async def list_files(limit: int = 50, current_user: dict = Depends(get_current_user)):
    """List files uploaded by user."""
    try:
        user_id = current_user.get("username", "default_user")
        from file_processor import FileProcessor
        
        upload_dir = AGENTS_DIR / "data" / "uploads"
        processor = FileProcessor(DB_PATH, upload_dir)
        
        files = processor.list_user_files(user_id, limit)
        
        return {
            "success": True,
            "files": files,
            "count": len(files)
        }
    except Exception as e:
        logger.error(f"List files error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/files/{file_id}/embed")
async def embed_file(file_id: str, _: dict = Depends(get_current_user)):
    """Generate embeddings for uploaded file to enable semantic search."""
    try:
        from document_rag import DocumentEmbedder
        
        upload_dir = AGENTS_DIR / "data" / "uploads"
        chroma_path = HARNESS / "memory" / "chromadb"
        
        embedder = DocumentEmbedder(DB_PATH, chroma_path)
        result = await embedder.embed_file(file_id)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Embedding failed"))
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Embed file error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/files/_search")
async def search_documents(query: str, limit: int = 5, file_ids: Optional[str] = None, _: dict = Depends(get_current_user)):
    """Semantic search across all embedded documents."""
    try:
        from document_rag import DocumentEmbedder
        
        chroma_path = HARNESS / "memory" / "chromadb"
        embedder = DocumentEmbedder(DB_PATH, chroma_path)
        
        # Parse file_ids if provided (comma-separated)
        file_id_list = file_ids.split(",") if file_ids else None
        
        results = await embedder.search(query, limit=limit, file_ids=file_id_list)
        
        return {
            "success": True,
            "query": query,
            "results": results,
            "count": len(results)
        }
    
    except Exception as e:
        logger.error(f"Document search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/files/upload/form")
async def upload_file_form(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """Multipart form upload for browser/webapp clients."""
    try:
        user_id = current_user.get("username", "default_user")
        from file_processor import FileProcessor

        upload_dir = AGENTS_DIR / "data" / "uploads"
        processor = FileProcessor(DB_PATH, upload_dir)

        content = await file.read()
        result = await processor.save_file(
            file_content=content,
            filename=file.filename,
            mime_type=file.content_type or "application/octet-stream",
            user_id=user_id,
            uploaded_via="webapp",
        )
        try:
            parse_result = await processor.parse_file(result["file_id"])
            result["parsing"] = parse_result
        except Exception as parse_error:
            result["parsing"] = {"status": "failed", "error": str(parse_error)}

        return {"success": True, "file": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Form upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/files/{file_id}")
async def delete_file(file_id: str, _: dict = Depends(get_current_user)):
    """Delete an uploaded file record and its chunks."""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        try:
            conn.execute("DELETE FROM file_chunks WHERE file_id = ?", (file_id,))
            conn.execute("DELETE FROM uploaded_files WHERE id = ?", (file_id,))
            conn.commit()
        finally:
            conn.close()
        return {"success": True}
    except Exception as e:
        logger.error(f"Delete file error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
