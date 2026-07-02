"""
RAG (Retrieval Augmented Generation) system for document embeddings.

Handles:
- Chunking documents into semantic segments
- Generating embeddings using OpenAI API
- Storing embeddings in ChromaDB vector database
- Semantic search across uploaded documents
"""

import asyncio
import json
import logging
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional


def _now_iso_rag() -> str:
    """ISO-UTC timestamp. Replaces the SQLite-only now() SQL function in the
    file_chunks insert so the SQL is portable to Postgres (contract C3/C6)."""
    return datetime.now(timezone.utc).replace(tzinfo=None).isoformat()

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_OK = True
except ImportError:
    CHROMADB_OK = False
    chromadb = None

try:
    from openai import OpenAI
    OPENAI_OK = True
except ImportError:
    OPENAI_OK = False
    OpenAI = None

# Setup paths
HERE = Path(__file__).parent
HARNESS = HERE.parent.parent
DB_PATH = HARNESS / "memory" / "runs_v3.db"
CHROMA_PATH = HARNESS / "memory" / "chromadb"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Chunking parameters
CHUNK_SIZE = 512  # tokens per chunk
CHUNK_OVERLAP = 50  # token overlap between chunks
EMBEDDING_MODEL = "text-embedding-3-small"  # OpenAI model
EMBEDDING_DIMENSION = 1536  # text-embedding-3-small dimension


class DocumentEmbedder:
    """Generates and stores document embeddings for RAG."""
    
    def __init__(self, db_path: Path, chroma_path: Path):
        self.db_path = db_path
        self.chroma_path = chroma_path
        self.chroma_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB
        if CHROMADB_OK:
            self.chroma_client = chromadb.PersistentClient(
                path=str(chroma_path),
                settings=Settings(anonymized_telemetry=False)
            )
            self.collection = self.chroma_client.get_or_create_collection(
                name="documents",
                metadata={"description": "ArchonHub document embeddings"}
            )
        else:
            self.chroma_client = None
            self.collection = None
            logger.warning("ChromaDB not installed. RAG features disabled.")
        
        # Initialize OpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        if OPENAI_OK and api_key:
            self.openai_client = OpenAI(api_key=api_key)
        else:
            self.openai_client = None
            logger.warning("OpenAI API key not found. Embeddings disabled.")
    
    def chunk_text(self, text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
        """Split text into overlapping chunks."""
        
        # Simple word-based chunking (token approximation: 1 token ≈ 0.75 words)
        words = text.split()
        word_chunk_size = int(chunk_size * 0.75)
        word_overlap = int(overlap * 0.75)
        
        chunks = []
        start = 0
        
        while start < len(words):
            end = start + word_chunk_size
            chunk_words = words[start:end]
            chunk_text = " ".join(chunk_words)
            
            if chunk_text.strip():
                chunks.append(chunk_text)
            
            # Move start position with overlap
            start = end - word_overlap
            
            # Avoid infinite loop if chunk size is too small
            if start <= 0 or word_chunk_size <= word_overlap:
                break
        
        return chunks
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using OpenAI API."""
        
        if not self.openai_client:
            logger.error("OpenAI client not initialized")
            return []
        
        try:
            response = self.openai_client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=texts
            )
            
            embeddings = [item.embedding for item in response.data]
            logger.info(f"Generated {len(embeddings)} embeddings")
            
            return embeddings
        
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return []
    
    async def embed_file(self, file_id: str) -> Dict[str, Any]:
        """Generate embeddings for a file's content."""
        
        if not CHROMADB_OK:
            return {"success": False, "error": "ChromaDB not installed"}
        
        if not self.openai_client:
            return {"success": False, "error": "OpenAI API not configured"}
        
        # Get file content from database
        conn = sqlite3.connect(str(self.db_path))
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT filename, file_type, parsed_content, metadata_json
                FROM uploaded_files
                WHERE file_id = ?
            """, (file_id,))
            
            row = cursor.fetchone()
            if not row:
                return {"success": False, "error": f"File not found: {file_id}"}
            
            filename, file_type, parsed_content, metadata_json = row
            
            if not parsed_content or not parsed_content.strip():
                return {"success": False, "error": "No content to embed"}
            
            # Chunk the content
            chunks = self.chunk_text(parsed_content)
            logger.info(f"Split file {file_id} into {len(chunks)} chunks")
            
            if not chunks:
                return {"success": False, "error": "No chunks generated"}
            
            # Generate embeddings in batches (max 100 per request)
            batch_size = 100
            all_embeddings = []
            
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                embeddings = await self.generate_embeddings(batch)
                all_embeddings.extend(embeddings)
            
            if len(all_embeddings) != len(chunks):
                return {"success": False, "error": "Embedding count mismatch"}
            
            # Store in ChromaDB
            chunk_ids = [f"{file_id}_chunk_{i}" for i in range(len(chunks))]
            metadata = [
                {
                    "file_id": file_id,
                    "filename": filename,
                    "file_type": file_type,
                    "chunk_index": i,
                    "chunk_tokens": len(chunks[i].split())
                }
                for i in range(len(chunks))
            ]
            
            self.collection.add(
                ids=chunk_ids,
                embeddings=all_embeddings,
                documents=chunks,
                metadatas=metadata
            )
            
            # Store chunk metadata in SQLite
            for i, chunk in enumerate(chunks):
                chunk_id = chunk_ids[i]
                cursor.execute("""
                    INSERT INTO file_chunks (
                        chunk_id, file_id, chunk_index, chunk_text, chunk_tokens,
                        embedding_model, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT (chunk_id) DO UPDATE SET
                        file_id = EXCLUDED.file_id,
                        chunk_index = EXCLUDED.chunk_index,
                        chunk_text = EXCLUDED.chunk_text,
                        chunk_tokens = EXCLUDED.chunk_tokens,
                        embedding_model = EXCLUDED.embedding_model,
                        created_at = EXCLUDED.created_at
                """, (
                    chunk_id, file_id, i, chunk, len(chunk.split()),
                    EMBEDDING_MODEL, _now_iso_rag()
                ))
            
            conn.commit()
            
            logger.info(f"Embedded file {file_id}: {len(chunks)} chunks")
            
            return {
                "success": True,
                "file_id": file_id,
                "chunk_count": len(chunks),
                "embedding_model": EMBEDDING_MODEL
            }
        
        except Exception as e:
            logger.error(f"Embedding failed for {file_id}: {e}")
            return {"success": False, "error": str(e)}
        
        finally:
            conn.close()
    
    async def search(self, query: str, limit: int = 5, file_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Semantic search across embedded documents."""
        
        if not CHROMADB_OK or not self.collection:
            return []
        
        if not self.openai_client:
            logger.error("OpenAI client not initialized")
            return []
        
        try:
            # Generate query embedding
            query_embeddings = await self.generate_embeddings([query])
            if not query_embeddings:
                return []
            
            query_embedding = query_embeddings[0]
            
            # Build filter for specific files if provided
            where_filter = None
            if file_ids:
                where_filter = {"file_id": {"$in": file_ids}}
            
            # Search ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=where_filter
            )
            
            # Format results
            formatted_results = []
            
            if results and results["ids"]:
                for i in range(len(results["ids"][0])):
                    formatted_results.append({
                        "chunk_id": results["ids"][0][i],
                        "text": results["documents"][0][i],
                        "distance": results["distances"][0][i] if "distances" in results else None,
                        "metadata": results["metadatas"][0][i] if "metadatas" in results else {}
                    })
            
            logger.info(f"Search for '{query}' returned {len(formatted_results)} results")
            
            return formatted_results
        
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def get_file_chunks(self, file_id: str) -> List[Dict[str, Any]]:
        """Get all chunks for a file."""
        
        conn = sqlite3.connect(str(self.db_path))
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT chunk_id, chunk_index, chunk_text, chunk_tokens
                FROM file_chunks
                WHERE file_id = ?
                ORDER BY chunk_index
            """, (file_id,))
            
            chunks = []
            for row in cursor.fetchall():
                chunks.append({
                    "chunk_id": row[0],
                    "chunk_index": row[1],
                    "text": row[2],
                    "tokens": row[3]
                })
            
            return chunks
        
        finally:
            conn.close()


async def main():
    """Test RAG system."""
    
    if not CHROMADB_OK:
        print("❌ ChromaDB not installed. Run: pip install chromadb")
        return
    
    if not OPENAI_OK:
        print("❌ OpenAI not installed. Run: pip install openai")
        return
    
    embedder = DocumentEmbedder(DB_PATH, CHROMA_PATH)
    
    # Get a recent file to embed
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute("""
        SELECT file_id, filename, file_type
        FROM uploaded_files
        WHERE parsing_status = 'complete' AND parsed_content IS NOT NULL
        ORDER BY uploaded_at DESC
        LIMIT 1
    """)
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        print("⚠️  No files to embed. Upload a file first.")
        return
    
    file_id, filename, file_type = row
    print(f"\n📄 Embedding file: {filename} ({file_type})")
    
    # Embed the file
    result = await embedder.embed_file(file_id)
    print(f"✅ Result: {json.dumps(result, indent=2)}")
    
    # Test search
    if result.get("success"):
        print("\n🔍 Testing search...")
        query = input("Enter search query: ")
        
        search_results = await embedder.search(query, limit=3)
        
        print(f"\n📊 Found {len(search_results)} results:")
        for i, result in enumerate(search_results, 1):
            print(f"\n--- Result {i} ---")
            print(f"File: {result['metadata'].get('filename', 'Unknown')}")
            print(f"Chunk {result['metadata'].get('chunk_index', '?')}")
            print(f"Text preview: {result['text'][:200]}...")
            if result.get('distance'):
                print(f"Distance: {result['distance']:.4f}")


if __name__ == "__main__":
    asyncio.run(main())
