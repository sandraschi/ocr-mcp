import { Inbox as InboxIcon, RefreshCw, Search } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

interface CorpusDoc {
  id: string;
  source_path?: string;
  title?: string;
  backend?: string;
  created_at?: string;
  ocr_excerpt?: string;
}

interface JobStatus {
  job_id: string;
  status: string;
  filename: string;
  result?: unknown;
  error?: string | null;
}

export function Inbox() {
  const [docs, setDocs] = useState<CorpusDoc[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [jobId, setJobId] = useState("");
  const [job, setJob] = useState<JobStatus | null>(null);
  const [jobError, setJobError] = useState<string | null>(null);
  const [jobLoading, setJobLoading] = useState(false);

  const fetchInbox = useCallback(async (q?: string) => {
    setLoading(true);
    setError(null);
    try {
      const qs = q?.trim()
        ? `?query=${encodeURIComponent(q.trim())}&sort_by=created_at&limit=50`
        : "?sort_by=created_at&limit=50";
      const res = await fetch(`/api/corpus${qs}`);
      if (!res.ok) {
        const t = await res.text();
        throw new Error(t || `HTTP ${res.status}`);
      }
      const data = (await res.json()) as { results?: CorpusDoc[]; total?: number };
      setDocs(Array.isArray(data.results) ? data.results : []);
      setTotal(typeof data.total === "number" ? data.total : 0);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load inbox");
      setDocs([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchInbox();
  }, [fetchInbox]);

  const lookupJob = useCallback(async () => {
    const id = jobId.trim();
    if (!id) return;
    setJobLoading(true);
    setJobError(null);
    setJob(null);
    try {
      const res = await fetch(`/api/job/${encodeURIComponent(id)}`);
      if (res.status === 404) throw new Error("Job not found (pruned or server restarted — jobs are in-memory).");
      if (!res.ok) {
        const t = await res.text();
        throw new Error(t || `HTTP ${res.status}`);
      }
      setJob((await res.json()) as JobStatus);
    } catch (e: unknown) {
      setJobError(e instanceof Error ? e.message : "Job lookup failed");
    } finally {
      setJobLoading(false);
    }
  }, [jobId]);

  return (
    <div data-testid="inbox-page" className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
            <InboxIcon className="h-8 w-8 text-blue-400" />
            Inbox
          </h1>
          <p className="text-sm text-slate-300 mt-1 max-w-2xl">
            Recently processed documents (corpus index, newest first) plus batch-job lookup.
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          className="border-slate-600 text-slate-200 shrink-0"
          onClick={() => void fetchInbox(query)}
          disabled={loading}
          data-testid="inbox-refresh"
        >
          {loading ? <RefreshCw className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4 mr-2" />}
          Refresh
        </Button>
      </div>

      <div className="flex gap-2">
        <Input
          data-testid="inbox-search"
          className="bg-slate-950 border-slate-800 text-sm text-slate-100 placeholder:text-slate-300"
          placeholder="Search title, path, or excerpt…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") void fetchInbox(query);
          }}
        />
        <Button
          variant="outline"
          size="sm"
          className="border-slate-600 text-slate-200 shrink-0"
          onClick={() => void fetchInbox(query)}
          disabled={loading}
        >
          <Search className="h-4 w-4 mr-2" />
          Search
        </Button>
      </div>

      {loading && <p className="text-sm text-slate-300">Loading inbox…</p>}
      {error && (
        <Card className="bg-red-950/20 border-red-900">
          <CardContent className="pt-4 text-sm text-red-300">
            Backend unreachable: {error}{" "}
            <button className="underline" onClick={() => void fetchInbox(query)}>
              retry
            </button>
          </CardContent>
        </Card>
      )}

      {!loading && !error && docs.length === 0 && (
        <Card className="bg-slate-900/50 border-slate-800">
          <CardContent className="pt-6 pb-6 text-center text-sm text-slate-300">
            Nothing here yet — process a file on the Process page and it will appear here automatically.
          </CardContent>
        </Card>
      )}

      <div data-testid="inbox-list" className="grid gap-3">
        {docs.map((d) => (
          <Card key={d.id} data-testid="inbox-item" className="bg-slate-900/50 border-slate-800">
            <CardHeader className="pb-2">
              <CardTitle className="text-slate-100 text-sm">{d.title || d.source_path || d.id}</CardTitle>
              <CardDescription className="text-slate-300 text-sm">
                {[d.backend, d.created_at, d.source_path].filter(Boolean).join(" · ")}
              </CardDescription>
            </CardHeader>
            {d.ocr_excerpt && (
              <CardContent className="pt-0">
                <p className="text-sm text-slate-300 line-clamp-2">{d.ocr_excerpt}</p>
              </CardContent>
            )}
          </Card>
        ))}
      </div>
      {!loading && !error && docs.length > 0 && (
        <p className="text-sm text-slate-300">
          Showing {docs.length} of {total} indexed documents.
        </p>
      )}

      <Card className="bg-slate-900/50 border-slate-800">
        <CardHeader>
          <CardTitle className="text-slate-100 text-base">Batch job lookup</CardTitle>
          <CardDescription className="text-slate-300">
            Jobs are in-memory — IDs come from POST /api/process_batch responses.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex gap-2">
            <Input
              data-testid="inbox-job-input"
              className="bg-slate-950 border-slate-800 text-sm text-slate-100 placeholder:text-slate-300"
              placeholder="job id…"
              value={jobId}
              onChange={(e) => setJobId(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") void lookupJob();
              }}
            />
            <Button
              variant="outline"
              size="sm"
              className="border-slate-600 text-slate-200 shrink-0"
              onClick={() => void lookupJob()}
              disabled={jobLoading || !jobId.trim()}
              data-testid="inbox-job-lookup"
            >
              Look up
            </Button>
          </div>
          {jobLoading && <p className="text-sm text-slate-300">Looking up job…</p>}
          {jobError && <p className="text-sm text-red-300">{jobError}</p>}
          {job && (
            <div data-testid="inbox-job-result" className="text-sm text-slate-300 space-y-1">
              <p>
                <span className="text-slate-300">Status:</span> {job.status}
              </p>
              <p>
                <span className="text-slate-300">File:</span> {job.filename}
              </p>
              {job.error && (
                <p className="text-red-300">
                  <span className="text-slate-300">Error:</span> {job.error}
                </p>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
