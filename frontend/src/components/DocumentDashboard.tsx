import { useEffect, useState } from 'react';
import { useParams, Navigate } from 'react-router-dom';
import { DocumentEditor } from './DocumentEditor';
import { DocumentEditorV2 } from './DocumentEditorV2';
import { QueryInterface } from './QueryInterface';
import { useDocuments } from '../hooks/useDocuments';
import { Button } from '@/components/ui/button';
import { FileEdit } from 'lucide-react';

export function DocumentDashboard() {
  const { id } = useParams<{ id: string }>();
  const { documentContent, selectedDocument, selectDocument, documents } = useDocuments();

  // Select the document based on URL parameter
  useEffect(() => {
    if (id && (!selectedDocument || selectedDocument.id !== id)) {
      // Find document by ID
      const doc = documents.find(d => d.id === id);
      if (doc) {
        selectDocument(doc.filename);
      }
    }
  }, [id, selectedDocument, documents, selectDocument]);

  // If no ID in URL, redirect to home
  if (!id) {
    return <Navigate to="/" replace />;
  }

  // If document not found in list, show error
  const doc = documents.find(d => d.id === id);
  if (documents.length > 0 && !doc) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-muted-foreground">Document not found</p>
      </div>
    );
  }

  // Loading state
  if (!documentContent) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-muted-foreground">Loading document...</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4 h-[calc(100vh-180px)]">
      {/* Top Section - Document Editor */}
      <div className="h-[55%] min-h-0">
        <DocumentEditorV2 />
      </div>

      {/* Bottom Section - Chat Interface */}
      <div className="h-[45%] min-h-0">
        <QueryInterface />
      </div>
    </div>
  );
}
