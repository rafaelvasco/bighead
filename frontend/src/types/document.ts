

export interface Document {
  id: string;
  filename: string;
  uploaded_at: string;
  chunk_count: number;
  word_count?: number;
  line_count?: number;
}

export interface DocumentData {
  document: {
    id: string;
    filename: string;
    summary: string | null;
    content: string;
    word_count: number;
    line_count: number;
    chunk_count: number;
    created_at: string;
    updated_at: string;
  };
  chat_history: ChatMessage[];
}

export interface UploadResponse {
  message: string;
  filename: string;
  document_id: string;
  is_update: boolean;
}

export interface ChatMessage {
  id: number;
  document_id: string;
  sender: 'human' | 'ai';
  message: string;
  sources: Array<{
    content: string;
    reference: string;
    filename: string;
    line_start: number;
    line_end: number;
    relevance_score?: number;
  }> | null;
  created_at: string;
}
