import {
  Activity,
  AlertCircle,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Download,
  FileText,
  FlaskConical,
  Loader2,
  RefreshCw,
  XCircle,
} from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useLocation, useSearchParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useScanStore } from "@/store";

interface BackendStatusInfo {
  name: string;
  description: string;
  model_size: string;
  available: boolean;
  error?: string;
}

interface DlState {
  phase: "idle" | "downloading" | "verifying" | "done" | "failed";
  progress?: number;
  message?: string;
}

interface TestState {
  phase: "idle" | "running" | "ok" | "failed";
  message?: string;
}

function BackendsCard() {
  const [backends, setBackends] = useState<BackendStatusInfo[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dl, setDl] = useState<Record<string, DlState>>({});
  const [test, setTest] = useState<Record<string, TestState>>({});
  const pollRefs = useRef<Record<string, ReturnType<typeof setInterval>>>({});

  const fetchStatus = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/models/status");
      if (!res.ok) throw new Error(`Backend API error: ${res.status}`);
      const data = await res.json();
      const list: BackendStatusInfo[] = Object.values(data.backends ?? {});
      list.sort((a, b) => Number(b.available) - Number(a.available) || a.name.localeCompare(b.name));
      setBackends(list);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to reach backend");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchStatus();
    const refs = pollRefs.current;
    return () => {
      for (const id of Object.values(refs)) clearInterval(id);
    };
  }, [fetchStatus]);

  const pollProgress = useCallback(
    (name: string) => {
      if (pollRefs.current[name]) clearInterval(pollRefs.current[name]);
      let tries = 0;
      pollRefs.current[name] = setInterval(async () => {
        tries += 1;
        try {
          const res = await fetch(`/api/models/download/${encodeURIComponent(name)}/progress`);
          if (!res.ok) throw new Error(`progress API error: ${res.status}`);
          const data = await res.json();
          const status: string = data.status ?? "downloading";
          if (status === "available") {
            clearInterval(pollRefs.current[name]);
            setDl((d) => ({ ...d, [name]: { phase: "done", progress: 100, message: "Ready" } }));
            void fetchStatus();
          } else if (status === "failed") {
            clearInterval(pollRefs.current[name]);
            const msg = typeof data.error === "string" ? data.error : "Download failed";
            setDl((d) => ({ ...d, [name]: { phase: "failed", message: msg } }));
          } else {
            setDl((d) => ({
              ...d,
              [name]: {
                phase: status === "verifying" ? "verifying" : "downloading",
                progress: typeof data.progress === "number" ? data.progress : undefined,
                message: status === "verifying" ? "Verifying…" : "Downloading…",
              },
            }));
          }
        } catch (err: unknown) {
          clearInterval(pollRefs.current[name]);
          setDl((d) => ({
            ...d,
            [name]: { phase: "failed", message: err instanceof Error ? err.message : "Poll error" },
          }));
        }
        if (tries >= 300) {
          clearInterval(pollRefs.current[name]);
          setDl((d) =>
            d[name]?.phase === "done"
              ? d
              : { ...d, [name]: { phase: "failed", message: "Timed out waiting (10 min)" } },
          );
        }
      }, 2000);
    },
    [fetchStatus],
  );

  const handleDownload = useCallback(
    async (name: string) => {
      setDl((d) => ({ ...d, [name]: { phase: "downloading", message: "Starting…" } }));
      try {
        const res = await fetch(`/api/models/download/${encodeURIComponent(name)}`, { method: "POST" });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) throw new Error(typeof data.detail === "string" ? data.detail : `HTTP ${res.status}`);
        if (data.status === "already_available") {
          setDl((d) => ({ ...d, [name]: { phase: "done", progress: 100, message: "Ready" } }));
          void fetchStatus();
        } else {
          pollProgress(name);
        }
      } catch (err: unknown) {
        setDl((d) => ({
          ...d,
          [name]: { phase: "failed", message: err instanceof Error ? err.message : "Download failed" },
        }));
      }
    },
    [fetchStatus, pollProgress],
  );

  const handleTest = useCallback(async (name: string) => {
    setTest((t) => ({ ...t, [name]: { phase: "running", message: "Probing…" } }));
    try {
      const res = await fetch("/api/backends/test", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ backend: name }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok || data.success === false) {
        const msg =
          typeof data.detail === "string"
            ? data.detail
            : typeof data.error === "string"
              ? data.error
              : `Probe failed (HTTP ${res.status})`;
        throw new Error(data.phase ? `${msg} [${String(data.phase)}]` : msg);
      }
      const text = typeof data.text === "string" ? data.text.slice(0, 120) : "OCR probe OK";
      const secs = typeof data.processing_time === "number" ? ` (${data.processing_time.toFixed(1)}s)` : "";
      setTest((t) => ({ ...t, [name]: { phase: "ok", message: `${text}${secs}` } }));
    } catch (err: unknown) {
      setTest((t) => ({
        ...t,
        [name]: { phase: "failed", message: err instanceof Error ? err.message : "Probe failed" },
      }));
    }
  }, []);

  return (
    <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-xl" data-testid="backends-card">
      <CardHeader>
        <CardTitle className="text-slate-100 flex items-center gap-2">
          <Download className="w-5 h-5 text-blue-400" /> Backends
        </CardTitle>
        <CardDescription className="text-slate-300">
          Download models and probe each OCR backend. First Indra run fetches ~76MB automatically.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex items-center gap-2">
          <Button
            onClick={() => void fetchStatus()}
            disabled={loading}
            size="sm"
            className="bg-slate-800 hover:bg-slate-700 text-white"
            data-testid="backends-refresh"
          >
            {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4 mr-1.5" />}
            Refresh
          </Button>
          {error && <span className="text-sm text-red-400">{error}</span>}
        </div>

        {!backends && !error && (
          <p className="text-sm text-slate-300 flex items-center gap-2">
            <Loader2 className="w-4 h-4 animate-spin" /> Loading backends…
          </p>
        )}

        {backends?.map((b) => {
          const d = dl[b.name] ?? { phase: "idle" as const };
          const t = test[b.name] ?? { phase: "idle" as const };
          const busy = d.phase === "downloading" || d.phase === "verifying" || t.phase === "running";
          return (
            <div
              key={b.name}
              className="rounded-md border border-slate-800 bg-slate-950/60 p-3"
              data-testid={`backend-row-${b.name}`}
            >
              <div className="flex flex-wrap items-center gap-2">
                <span
                  className={`h-2.5 w-2.5 rounded-full ${b.available ? "bg-green-500" : "bg-red-500"}`}
                  data-testid={`backend-status-${b.name}`}
                />
                <span className="font-mono text-sm text-slate-100">{b.name}</span>
                <span className="text-xs text-slate-300 rounded bg-slate-800 px-1.5 py-0.5">{b.model_size}</span>
                {!b.available && (
                  <Button
                    size="sm"
                    onClick={() => void handleDownload(b.name)}
                    disabled={busy}
                    className="bg-blue-600 hover:bg-blue-700 text-white text-xs"
                    data-testid={`backend-download-${b.name}`}
                  >
                    {d.phase === "downloading" || d.phase === "verifying" ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin mr-1" />
                    ) : (
                      <Download className="w-3.5 h-3.5 mr-1" />
                    )}
                    Download
                  </Button>
                )}
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => void handleTest(b.name)}
                  disabled={busy || !b.available}
                  className="border-slate-600 text-slate-200 text-xs"
                  data-testid={`backend-test-${b.name}`}
                >
                  {t.phase === "running" ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin mr-1" />
                  ) : (
                    <FlaskConical className="w-3.5 h-3.5 mr-1" />
                  )}
                  Test
                </Button>
                {b.available && d.phase !== "done" && <span className="text-xs text-emerald-400">Ready</span>}
              </div>
              <p className="mt-1 text-xs text-slate-300">{b.description}</p>
              {b.error && <p className="mt-1 text-xs text-red-400">{b.error}</p>}
              {d.phase !== "idle" && (
                <p
                  className={`mt-1 text-xs ${d.phase === "failed" ? "text-red-400" : "text-blue-300"}`}
                  data-testid={`backend-download-state-${b.name}`}
                >
                  {d.phase === "downloading" &&
                    `Downloading…${typeof d.progress === "number" ? ` ${d.progress}%` : ""}`}
                  {d.phase === "verifying" && "Verifying…"}
                  {d.phase === "done" && "Model ready."}
                  {d.phase === "failed" && `Failed: ${d.message ?? "unknown"}`}
                </p>
              )}
              {t.phase !== "idle" && (
                <p
                  className={`mt-1 text-xs ${t.phase === "failed" ? "text-red-400" : t.phase === "ok" ? "text-emerald-400" : "text-slate-300"}`}
                  data-testid={`backend-test-state-${b.name}`}
                >
                  {t.phase === "running" && "Probing…"}
                  {t.phase === "ok" && `OK: ${t.message ?? ""}`}
                  {t.phase === "failed" && `Failed: ${t.message ?? "unknown"}`}
                </p>
              )}
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}

export function Status() {
  const [searchParams] = useSearchParams();
  const location = useLocation();
  const jobIdParam = searchParams.get("job_id") || "";
  const lastOcrJobId = useScanStore((s) => s.lastOcrJobId);

  const [activeJobId, setActiveJobId] = useState(() => jobIdParam || lastOcrJobId || "");
  const [jobData, setJobData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [advancedOpen, setAdvancedOpen] = useState(!!jobIdParam);
  const [advancedIdInput, setAdvancedIdInput] = useState("");

  const fetchJob = useCallback(async (id: string) => {
    if (!id) return;
    setLoading(true);
    try {
      const res = await fetch(`/api/job/${id}`);
      if (res.ok) {
        const data = await res.json();
        setJobData(data);
      } else {
        setJobData({ error: "That result is gone or invalid." });
      }
    } catch (err: unknown) {
      setJobData({
        error: err instanceof Error ? err.message : "Network error",
      });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const target = jobIdParam || lastOcrJobId || "";
    if (!target) return;
    setActiveJobId(target);
    void fetchJob(target);
  }, [jobIdParam, lastOcrJobId, location.pathname, fetchJob]);

  useEffect(() => {
    if (!activeJobId || !jobData || jobData.status !== "processing") return;
    const interval = setInterval(() => fetchJob(activeJobId), 2500);
    return () => clearInterval(interval);
  }, [activeJobId, jobData?.status, fetchJob]);

  const statusPill = () => {
    if (jobData?.error && !jobData?.status) {
      return (
        <span className="inline-flex items-center gap-1.5 rounded-full bg-red-500/15 text-red-300 px-3 py-1 text-sm">
          <XCircle className="w-4 h-4" /> Problem
        </span>
      );
    }
    if (jobData?.status === "processing") {
      return (
        <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-500/15 text-amber-200 px-3 py-1 text-sm">
          <Loader2 className="w-4 h-4 animate-spin" /> Working…
        </span>
      );
    }
    if (jobData?.status === "completed") {
      return (
        <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/15 text-emerald-200 px-3 py-1 text-sm">
          <CheckCircle2 className="w-4 h-4" /> Finished
        </span>
      );
    }
    if (jobData?.status === "failed") {
      return (
        <span className="inline-flex items-center gap-1.5 rounded-full bg-red-500/15 text-red-300 px-3 py-1 text-sm">
          <XCircle className="w-4 h-4" /> Failed
        </span>
      );
    }
    return null;
  };

  return (
    <div className="space-y-6" data-testid="status-page">
      <div data-testid="status-control-3">
        <h1 className="text-3xl font-bold tracking-tight text-slate-100" data-testid="status-title">
          Activity
        </h1>
        <p className="text-sm text-slate-300 mt-1 max-w-2xl">
          What your last OCR run is doing. You don&apos;t need job IDs — use{" "}
          <Link to="/editor" className="text-blue-400 hover:underline">
            Your OCR text
          </Link>{" "}
          for the result.
        </p>
      </div>

      <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-xl">
        <CardHeader>
          <CardTitle className="text-slate-100 flex items-center gap-2">
            <Activity className="w-5 h-5 text-emerald-400" /> Latest run
          </CardTitle>
          <CardDescription className="text-slate-300">
            Tracks the most recent OCR from Scanner, Import, or Pipelines.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          {!activeJobId && !lastOcrJobId ? (
            <p className="text-sm text-slate-300">Nothing running yet. Scan or upload and start OCR first.</p>
          ) : (
            <>
              <div className="flex flex-wrap items-center gap-3">
                {statusPill()}
                {jobData?.filename && (
                  <span className="text-sm text-slate-300 truncate max-w-full" title={jobData.filename}>
                    {jobData.filename}
                  </span>
                )}
                <Button
                  onClick={() => activeJobId && fetchJob(activeJobId)}
                  disabled={loading || !activeJobId}
                  size="sm"
                  className="bg-slate-800 hover:bg-slate-700 text-white"
                >
                  {loading ? (
                    <RefreshCw className="w-4 h-4 animate-spin" />
                  ) : (
                    <>
                      <RefreshCw className="w-4 h-4 mr-1.5" /> Refresh
                    </>
                  )}
                </Button>
                <Button size="sm" variant="outline" className="border-slate-600 text-slate-200" asChild>
                  <Link to="/editor">
                    <FileText className="w-4 h-4 mr-1.5" /> View text
                  </Link>
                </Button>
              </div>

              {jobData?.error && (
                <div className="flex items-start gap-2 text-red-400 bg-red-500/10 p-3 rounded-md border border-red-500/20 text-sm">
                  <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                  <span>{typeof jobData.error === "string" ? jobData.error : "Error"}</span>
                </div>
              )}

              {jobData && !jobData.error && (
                <details className="group">
                  <summary className="cursor-pointer text-xs text-slate-300 hover:text-slate-300 list-none flex items-center gap-1">
                    <ChevronRight className="w-3 h-3 group-open:rotate-90 transition-transform" />
                    Technical details (JSON)
                  </summary>
                  <pre className="mt-2 p-3 rounded-md bg-slate-950 border border-slate-800 font-mono text-[11px] text-slate-300 overflow-auto max-h-64">
                    {JSON.stringify(jobData, null, 2)}
                  </pre>
                </details>
              )}
            </>
          )}

          <button
            type="button"
            onClick={() => setAdvancedOpen((o) => !o)}
            className="text-left text-xs text-slate-300 hover:text-slate-300 flex items-center gap-1 pt-2 border-t border-slate-800 w-full"
          >
            {advancedOpen ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
            Advanced — inspect another job by ID
          </button>
          {advancedOpen && (
            <div className="flex flex-wrap gap-2 items-center p-3 rounded-md bg-slate-950/80 border border-slate-800">
              <input
                type="text"
                placeholder="Internal job id…"
                className="flex-1 min-w-[10rem] rounded-md border-0 py-1.5 px-2 bg-slate-900 text-slate-200 text-xs font-mono ring-1 ring-slate-700"
                value={advancedIdInput}
                onChange={(e) => setAdvancedIdInput(e.target.value)}
              />
              <Button
                type="button"
                size="sm"
                variant="outline"
                className="text-xs"
                onClick={() => {
                  const id = advancedIdInput.trim();
                  if (!id) return;
                  setActiveJobId(id);
                  void fetchJob(id);
                }}
                disabled={!advancedIdInput.trim()}
              >
                Load
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      <BackendsCard />
    </div>
  );
}
