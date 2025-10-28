export interface TableInfo {
  name: string;
  row_count: number;
  columns: Array<{
    name: string;
    type: string;
    nullable: boolean;
    primary_key: boolean;
  }>;
}

export interface TableData {
  table: string;
  columns: string[];
  data: Array<Record<string, unknown>>;
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface ChromaCollection {
  collection_name: string;
  total_embeddings: number;
}

export interface ChromaDocuments {
  documents: Array<{
    filename: string;
    uploaded_at: string | null;
    chunk_count: number;
    embeddings: Array<{
      id: string;
      content: string;
      metadata: Record<string, unknown>;
    }>;
  }>;
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}
