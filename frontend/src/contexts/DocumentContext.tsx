import { createContext, useContext, useState, useCallback } from 'react';
import type { ReactNode } from 'react';
import type { Document, ChatMessage } from '../types/document';

export interface DocumentState {
  documents: Document[];
  selectedDocument: Document | null;
  documentContent: string | null;
  summary: string | null;
  chatHistory: ChatMessage[];
  isLoading: boolean;
  error: string | null;
}

interface DocumentContextValue extends DocumentState {
  setDocuments: (documents: Document[]) => void;
  setSelectedDocument: (document: Document | null) => void;
  setDocumentContent: (content: string | null) => void;
  setSummary: (summary: string | null) => void;
  setChatHistory: (history: ChatMessage[]) => void;
  setIsLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  selectDocumentByFilename: (filename: string | null) => void;
  addDocument: (document: Document) => void;
  removeDocument: (filename: string) => void;
  updateDocument: (filename: string, updates: Partial<Document>) => void;
  clearSelection: () => void;
}

const DocumentContext = createContext<DocumentContextValue | undefined>(undefined);

export function DocumentProvider({ children }: { children: ReactNode }) {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  const [documentContent, setDocumentContent] = useState<string | null>(null);
  const [summary, setSummary] = useState<string | null>(null);
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const selectDocumentByFilename = useCallback((filename: string | null) => {
    if (!filename) {
      setSelectedDocument(null);
      setDocumentContent(null);
      setSummary(null);
      setChatHistory([]);
      return;
    }

    const doc = documents.find(d => d.filename === filename);
    if (doc) {
      setSelectedDocument(doc);
      // Clear content, summary, and chat history when switching documents
      // They will be loaded as needed
      setDocumentContent(null);
      setSummary(null);
      setChatHistory([]);
    }
  }, [documents]);

  const addDocument = useCallback((document: Document) => {
    setDocuments(prev => {
      // Check if document already exists
      const exists = prev.some(d => d.filename === document.filename);
      if (exists) {
        // Update existing document
        return prev.map(d => d.filename === document.filename ? document : d);
      }
      // Add new document
      return [...prev, document];
    });
  }, []);

  const removeDocument = useCallback((filename: string) => {
    setDocuments(prev => prev.filter(d => d.filename !== filename));

    // If the removed document was selected, clear selection
    if (selectedDocument?.filename === filename) {
      setSelectedDocument(null);
      setDocumentContent(null);
      setSummary(null);
      setChatHistory([]);
    }
  }, [selectedDocument]);

  const updateDocument = useCallback((filename: string, updates: Partial<Document>) => {
    setDocuments(prev => prev.map(d =>
      d.filename === filename ? { ...d, ...updates } : d
    ));

    // Update selected document if it's the one being updated
    if (selectedDocument?.filename === filename) {
      setSelectedDocument(prev => prev ? { ...prev, ...updates } : null);
    }
  }, [selectedDocument]);

  const clearSelection = useCallback(() => {
    setSelectedDocument(null);
    setDocumentContent(null);
    setSummary(null);
    setChatHistory([]);
  }, []);

  const value: DocumentContextValue = {
    documents,
    selectedDocument,
    documentContent,
    summary,
    chatHistory,
    isLoading,
    error,
    setDocuments,
    setSelectedDocument,
    setDocumentContent,
    setSummary,
    setChatHistory,
    setIsLoading,
    setError,
    selectDocumentByFilename,
    addDocument,
    removeDocument,
    updateDocument,
    clearSelection,
  };

  return (
    <DocumentContext.Provider value={value}>
      {children}
    </DocumentContext.Provider>
  );
}

export function useDocumentContext() {
  const context = useContext(DocumentContext);
  if (context === undefined) {
    throw new Error('useDocumentContext must be used within a DocumentProvider');
  }
  return context;
}
