import { useState, useEffect, useRef } from "react";
import { Send, Loader2, Brain, User, Bot } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { useDocuments } from "../hooks/useDocuments";
import { useDocumentContext } from "../contexts/DocumentContext";
import { MarkdownRenderer } from "./MarkdownRenderer";
import { SourceHighlight } from "./SourceHighlight";

export function QueryInterface() {
  const { queryDocuments, selectedDocument, chatHistory } = useDocuments();
  const { setHighlightedLineRange } = useDocumentContext();
  const [question, setQuestion] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  const handleSourceClick = (lineStart: number, lineEnd: number) => {
    setHighlightedLineRange({ start: lineStart, end: lineEnd });
  };

  // Auto-scroll to bottom when chat history updates
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatHistory]);

  const handleQuery = async () => {
    if (!question.trim()) return;

    if (!selectedDocument?.id) {
      setError("Please select a document first");
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      await queryDocuments(question, selectedDocument.id);
      setQuestion(""); // Clear input after successful query
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to query documents"
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleQuery();
    }
  };

  return (
    <Card className="flex flex-col">
      <CardHeader>
        <CardTitle>Chat with Document</CardTitle>
        <CardDescription>
          Ask questions about your document and view conversation history
        </CardDescription>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col space-y-4 overflow-hidden">
        {/* Chat History */}
        <div className="flex-1 overflow-y-auto space-y-3 pr-2">
          {chatHistory.length === 0 ? (
            <div className="text-center text-muted-foreground py-5">
              <Brain className="h-12 w-12 mx-auto mb-2 opacity-50" />
              <p>No questions asked yet. Start a conversation!</p>
            </div>
          ) : (
            <>
              {chatHistory.map((message) => (
                <div
                  key={message.id}
                  className={`flex gap-3 ${
                    message.sender === "human" ? "justify-end" : "justify-start"
                  }`}
                >
                  <div
                    className={`flex gap-2 max-w-[85%] ${
                      message.sender === "human"
                        ? "flex-row-reverse"
                        : "flex-row"
                    }`}
                  >
                    <div className="shrink-0 mt-1">
                      {message.sender === "human" ? (
                        <User className="h-5 w-5 text-primary" />
                      ) : (
                        <Bot className="h-5 w-5 text-secondary" />
                      )}
                    </div>
                    <div
                      className={`rounded-lg p-3 ${
                        message.sender === "human"
                          ? "bg-primary text-primary-foreground"
                          : "bg-muted"
                      }`}
                    >
                      <div className="text-sm">
                        {message.sender === "human" ? (
                          <p className="whitespace-pre-wrap">
                            {message.message}
                          </p>
                        ) : (
                          <MarkdownRenderer content={message.message} />
                        )}
                      </div>
                      {message.sender === "ai" && (
                        <SourceHighlight
                          message={message}
                          onSourceClick={handleSourceClick}
                        />
                      )}
                    </div>
                  </div>
                </div>
              ))}
              <div ref={chatEndRef} />
            </>
          )}
        </div>

        {/* Error Display */}
        {error && (
          <div className="p-3 bg-destructive/10 border border-destructive/20 text-destructive rounded-md">
            <p className="text-sm">{error}</p>
          </div>
        )}

        {/* Loading Indicator */}
        {isLoading && (
          <div className="p-3 bg-primary/5 border border-primary/20 rounded-md">
            <div className="flex items-center gap-2">
              <Loader2 className="h-4 w-4 text-primary animate-spin" />
              <p className="text-sm text-primary">AI is thinking...</p>
            </div>
          </div>
        )}

        {/* Input Area */}
        <div className="flex gap-2 pt-2 border-t">
          <Textarea
            placeholder="Ask a question about your document..."
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={handleKeyPress}
            className="min-h-[60px] resize-none"
            disabled={isLoading}
          />
          <Button
            onClick={handleQuery}
            disabled={isLoading || !question.trim()}
            size="icon"
            className="h-[60px] w-[60px]"
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
