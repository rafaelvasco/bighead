"""RAG (Retrieval-Augmented Generation) service module."""

import logging
import threading
from typing import List, Dict, Any

from haystack import Pipeline, Document
from haystack.components.builders import PromptBuilder
from haystack.components.generators import OpenAIGenerator
from haystack.components.embedders import OpenAITextEmbedder, OpenAIDocumentEmbedder
from haystack.components.writers import DocumentWriter
from haystack_integrations.components.retrievers.chroma import ChromaEmbeddingRetriever
from haystack.utils import Secret

from app.config import Config
from .chromadb_manager import ChromaDBManager
from .text_chunker import TextChunker
from .query_expander import QueryExpander
from .embeddings_manager import EmbeddingsManager

logger = logging.getLogger(__name__)


class RAGService:
    def __init__(self):
        # Initialize ChromaDB document store with retry logic
        self.chromadb_manager = ChromaDBManager()
        self.document_store = self.chromadb_manager.initialize_with_retry()

        # Initialize utilities
        self.text_chunker = TextChunker()
        self.query_expander = QueryExpander()
        self.embeddings_manager = EmbeddingsManager(self.document_store)

        # Initialize OpenAI components for embeddings (directly from OpenAI, not OpenRouter)
        # OpenRouter does not support embedding models, only LLMs
        self.text_embedder = OpenAITextEmbedder(
            api_key=Secret.from_token(Config.OPENAI_API_KEY),
            model=Config.EMBEDDING_MODEL
        )

        self.doc_embedder = OpenAIDocumentEmbedder(
            api_key=Secret.from_token(Config.OPENAI_API_KEY),
            model=Config.EMBEDDING_MODEL
        )

        # Initialize generator
        self.generator = OpenAIGenerator(
            api_key=Secret.from_token(Config.OPENROUTER_API_KEY),
            api_base_url=Config.OPENROUTER_BASE_URL,
            model=Config.MODEL_NAME
        )

        # Setup pipelines
        self._setup_pipelines()

    def _setup_pipelines(self):
        """Setup indexing and query pipelines"""
        # Indexing pipeline
        self.indexing_pipeline = Pipeline()
        self.indexing_pipeline.add_component("embedder", self.doc_embedder)
        self.indexing_pipeline.add_component("writer", DocumentWriter(document_store=self.document_store))
        self.indexing_pipeline.connect("embedder.documents", "writer.documents")

        # Query pipeline
        template = """Given the following context, answer the question.

**Important Instructions:**
- For questions about time periods (like "from X year to Y year"), look for relevant information related to the time range in the document
- Synthesize information from multiple chunks if needed to construct a complete answer
- If the answer is found across multiple sources, combine them logically
- Only say "I don't have enough information" if the information is truly absent from all context
- Focus on the content of the provided document(s) without making assumptions about specific document types

Context:
{% for doc in documents %}
{{ doc.content }}
{% endfor %}

Question: {{ question }}

Answer:"""

        prompt_builder = PromptBuilder(template=template, required_variables=["documents", "question"])
        retriever = ChromaEmbeddingRetriever(document_store=self.document_store)

        self.query_pipeline = Pipeline()
        self.query_pipeline.add_component("text_embedder", self.text_embedder)
        self.query_pipeline.add_component("retriever", retriever)
        self.query_pipeline.add_component("prompt_builder", prompt_builder)
        self.query_pipeline.add_component("llm", self.generator)

        self.query_pipeline.connect("text_embedder.embedding", "retriever.query_embedding")
        self.query_pipeline.connect("retriever.documents", "prompt_builder.documents")
        self.query_pipeline.connect("prompt_builder.prompt", "llm.prompt")

    def index_document(self, filename: str, content: str) -> int:
        """
        Index a document into the vector store with intelligent chunking.

        Args:
            filename: Name of the document
            content: Document content

        Returns:
            Number of chunks created

        Raises:
            Exception: If indexing fails
        """
        logger.debug(f"Indexing document: {filename}")

        try:
            # Use semantic chunking that preserves related information together
            chunks = self.text_chunker.split_text_semantically(content)
            logger.debug(f"Split document into {len(chunks)} chunks")

            # Create Haystack documents
            documents = [
                Document(
                    content=chunk['text'],
                    meta={
                        "filename": filename,
                        "chunk_id": i,
                        "line_start": chunk['line_start'],
                        "line_end": chunk['line_end']
                    }
                )
                for i, chunk in enumerate(chunks)
            ]

            logger.debug(f"Indexing {len(documents)} document chunks for {filename}")
            # Run indexing pipeline
            self.indexing_pipeline.run({"embedder": {"documents": documents}})

            # Verify documents were indexed
            doc_count = self.document_store.count_documents()
            logger.debug(f"Total documents in store after indexing: {doc_count}")
            logger.debug(f"Successfully indexed {len(chunks)} chunks for {filename}")

            return len(chunks)
        except Exception as e:
            logger.error(f"Error indexing document {filename}: {str(e)}", exc_info=True)
            raise

    def query(self, question: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Query the RAG system.

        Args:
            question: The question to ask
            top_k: Number of chunks to retrieve

        Returns:
            Dict with answer and sources

        Raises:
            Exception: If query fails
        """
        logger.debug(f"Processing query: {question[:100]}...")

        try:
            # Expand query for temporal work queries
            expanded_question = self.query_expander.expand_temporal_query(question)
            if expanded_question != question:
                logger.debug(f"Using expanded query: {expanded_question[:100]}...")

            # Check document count before querying
            doc_count = self.document_store.count_documents()

            # Log query details for debugging
            logger.debug(f"Query details - Original: '{question}', Expanded: '{expanded_question}', Top_k: {top_k}")
            
            result = self.query_pipeline.run({
                "text_embedder": {"text": expanded_question},
                "retriever": {"top_k": top_k},
                "prompt_builder": {"question": question}
            }, include_outputs_from={"text_embedder", "retriever", "prompt_builder", "llm"})

            # Get documents from the retriever output
            documents = result.get("retriever", {}).get("documents", [])
            logger.debug(f"Retrieved {len(documents)} relevant chunks")
            
            # Log retrieved documents (debug level)
            for i, doc in enumerate(documents, 1):
                logger.debug(f"Document {i}: {doc.content[:100]}...")

            # Log retrieval diagnostics
            if len(documents) == 0:
                logger.warning("No documents retrieved - possible retrieval issue")
            elif len(documents) < top_k:
                logger.warning(f"Only retrieved {len(documents)} documents out of requested {top_k} - may indicate limited relevant content")
            
            # Check for temporal information in retrieved docs
            has_temporal_info = any(
                '2012' in doc.content and '2019' in doc.content or
                'Sep 2012' in doc.content or 'Jun 2019' in doc.content
                for doc in documents
            )

            # Get answer from LLM
            llm_output = result.get("llm", {})
            answer = llm_output.get("replies", [""])[0] if llm_output else "No response from LLM"
            logger.debug(f"Generated answer: {answer[:100]}...")

            # Extract relevance scores from document metadata
            # ChromaDB uses L2 distance by default: lower score = higher relevance
            # We need to invert: normalize distance then flip so higher = more relevant
            sources = []
            max_score = 1.0
            min_score = 0.0
            
            # First pass: collect all scores to determine min/max for normalization
            scores = []
            for doc in documents:
                score = doc.meta.get('score', None)
                if score is not None:
                    scores.append(float(score))
            
            # Determine normalization bounds
            if scores:
                max_score = max(scores)
                min_score = min(scores)
                logger.debug(f"Score range from retriever: {min_score} to {max_score}")
            
            # Second pass: build sources with normalized relevance scores
            for i, doc in enumerate(documents):
                score = doc.meta.get('score', None)
                
                # Normalize score to 0-1 range, then invert (L2: lower distance = higher relevance)
                if score is not None and max_score != min_score:
                    # Normalize distance to 0-1
                    normalized_distance = (float(score) - min_score) / (max_score - min_score)
                    # Invert: lower distance becomes higher relevance score
                    relevance_score = 1.0 - normalized_distance
                else:
                    # Fallback: use positional relevance if no score available
                    relevance_score = 1.0 - (i / max(len(documents), 1))
                    normalized_distance = None
                
                distance_str = f"{normalized_distance:.3f}" if normalized_distance is not None else "N/A"
                logger.debug(f"Document {i+1}: raw_score={score}, normalized_distance={distance_str}, relevance={relevance_score:.3f}")
                
                sources.append({
                    "content": doc.content,
                    "reference": f"{doc.meta.get('filename', 'unknown')}:{doc.meta.get('line_start', 0)}-{doc.meta.get('line_end', 0)}",
                    "filename": doc.meta.get('filename', 'unknown'),
                    "line_start": doc.meta.get('line_start', 0),
                    "line_end": doc.meta.get('line_end', 0),
                    "relevance_score": round(relevance_score, 3)
                })

            return {
                "answer": answer,
                "sources": sources
            }
        except Exception as e:
            logger.error(f"Error querying RAG system: {str(e)}", exc_info=True)
            raise

    # Delegate methods to embeddins_manager
    def get_all_documents(self) -> List[Dict[str, Any]]:
        """Delegate to embeddings_manager"""
        return self.embeddings_manager.get_all_documents()

    def delete_document(self, filename: str) -> bool:
        """Delegate to embeddings_manager"""
        return self.embeddings_manager.delete_document(filename)

    def get_embeddings_paginated(self, page: int = 1, per_page: int = 50, document_id: str = None) -> Dict[str, Any]:
        """Delegate to embeddings_manager"""
        return self.embeddings_manager.get_embeddings_paginated(page, per_page, document_id)

    def delete_embedding_by_id(self, embedding_id: str) -> bool:
        """Delegate to embeddings_manager"""
        return self.embeddings_manager.delete_embedding_by_id(embedding_id)

    def get_collection_info(self) -> Dict[str, Any]:
        """Delegate to embeddings_manager"""
        return self.embeddings_manager.get_collection_info()

    def get_documents_with_embeddings_paginated(self, page: int = 1, per_page: int = 50) -> Dict[str, Any]:
        """Delegate to embeddings_manager"""
        return self.embeddings_manager.get_documents_with_embeddings_paginated(page, per_page)

    def clear_all_embeddings(self) -> bool:
        """Delegate to embeddings_manager"""
        return self.embeddings_manager.clear_all_embeddings()


# Thread-safe singleton implementation
_rag_service = None
_rag_service_lock = threading.Lock()

def get_rag_service() -> RAGService:
    """
    Get the singleton RAGService instance with thread-safe initialization.
    
    Returns:
        RAGService instance
    """
    global _rag_service
    
    # Double-checked locking pattern for thread safety
    if _rag_service is None:
        with _rag_service_lock:
            # Check again inside the lock to prevent race conditions
            if _rag_service is None:
                logger.info("Initializing new RAGService singleton")
                _rag_service = RAGService()
    else:
        # Log when returning existing instance
        logger.debug("Returning existing RAGService instance")
    
    return _rag_service
