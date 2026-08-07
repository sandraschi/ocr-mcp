import { BookOpen, ChevronDown, ChevronRight, Loader2, RefreshCw } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";

interface SkillInfo {
  name: string;
}

export function Skills() {
  const [skills, setSkills] = useState<SkillInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [content, setContent] = useState<string | null>(null);
  const [contentLoading, setContentLoading] = useState(false);

  const fetchSkills = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/skills");
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = (await res.json()) as { skills?: SkillInfo[] };
      setSkills(Array.isArray(data.skills) ? data.skills : []);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load skills");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchSkills();
  }, [fetchSkills]);

  const toggleSkill = useCallback(
    async (name: string) => {
      if (expanded === name) {
        setExpanded(null);
        setContent(null);
        return;
      }
      setExpanded(name);
      setContentLoading(true);
      setContent(null);
      try {
        const res = await fetch(`/api/skills/${encodeURIComponent(name)}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = (await res.json()) as { content?: string; error?: string };
        setContent(data.content ?? data.error ?? "No content.");
      } catch (e: unknown) {
        setContent(e instanceof Error ? e.message : "Failed to load skill");
      } finally {
        setContentLoading(false);
      }
    },
    [expanded],
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
            <BookOpen className="h-8 w-8 text-amber-400" />
            Skills
          </h1>
          <p className="text-sm text-slate-400 mt-1 max-w-2xl">
            Skills teach the LLM how to use OCR-MCP. Click a skill to read its SKILL.md.
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          className="border-slate-600 text-slate-200 shrink-0"
          onClick={() => void fetchSkills()}
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
            Registered skills <span className="text-slate-500 font-normal">({skills.length})</span>
          </CardTitle>
          <CardDescription className="text-slate-400">
            Content served from src/ocr_mcp/skills/{`{name}`}/SKILL.md.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[min(65vh,560px)] rounded-md border border-slate-800 bg-slate-950 p-2">
            {skills.length === 0 && !loading && !error ? (
              <p className="text-sm text-slate-500 p-3">No skills found.</p>
            ) : (
              <div className="space-y-1">
                {skills.map((skill) => (
                  <div key={skill.name} className="rounded-md border border-slate-800/70">
                    <button
                      type="button"
                      onClick={() => void toggleSkill(skill.name)}
                      className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-left hover:bg-slate-800/50 transition-colors"
                    >
                      {expanded === skill.name ? (
                        <ChevronDown className="h-4 w-4 shrink-0 text-slate-500" />
                      ) : (
                        <ChevronRight className="h-4 w-4 shrink-0 text-slate-500" />
                      )}
                      <code className="text-sm font-mono text-sky-300">{skill.name}</code>
                    </button>
                    {expanded === skill.name && (
                      <div className="px-4 pb-3 pl-9">
                        {contentLoading ? (
                          <Loader2 className="h-4 w-4 animate-spin text-slate-500" />
                        ) : (
                          <pre className="text-[11px] font-mono text-slate-300 whitespace-pre-wrap break-all bg-slate-900/60 rounded p-3 max-h-[50vh] overflow-auto">
                            {content}
                          </pre>
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
