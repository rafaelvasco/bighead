import type { 
  UploadResponse, 
  Document, 
  DocumentData 
} from '../types/document';
import type { 
  QueryResponse, 
  SummaryResponse 
} from '../types/query';
import type { 
  TableInfo, 
  TableData, 
  ChromaCollection, 
  ChromaDocuments 
} from '../types/admin';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5177/api';

export const api = {
  async uploadDocument(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/documents/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to upload document');
    }

    return response.json();
  },

  async queryDocuments(question: string, document_id: string, top_k: number = 3): Promise<QueryResponse> {
    const response = await fetch(`${API_BASE_URL}/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ question, document_id, top_k }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to query documents');
    }

    return response.json();
  },

  async summarizeDocument(content: string, document_id: string): Promise<SummaryResponse> {
    const response = await fetch(`${API_BASE_URL}/summarize`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ content, document_id }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to summarize document');
    }

    return response.json();
  },

  async createFromSearch(query: string, filename: string): Promise<{ message: string; filename: string; document_id: string; content: string; search_sources: number }> {
    const response = await fetch(`${API_BASE_URL}/documents/create-from-search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query, filename }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to create document from search');
    }

    return response.json();
  },

  async getDocument(filename: string): Promise<{ id: string; filename: string; content: string; summary: string | null; word_count: number; line_count: number; chunk_count: number; created_at: string; updated_at: string }> {
    const response = await fetch(`${API_BASE_URL}/documents/${encodeURIComponent(filename)}`, {
      method: 'GET',
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to get document');
    }

    return response.json();
  },

  async updateDocument(filename: string, content: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/documents/${encodeURIComponent(filename)}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ content }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to update document');
    }
  },

  async listDocuments(): Promise<Document[]> {
    const response = await fetch(`${API_BASE_URL}/documents/`, {
      method: 'GET',
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to list documents');
    }

    const data = await response.json();
    return data.documents;
  },

  async deleteDocument(filename: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/documents/${encodeURIComponent(filename)}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to delete document');
    }
  },

  async getDocumentData(filename: string): Promise<DocumentData> {
    const response = await fetch(`${API_BASE_URL}/documents/${encodeURIComponent(filename)}/data`, {
      method: 'GET',
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to get document data');
    }

    return response.json();
  },

  // Admin endpoints
  async getTables(): Promise<{ tables: TableInfo[] }> {
    const response = await fetch(`${API_BASE_URL}/admin/tables`, {
      method: 'GET',
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to get tables');
    }

    return response.json();
  },

  async getTableData(tableName: string, page: number = 1, perPage: number = 50): Promise<TableData> {
    const response = await fetch(`${API_BASE_URL}/admin/table/${encodeURIComponent(tableName)}?page=${page}&per_page=${perPage}`, {
      method: 'GET',
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to get table data');
    }

    return response.json();
  },

  async updateTableRow(tableName: string, primaryKey: string | number, updates: Record<string, unknown>): Promise<{ message: string; rows_affected: number }> {
    const response = await fetch(`${API_BASE_URL}/admin/table/${encodeURIComponent(tableName)}/row`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ primary_key: primaryKey, updates }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to update row');
    }

    return response.json();
  },

  async deleteTableRow(tableName: string, primaryKey: string | number): Promise<{ message: string; rows_affected: number }> {
    const response = await fetch(`${API_BASE_URL}/admin/table/${encodeURIComponent(tableName)}/row`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ primary_key: primaryKey }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to delete row');
    }

    return response.json();
  },

  async getChromaCollections(): Promise<ChromaCollection> {
    const response = await fetch(`${API_BASE_URL}/admin/chroma/collections`, {
      method: 'GET',
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to get ChromaDB collections');
    }

    return response.json();
  },

  async getChromaDocuments(page: number = 1, perPage: number = 50): Promise<ChromaDocuments> {
    const params = new URLSearchParams({
      page: page.toString(),
      per_page: perPage.toString(),
    });

    const response = await fetch(`${API_BASE_URL}/admin/chroma/documents?${params}`, {
      method: 'GET',
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to get documents');
    }

    return response.json();
  },

  async deleteDocumentEmbeddings(documentId: string): Promise<{ message: string }> {
    const response = await fetch(`${API_BASE_URL}/admin/chroma/document/${encodeURIComponent(documentId)}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to delete document embeddings');
    }

    return response.json();
  },

  async clearSqliteDatabase(): Promise<{ message: string }> {
    const response = await fetch(`${API_BASE_URL}/admin/sqlite/clear`, {
      method: 'POST',
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to clear SQLite database');
    }

    return response.json();
  },

  async clearChromaDatabase(): Promise<{ message: string }> {
    const response = await fetch(`${API_BASE_URL}/admin/chroma/clear`, {
      method: 'POST',
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to clear ChromaDB');
    }

    return response.json();
  },

  async clearAllDatabases(): Promise<{ message: string }> {
    const response = await fetch(`${API_BASE_URL}/admin/clear-all`, {
      method: 'POST',
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to clear all databases');
    }

    return response.json();
  },
};
