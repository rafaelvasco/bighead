"""
Diagnostic script to test RAG pipeline components
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.retrieval import get_rag_service
from app.config import Config

def test_pipeline():
    print("=" * 60)
    print("RAG Pipeline Diagnostic Test")
    print("=" * 60)

    # Validate config
    try:
        Config.validate()
        print("✓ Configuration validated")
    except Exception as e:
        print(f"✗ Configuration error: {e}")
        return

    # Initialize RAG service
    try:
        rag_service = get_rag_service()
        print("✓ RAG service initialized")
    except Exception as e:
        print(f"✗ Failed to initialize RAG service: {e}")
        import traceback
        traceback.print_exc()
        return

    # Test document store
    try:
        docs = rag_service.get_all_documents()
        print(f"✓ Document store accessible: {len(docs)} documents indexed")
        if docs:
            print("\nIndexed documents:")
            for doc in docs:
                print(f"  - {doc['filename']}: {doc['chunk_count']} chunks")
        else:
            print("\n⚠ Warning: No documents indexed. Upload a document first.")
            return
    except Exception as e:
        print(f"✗ Failed to access document store: {e}")
        import traceback
        traceback.print_exc()
        return

    # Test query pipeline
    test_question = "What is this document about?"
    print(f"\nTesting query pipeline with question: '{test_question}'")
    print("-" * 60)

    try:
        # Run the query
        result = rag_service.query(test_question, top_k=3)

        print("\n✓ Query executed successfully")
        print("\nAnswer:")
        print(f"  {result['answer']}")

        print("\nSources retrieved:")
        if result['sources']:
            for i, source in enumerate(result['sources'], 1):
                print(f"\n  Source {i}:")
                print(f"    Reference: {source['reference']}")
                print(f"    Content preview: {source['content'][:100]}...")
        else:
            print("  ⚠ No sources retrieved (this might indicate a retrieval problem)")

        # Additional diagnostics
        print("\n" + "=" * 60)
        print("Pipeline Diagnostics:")
        print("=" * 60)

        # Check if answer is generic error message
        if "error occurred" in result['answer'].lower():
            print("⚠ Warning: Answer contains error message")

        # Check if answer indicates lack of information
        if "don't have enough information" in result['answer'].lower():
            print("⚠ Warning: LLM couldn't find answer in retrieved documents")
            print("  This could mean:")
            print("    1. Documents don't contain relevant information")
            print("    2. Retrieval is not finding the right chunks")
            print("    3. Chunks are too small/large")

        # Check source count
        if len(result['sources']) == 0:
            print("✗ Problem: No sources retrieved!")
            print("  Possible causes:")
            print("    1. Retriever is not finding similar documents")
            print("    2. Pipeline connection issue")
            print("    3. Embedding mismatch between indexing and querying")
        elif len(result['sources']) < 3:
            print(f"⚠ Warning: Only {len(result['sources'])} sources retrieved (expected 3)")
        else:
            print(f"✓ Retrieved {len(result['sources'])} sources as expected")

    except Exception as e:
        print(f"\n✗ Query failed: {e}")
        import traceback
        traceback.print_exc()
        return

    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)

if __name__ == "__main__":
    test_pipeline()
