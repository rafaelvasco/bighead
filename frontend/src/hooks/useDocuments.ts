import { useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDocumentContext } from '../contexts/DocumentContext';
import { api } from '../services/api';
import type { Document } from '../types/document';

export function useDocuments() {
  const navigate = useNavigate();
  const {
    documents,
    selectedDocument,
    documentContent,
    summary,
    chatHistory,
    isLoading,
    error,
    setDocuments,
    setDocumentContent,
    setSummary,
    setChatHistory,
    setIsLoading,
    setError,
    selectDocumentByFilename,
    addDocument,
    removeDocument,
    clearSelection,
  } = useDocumentContext();

  // Auto-load document data when a document is selected
  useEffect(() => {
    const loadDocumentData = async () => {
      if (!selectedDocument?.filename) {
        setDocumentContent(null);
        setSummary(null);
        setChatHistory([]);
        return;
      }

      try {
        const data = await api.getDocumentData(selectedDocument.filename);
        setDocumentContent(data.document.content);
        setSummary(data.document.summary);
        setChatHistory(data.chat_history);
      } catch (err) {
        console.error('Failed to load document data:', err);
        // Don't set error here as it's not critical
      }
    };

    loadDocumentData();
  }, [selectedDocument?.filename, setDocumentContent, setSummary, setChatHistory]);

  // Load all documents from the API
  const loadDocuments = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const docs = await api.listDocuments();
      setDocuments(docs);
      return docs;
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to load documents';
      setError(errorMsg);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [setDocuments, setIsLoading, setError]);

  // Upload a new document
  const uploadDocument = useCallback(async (file: File) => {
    try {
      setIsLoading(true);
      setError(null);

      // Read file content
      const content = await file.text();

      // Upload to backend
      const response = await api.uploadDocument(file);

      // Create document object
      const newDocument: Document = {
        id: response.document_id,
        filename: response.filename,
        uploaded_at: new Date().toISOString(),
        chunk_count: 0, // Will be updated when we reload documents
      };

      // Add to documents list
      addDocument(newDocument);

      // Select the newly uploaded document and navigate to dashboard
      selectDocumentByFilename(response.filename);
      setDocumentContent(content);
      setSummary(null); // Clear summary to trigger regeneration

      // Navigate to document page
      navigate(`/document/${response.document_id}`);

      // Reload documents to get accurate chunk_count
      await loadDocuments();

      return { content, filename: response.filename, documentId: response.document_id };
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to upload document';
      setError(errorMsg);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [navigate, addDocument, selectDocumentByFilename, setDocumentContent, setSummary, setIsLoading, setError, loadDocuments]);

  // Delete a document
  const deleteDocument = useCallback(async (filename: string) => {
    try {
      setIsLoading(true);
      setError(null);

      // Check if this is the currently selected document
      const isCurrentDocument = selectedDocument?.filename === filename;

      await api.deleteDocument(filename);

      // Remove from documents list
      removeDocument(filename);

      // Navigate back to main page if we deleted the current document
      if (isCurrentDocument) {
        navigate('/');
      }

      return true;
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to delete document';
      setError(errorMsg);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [selectedDocument, removeDocument, setIsLoading, setError, navigate]);

  // Select a document by filename
  const selectDocument = useCallback((filename: string | null) => {
    selectDocumentByFilename(filename);
  }, [selectDocumentByFilename]);

  // Query documents
  const queryDocuments = useCallback(async (question: string, documentId: string, top_k: number = 3) => {
    try {
      setError(null);
      const response = await api.queryDocuments(question, documentId, top_k);

      // Immediately add the new messages to the chat history state
      // This prevents timing issues with database reload
      const newMessages = [
        {
          id: Date.now(), // temporary ID
          document_id: documentId,
          sender: 'human' as const,
          message: question,
          sources: null,
          created_at: new Date().toISOString()
        },
        {
          id: Date.now() + 1, // temporary ID
          document_id: documentId,
          sender: 'ai' as const,
          message: response.answer,
          sources: response.sources || [],
          created_at: new Date().toISOString()
        }
      ];
      
      setChatHistory([...chatHistory, ...newMessages]);

      // Optionally reload in background to get correct IDs, but don't replace the UI
      if (selectedDocument?.filename) {
        api.getDocumentData(selectedDocument.filename)
          .then(data => {
            // Only update if the messages are different (to avoid flicker)
            // This ensures we have the correct IDs from the database
            if (data.chat_history.length !== chatHistory.length) {
              setChatHistory(data.chat_history);
            }
          })
          .catch(err => {
            console.error('Failed to reload chat history:', err);
            // Don't overwrite the state if reload fails
          });
      }

      return response;
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to query documents';
      setError(errorMsg);
      throw err;
    }
  }, [setError, selectedDocument?.filename, setChatHistory]);

  // Generate summary for current document
  const generateSummary = useCallback(async (content: string, documentId: string) => {
    try {
      setError(null);
      const response = await api.summarizeDocument(content, documentId);
      setSummary(response.summary);
      return response;
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to generate summary';
      setError(errorMsg);
      throw err;
    }
  }, [setSummary, setError]);

  // Update document content
  const updateDocumentContent = useCallback(async (filename: string, content: string) => {
    try {
      setIsLoading(true);
      setError(null);
      await api.updateDocument(filename, content);

      // Reload document data
      if (selectedDocument?.filename === filename) {
        const data = await api.getDocumentData(filename);
        setDocumentContent(data.document.content);
        setSummary(data.document.summary);
      }

      // Reload documents to update stats
      await loadDocuments();

      return true;
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to update document';
      setError(errorMsg);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [selectedDocument?.filename, setDocumentContent, setSummary, setIsLoading, setError, loadDocuments]);

  // Create document from search
  const createFromSearch = useCallback(async (query: string, filename: string) => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await api.createFromSearch(query, filename);

      // Create document object
      const newDocument: Document = {
        id: response.document_id,
        filename: response.filename,
        uploaded_at: new Date().toISOString(),
        chunk_count: 0,
      };

      // Add to documents list
      addDocument(newDocument);

      // Select the newly created document and navigate to dashboard
      selectDocumentByFilename(response.filename);
      setDocumentContent(response.content);
      setSummary(null);

      // Navigate to document page
      navigate(`/document/${response.document_id}`);

      // Reload documents to get accurate stats
      await loadDocuments();

      return { content: response.content, filename: response.filename, documentId: response.document_id };
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to create document from search';
      setError(errorMsg);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [navigate, addDocument, selectDocumentByFilename, setDocumentContent, setSummary, setIsLoading, setError, loadDocuments]);

  return {
    // State
    documents,
    selectedDocument,
    documentContent,
    summary,
    chatHistory,
    isLoading,
    error,

    // Actions
    loadDocuments,
    uploadDocument,
    deleteDocument,
    selectDocument,
    clearSelection,
    queryDocuments,
    generateSummary,
    updateDocumentContent,
    createFromSearch,
  };
}
