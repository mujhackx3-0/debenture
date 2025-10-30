"""
RAG system for loan product knowledge base.
"""
import asyncio
from typing import List, Dict, Any
import chromadb
from sentence_transformers import SentenceTransformer

from app.config import settings
from app.utils.logger import logger


LOAN_PRODUCTS_DATA = [
    "Personal Loan: Max ₹5,00,000, Interest Rate: 10-15%, Term: 12-60 months, Eligibility: Salaried employees, good credit score (650+).",
    "Home Loan: Max ₹50,00,000, Interest Rate: 7-9%, Term: 60-360 months, Eligibility: Property owners, stable income.",
    "Education Loan: Max ₹20,00,000, Interest Rate: 8-12%, Term: 12-120 months, Eligibility: Students admitted to recognized institutions.",
    "Car Loan: Max ₹15,00,000, Interest Rate: 9-14%, Term: 12-84 months, Eligibility: Salaried/Self-employed, new or used car purchase.",
    "Eligibility Criteria: All applicants must be 21-60 years old, Indian citizens, with a minimum monthly income of ₹25,000 for personal loans.",
    "KYC Documents: Valid ID proof (Aadhaar, Passport, Driving License), Address proof (Utility Bill, Bank Statement), PAN Card.",
    "Credit Score Impact: A higher credit score (700+) usually results in better interest rates. Scores below 600 might lead to rejection.",
    "Loan Sanction Process: Once approved, a digital sanction letter is issued. Physical documents might be required for final disbursement."
]


class RAGSystem:
    """
    Retrieval-Augmented Generation system for loan knowledge base.
    """
    
    def __init__(self):
        self.chroma_client = None
        self.collection = None
        self.embedder = None
        self._initialized = False
    
    async def initialize(self):
        """
        Initialize RAG system with ChromaDB and embeddings.
        """
        try:
            logger.info("Initializing RAG system...")
            
            # Load embedding model in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            self.embedder = await loop.run_in_executor(
                None,
                lambda: SentenceTransformer(settings.EMBEDDING_MODEL)
            )
            
            # Initialize ChromaDB
            self.chroma_client = chromadb.PersistentClient(path=settings.CHROMA_DB_PERSIST_DIR)
            
            # Get or create collection
            try:
                self.collection = self.chroma_client.get_collection(name="loan_sales_rag_collection")
                logger.info("Loaded existing RAG collection")
            except:
                self.collection = self.chroma_client.create_collection(name="loan_sales_rag_collection")
                await self._index_documents()
                logger.info("Created and indexed new RAG collection")
            
            self._initialized = True
            logger.info("RAG system initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG system: {e}")
            raise
    
    async def _index_documents(self):
        """
        Index loan product documents into ChromaDB.
        """
        logger.info(f"Indexing {len(LOAN_PRODUCTS_DATA)} documents...")
        
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None,
            lambda: self.embedder.encode(LOAN_PRODUCTS_DATA).tolist()
        )
        
        ids = [f"loan_product_{i}" for i in range(len(LOAN_PRODUCTS_DATA))]
        metadatas = [{"source": "internal_loan_data"}] * len(LOAN_PRODUCTS_DATA)
        
        self.collection.add(
            documents=LOAN_PRODUCTS_DATA,
            embeddings=embeddings,
            ids=ids,
            metadatas=metadatas
        )
        
        logger.info(f"Indexed {len(LOAN_PRODUCTS_DATA)} documents successfully")
    
    async def query(self, query_text: str, top_k: int = 3) -> Dict[str, Any]:
        """
        Query the RAG system for relevant documents.
        
        Args:
            query_text: Query string
            top_k: Number of results to return
            
        Returns:
            Dictionary with documents and sources
        """
        if not self._initialized:
            raise RuntimeError("RAG system not initialized")
        
        try:
            # Generate query embedding
            loop = asyncio.get_event_loop()
            query_embedding = await loop.run_in_executor(
                None,
                lambda: self.embedder.encode([query_text])[0].tolist()
            )
            
            # Query ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )
            
            documents = results.get("documents", [[]])[0]
            sources = [f"Internal Knowledge Base - Document {i+1}" for i in range(len(documents))]
            
            return {
                "documents": documents,
                "sources": sources
            }
            
        except Exception as e:
            logger.error(f"RAG query failed: {e}")
            return {"documents": [], "sources": []}
    
    async def cleanup(self):
        """
        Cleanup resources.
        """
        logger.info("Cleaning up RAG system...")
        # ChromaDB client cleanup if needed
        self._initialized = False

