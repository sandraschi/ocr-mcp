import { RefreshCw, ScrollText } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";

const POLL_MS = 2500;

export function Logger() {
  const [lines, setLines] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const [stickToEnd, setStickToEnd] = useState(true);

  const fetchLogs = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/server_logs?limit=400");
      if (!res.ok) {
        const t = await res.text();
        throw new Error(t || `HTTP ${res.status}`);
      }
      const data = (await res.json()) as { lines?: string[] };
      setLines(Array.isArray(data.lines) ? data.lines : []);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load logs");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchLogs();
  }, [fetchLogs]);

  useEffect(() => {
    const id = window.setInterval(() => void fetchLogs(), POLL_MS);
    return () => window.clearInterval(id);
  }, [fetchLogs]);

  useEffect(() => {
    if (stickToEnd && bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [stickToEnd]);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
            <ScrollText className="h-8 w-8 text-amber-400" />
            Logger
          </h1>
          <p className="text-sm text-slate-400 mt-1 max-w-2xl">
            Recent lines from the FastAPI backend (in-memory buffer). Useful
            when OCR selection or scans misbehave; full detail still lives in
            the server console.
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          className="border-slate-600 text-slate-200 shrink-0"
          onClick={() => void fetchLogs()}
          disabled={loading}
        >
          {loading ? (
            <RefreshCw className="h-4 w-4 animate-spin" />
          ) : (
            <RefreshCw className="h-4 w-4 mr-2" />
          )}
          Refresh
        </Button>
      </div>

      <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-xl">
        <CardHeader>
          <CardTitle className="text-slate-100 text-base">
            Server log tail
          </CardTitle>
          <CardDescription className="text-slate-400">
            Auto-refreshes every {POLL_MS / 1000}s. Sticky scroll to end when
            you stay at the bottom.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <label className="flex items-center gap-2 text-xs text-slate-400">
            <input
              type="checkbox"
              checked={stickToEnd}
              onChange={(e) => setStickToEnd(e.target.checked)}
              className="rounded border-slate-600"
            />
            Follow tail
          </label>
          {error && (
            <p className="text-sm text-red-400 bg-red-500/10 border border-red-500/20 rounded-md p-3">
              {error}
            </p>
          )}
          <ScrollArea className="h-[min(70vh,640px)] rounded-md border border-slate-800 bg-slate-950 p-3">
            <pre className="text-[11px] leading-relaxed font-mono text-slate-300 whitespace-pre-wrap break-all">
              {lines.length === 0
                ? "No log lines yet (or backend not reachable)."
                : lines.join("\n")}
            </pre>
            <div ref={bottomRef} />
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
}
