"""
File processing service for ArchonHub.

Handles file uploads, parsing, and RAG indexing for:
- PDFs (text extraction + OCR fallback)
- Images (Vision API analysis)
- Spreadsheets (CSV/Excel parsing)
- Documents (DOCX text extraction)
"""

import base64
import io
import json
import logging
import mimetypes
import os
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

# File size limits
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_CHUNK_TOKENS = 512

# Supported file types
SUPPORTED_MIMETYPES = {
    # PDFs
    "application/pdf",
    # Images
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/gif",
    "image/webp",
    # Spreadsheets
    "text/csv",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    # Documents
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
}

logger = logging.getLogger(__name__)


class FileProcessor:
    """Handles file upload, storage, parsing, and indexing."""
    
    def __init__(self, db_path: Path, upload_dir: Path):
        self.db_path = db_path
        self.upload_dir = upload_dir
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    def validate_file(self, filename: str, file_size: int, mime_type: str) -> Tuple[bool, Optional[str]]:
        """Validate uploaded file."""
        # Check file size
        if file_size > MAX_FILE_SIZE:
            return False, f"File size {file_size} exceeds limit {MAX_FILE_SIZE} bytes"
        
        # Check MIME type
        if mime_type not in SUPPORTED_MIMETYPES:
            return False, f"Unsupported file type: {mime_type}"
        
        return True, None
    
    def determine_file_type(self, mime_type: str) -> str:
        """Determine file type category from MIME type."""
        if mime_type == "application/pdf":
            return "pdf"
        elif mime_type.startswith("image/"):
            return "image"
        elif mime_type in ("text/csv", "application/vnd.ms-excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"):
            return "spreadsheet"
        elif mime_type in ("application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/plain"):
            return "document"
        else:
            return "unknown"
    
    async def save_file(
        self,
        file_content: bytes,
        filename: str,
        mime_type: str,
        user_id: str,
        conversation_id: Optional[str] = None,
        message_id: Optional[str] = None,
        uploaded_via: str = "ios"
    ) -> Dict[str, Any]:
        """Save uploaded file and create database record."""
        
        # Validate
        file_size = len(file_content)
        is_valid, error_msg = self.validate_file(filename, file_size, mime_type)
        if not is_valid:
            raise ValueError(error_msg)
        
        # Generate unique file ID
        file_id = str(uuid.uuid4())
        file_type = self.determine_file_type(mime_type)
        
        # Determine storage path (organize by date + user)
        date_prefix = datetime.utcnow().strftime("%Y/%m/%d")
        storage_dir = self.upload_dir / date_prefix / user_id
        storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename to avoid collisions
        file_ext = Path(filename).suffix
        storage_filename = f"{file_id}{file_ext}"
        storage_path = storage_dir / storage_filename
        
        # Write file to disk
        storage_path.write_bytes(file_content)
        logger.info(f"Saved file {file_id} to {storage_path}")
        
        # Insert database record
        conn = sqlite3.connect(str(self.db_path))
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO uploaded_files (
                    file_id, user_id, filename, file_type, mime_type, file_size,
                    storage_path, parsing_status, uploaded_at, uploaded_via,
                    conversation_id, message_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                file_id, user_id, filename, file_type, mime_type, file_size,
                str(storage_path), "pending", datetime.utcnow().isoformat(),
                uploaded_via, conversation_id, message_id
            ))
            conn.commit()
        finally:
            conn.close()
        
        return {
            "file_id": file_id,
            "filename": filename,
            "file_type": file_type,
            "file_size": file_size,
            "status": "uploaded"
        }
    
    async def parse_file(self, file_id: str) -> Dict[str, Any]:
        """Parse uploaded file and extract content."""
        
        conn = sqlite3.connect(str(self.db_path))
        try:
            # Get file metadata
            cursor = conn.cursor()
            cursor.execute("""
                SELECT file_type, mime_type, storage_path, filename
                FROM uploaded_files
                WHERE file_id = ?
            """, (file_id,))
            row = cursor.fetchone()
            
            if not row:
                raise ValueError(f"File not found: {file_id}")
            
            file_type, mime_type, storage_path, filename = row
            
            # Update status to processing
            cursor.execute("""
                UPDATE uploaded_files
                SET parsing_status = 'processing'
                WHERE file_id = ?
            """, (file_id,))
            conn.commit()
            
            # Parse based on file type
            try:
                if file_type == "pdf":
                    result = await self._parse_pdf(Path(storage_path))
                elif file_type == "image":
                    result = await self._parse_image(Path(storage_path))
                elif file_type == "spreadsheet":
                    result = await self._parse_spreadsheet(Path(storage_path), filename)
                elif file_type == "document":
                    result = await self._parse_document(Path(storage_path))
                else:
                    raise ValueError(f"Unsupported file type: {file_type}")
                
                # Update database with parsed content
                cursor.execute("""
                    UPDATE uploaded_files
                    SET parsed_content = ?,
                        parsing_status = 'complete',
                        metadata_json = ?
                    WHERE file_id = ?
                """, (
                    result["content"],
                    json.dumps(result.get("metadata", {})),
                    file_id
                ))
                conn.commit()
                
                logger.info(f"Parsed file {file_id} ({file_type})")
                
                return {
                    "file_id": file_id,
                    "status": "complete",
                    "content_length": len(result["content"]),
                    "metadata": result.get("metadata", {})
                }
                
            except Exception as parse_error:
                # Update status to failed
                cursor.execute("""
                    UPDATE uploaded_files
                    SET parsing_status = 'failed',
                        parsing_error = ?
                    WHERE file_id = ?
                """, (str(parse_error), file_id))
                conn.commit()
                
                logger.error(f"Failed to parse file {file_id}: {parse_error}")
                raise
        
        finally:
            conn.close()
    
    async def _parse_pdf(self, file_path: Path) -> Dict[str, Any]:
        """Extract text from PDF using PyMuPDF."""
        try:
            import fitz  # PyMuPDF
        except ImportError:
            return {
                "content": "[PDF parsing requires PyMuPDF installation: pip install pymupdf]",
                "metadata": {"error": "PyMuPDF not installed"}
            }
        
        try:
            doc = fitz.open(file_path)
            pages = []
            
            for page_num, page in enumerate(doc, start=1):
                text = page.get_text()
                if text.strip():
                    pages.append(f"--- Page {page_num} ---\n{text}")
            
            content = "\n\n".join(pages)
            metadata = {
                "page_count": len(doc),
                "has_text": bool(content.strip())
            }
            
            doc.close()
            
            return {"content": content, "metadata": metadata}
        
        except Exception as e:
            logger.error(f"PDF parsing error: {e}")
            return {
                "content": f"[PDF parsing failed: {e}]",
                "metadata": {"error": str(e)}
            }
    
    async def _parse_image(self, file_path: Path) -> Dict[str, Any]:
        """Analyze image (placeholder - requires Vision API)."""
        try:
            from PIL import Image
        except ImportError:
            return {
                "content": "[Image analysis requires Pillow: pip install pillow]",
                "metadata": {"error": "Pillow not installed"}
            }
        
        try:
            img = Image.open(file_path)
            metadata = {
                "width": img.width,
                "height": img.height,
                "format": img.format,
                "mode": img.mode
            }
            
            # Read EXIF data if available
            exif = img.getexif()
            if exif:
                metadata["exif"] = {k: str(v) for k, v in exif.items()}
            
            # TODO: Add Vision API integration for actual image understanding
            content = f"[Image: {img.width}x{img.height} {img.format}]\n\n"
            content += "Note: Vision API analysis not yet implemented. "
            content += "Image has been uploaded and stored successfully."
            
            return {"content": content, "metadata": metadata}
        
        except Exception as e:
            logger.error(f"Image parsing error: {e}")
            return {
                "content": f"[Image parsing failed: {e}]",
                "metadata": {"error": str(e)}
            }
    
    async def _parse_spreadsheet(self, file_path: Path, filename: str) -> Dict[str, Any]:
        """Parse CSV/Excel file using pandas."""
        try:
            import pandas as pd
        except ImportError:
            return {
                "content": "[Spreadsheet parsing requires pandas: pip install pandas openpyxl]",
                "metadata": {"error": "pandas not installed"}
            }
        
        try:
            # Determine file type
            if filename.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
            
            # Generate markdown table (limit to first 50 rows)
            preview_rows = min(50, len(df))
            df_preview = df.head(preview_rows)
            
            content = f"**Spreadsheet Preview** ({preview_rows} of {len(df)} rows)\n\n"
            content += df_preview.to_markdown(index=False)
            
            if len(df) > preview_rows:
                content += f"\n\n... ({len(df) - preview_rows} more rows)"
            
            # Add summary statistics
            content += "\n\n**Summary Statistics:**\n"
            for col in df.select_dtypes(include=['number']).columns:
                content += f"\n- {col}: min={df[col].min():.2f}, max={df[col].max():.2f}, avg={df[col].mean():.2f}"
            
            metadata = {
                "rows": len(df),
                "columns": len(df.columns),
                "column_names": list(df.columns),
                "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()}
            }
            
            return {"content": content, "metadata": metadata}
        
        except Exception as e:
            logger.error(f"Spreadsheet parsing error: {e}")
            return {
                "content": f"[Spreadsheet parsing failed: {e}]",
                "metadata": {"error": str(e)}
            }
    
    async def _parse_document(self, file_path: Path) -> Dict[str, Any]:
        """Extract text from DOCX or plain text."""
        try:
            # Try reading as plain text first
            if file_path.suffix == ".txt":
                content = file_path.read_text(encoding="utf-8")
                return {
                    "content": content,
                    "metadata": {"char_count": len(content)}
                }
            
            # DOCX parsing (requires python-docx)
            try:
                import docx
            except ImportError:
                return {
                    "content": "[DOCX parsing requires python-docx: pip install python-docx]",
                    "metadata": {"error": "python-docx not installed"}
                }
            
            doc = docx.Document(file_path)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            content = "\n\n".join(paragraphs)
            
            metadata = {
                "paragraph_count": len(paragraphs),
                "char_count": len(content)
            }
            
            return {"content": content, "metadata": metadata}
        
        except Exception as e:
            logger.error(f"Document parsing error: {e}")
            return {
                "content": f"[Document parsing failed: {e}]",
                "metadata": {"error": str(e)}
            }
    
    def get_file_metadata(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve file metadata from database."""
        conn = sqlite3.connect(str(self.db_path))
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT file_id, filename, file_type, mime_type, file_size,
                       parsing_status, parsed_content, metadata_json, uploaded_at
                FROM uploaded_files
                WHERE file_id = ?
            """, (file_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            file_id, filename, file_type, mime_type, file_size, \
            parsing_status, parsed_content, metadata_json, uploaded_at = row
            
            return {
                "file_id": file_id,
                "filename": filename,
                "file_type": file_type,
                "mime_type": mime_type,
                "file_size": file_size,
                "parsing_status": parsing_status,
                "content": parsed_content,
                "metadata": json.loads(metadata_json) if metadata_json else {},
                "uploaded_at": uploaded_at
            }
        finally:
            conn.close()
    
    def list_user_files(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """List files uploaded by user."""
        conn = sqlite3.connect(str(self.db_path))
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT file_id, filename, file_type, file_size,
                       parsing_status, uploaded_at
                FROM uploaded_files
                WHERE user_id = ?
                ORDER BY uploaded_at DESC
                LIMIT ?
            """, (user_id, limit))
            
            files = []
            for row in cursor.fetchall():
                files.append({
                    "file_id": row[0],
                    "filename": row[1],
                    "file_type": row[2],
                    "file_size": row[3],
                    "parsing_status": row[4],
                    "uploaded_at": row[5]
                })
            
            return files
        finally:
            conn.close()
