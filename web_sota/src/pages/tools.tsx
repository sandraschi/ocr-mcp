import { ChevronDown, ChevronRight, Loader2, RefreshCw, Wrench } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";

interface ToolInfo {
  name: string;
  description: string;
  parameters?: Record<string, unknown> | null;
}

export function Tools() {
  const [tools, setTools] = useState<ToolInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<string | null>(null);

  const fetchTools = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/tools");
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = (await res.json()) as { tools?: ToolInfo[]; error?: string };
      if (data.error) throw new Error(data.error);
      setTools(Array.isArray(data.tools) ? data.tools : []);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load tools");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchTools();
  }, [fetchTools]);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
            <Wrench className="h-8 w-8 text-amber-400" />
            Tools
          </h1>
          <p className="text-sm text-slate-400 mt-1 max-w-2xl">
            Live MCP tool surface discovered from the FastMCP server. Click a tool to expand its schema.
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          className="border-slate-600 text-slate-200 shrink-0"
          onClick={() => void fetchTools()}
          disabled={loading}
        >
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4 mr-2" />}
          Refresh
        </Button>
      </div>

      {error && <p className="text-sm text-red-400 bg-red-500/10 border border-red-500/20 rounded-md p-3">{error}</p>}

      <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-xl">
        <CardHeader>
          <CardTitle className="text-slate-100 text-base">
            MCP tools <span className="text-slate-500 font-normal">({tools.length} registered)</span>
          </CardTitle>
          <CardDescription className="text-slate-400">
            Portmanteau tools group multiple operations behind one entry point.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[min(65vh,560px)] rounded-md border border-slate-800 bg-slate-950 p-2">
            {tools.length === 0 && !loading && !error ? (
              <p className="text-sm text-slate-500 p-3">No tools discovered.</p>
            ) : (
              <div className="space-y-1">
                {tools.map((tool) => (
                  <div key={tool.name} className="rounded-md border border-slate-800/70">
                    <button
                      type="button"
                      onClick={() => setExpanded(expanded === tool.name ? null : tool.name)}
                      className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-left hover:bg-slate-800/50 transition-colors"
                    >
                      {expanded === tool.name ? (
                        <ChevronDown className="h-4 w-4 shrink-0 text-slate-500" />
                      ) : (
                        <ChevronRight className="h-4 w-4 shrink-0 text-slate-500" />
                      )}
                      <code className="text-sm font-mono text-sky-300">{tool.name}</code>
                    </button>
                    {expanded === tool.name && (
                      <div className="px-4 pb-3 pl-9 space-y-2">
                        <p className="text-xs text-slate-400">{tool.description || "No description."}</p>
                        {tool.parameters ? (
                          <pre className="text-[11px] font-mono text-slate-300 whitespace-pre-wrap break-all bg-slate-900/60 rounded p-2 max-h-64 overflow-auto">
                            {JSON.stringify(tool.parameters, null, 2)}
                          </pre>
                        ) : (
                          <p className="text-[11px] text-slate-500">No parameter schema.</p>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
}
