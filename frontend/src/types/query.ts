export interface QueryResponse {
  answer: string;
  sources: Array<{
    content: string;
    reference: string;
    filename: string;
    line_start: number;
    line_end: number;
  }>;
}

export interface SummaryResponse {
  summary: string;
  word_count: number;
  line_count: number;
  key_points?: string[];
}
