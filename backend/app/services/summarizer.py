"""Document summarization service."""
import logging
from typing import Dict, Any
from openai import OpenAI

from app.config import Config
from app.database import get_db_service
from app.utils.errors import NotFoundError

logger = logging.getLogger(__name__)


class SummarizerService:
    """Service for generating document summaries."""

    def __init__(self):
        self.client = OpenAI(
            api_key=Config.OPENROUTER_API_KEY,
            base_url=Config.OPENROUTER_BASE_URL
        )
        self.db = get_db_service()

    def summarize(self, content: str, document_id: str) -> Dict[str, Any]:
        """
        Generate a summary and key insights from document content.

        Args:
            content: The document content to summarize
            document_id: ID of the document (for saving summary)

        Returns:
            Dict with summary and statistics

        Raises:
            NotFoundError: If document doesn't exist
        """
        logger.debug(f"Generating summary for document {document_id}")

        # Verify document exists
        doc = self.db.get_document_by_id(document_id)
        if not doc:
            logger.warning(f"Document not found: {document_id}")
            raise NotFoundError(f"Document with ID {document_id} not found")

        try:
            # Generate summary
            summary_prompt = f"""
            Please provide a concise summary of the following document.
            Focus on the main points and key takeaways.

            Document:
            {content}

            Provide:
            1. A brief summary (2-3 sentences)
            2. Key points (3-5 bullet points)
            3. Main themes or topics
            """

            logger.debug(f"Calling LLM for summary generation")
            response = self.client.chat.completions.create(
                model=Config.MODEL_NAME,
                messages=[
                    {"role": "system", "content": "You are a helpful document analyst."},
                    {"role": "user", "content": summary_prompt}
                ]
            )

            summary_text = response.choices[0].message.content
            logger.info(f"Summary generated successfully for document {document_id}")

            # Calculate statistics
            word_count = len(content.split())
            line_count = len(content.split('\n'))

            # Save summary to document
            summary_saved = False
            try:
                self.db.update_document(document_id, {'summary': summary_text})
                logger.debug(f"Summary saved to database for document {document_id}")
                summary_saved = True
            except Exception as e:
                logger.error(f"Failed to save summary to database: {str(e)}")

            return {
                "summary": summary_text,
                "word_count": word_count,
                "line_count": line_count,
                "summary_saved": summary_saved
            }

        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}", exc_info=True)
            raise


# Singleton instance
_summarizer_service = None

def get_summarizer_service() -> SummarizerService:
    global _summarizer_service
    if _summarizer_service is None:
        _summarizer_service = SummarizerService()
    return _summarizer_service
