import { ChevronDown, FileText } from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

interface SummaryPanelProps {
  summary: string | null;
  filename?: string;
  isExpanded: boolean;
  onExpandedChange: (expanded: boolean) => void;
}

export function SummaryPanel({
  summary,
  filename,
  isExpanded,
  onExpandedChange,
}: SummaryPanelProps) {
  // Don't render if no summary
  if (!summary) {
    return null;
  }

  return (
    <Card className="flex flex-col h-full">
      <CardHeader className={`pb-3 shrink-0 ${!isExpanded ? "border-b" : ""}`}>
        <button
          onClick={() => onExpandedChange(!isExpanded)}
          className="flex items-center justify-between w-full hover:opacity-80 transition-opacity"
        >
          <div className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            <div className="text-left">
              <CardTitle className="text-base">Summary</CardTitle>
              {filename && (
                <CardDescription className="text-xs">
                  {filename}
                </CardDescription>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2">
            {!isExpanded && (
              <span className="text-xs text-muted-foreground">
                Expand to Read Summary
              </span>
            )}
            <ChevronDown
              className={`h-5 w-5 transition-transform duration-300 ${
                isExpanded ? "transform rotate-180" : ""
              }`}
            />
          </div>
        </button>
      </CardHeader>

      <CardContent
        className={`pt-2 pb-2 flex-1 overflow-y-auto min-h-0 transition-opacity duration-300 ${
          isExpanded ? "opacity-100" : "opacity-0"
        }`}
      >
        <div className="flex prose prose-sm max-w-none dark:prose-invert">
          <div className="whitespace-pre-wrap text-sm leading-relaxed text-foreground">
            {summary}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
