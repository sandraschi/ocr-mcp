import { useState, useEffect, useCallback } from 'react';
import { useSearchParams, useLocation, Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { AlertCircle, RefreshCw, Activity, FileText, ChevronDown, ChevronRight, CheckCircle2, Loader2, XCircle } from "lucide-react";
import { useScanStore } from '@/store';

export function Status() {
    const [searchParams] = useSearchParams();
    const location = useLocation();
    const jobIdParam = searchParams.get('job_id') || '';
    const lastOcrJobId = useScanStore((s) => s.lastOcrJobId);

    const [activeJobId, setActiveJobId] = useState(() => jobIdParam || lastOcrJobId || '');
    const [jobData, setJobData] = useState<any>(null);
    const [loading, setLoading] = useState(false);
    const [advancedOpen, setAdvancedOpen] = useState(!!jobIdParam);
    const [advancedIdInput, setAdvancedIdInput] = useState('');

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
            setJobData({ error: err instanceof Error ? err.message : "Network error" });
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        const target = jobIdParam || lastOcrJobId || '';
        if (!target) return;
        setActiveJobId(target);
        void fetchJob(target);
    }, [jobIdParam, lastOcrJobId, location.pathname, fetchJob]);

    useEffect(() => {
        if (!activeJobId || !jobData || jobData.status !== 'processing') return;
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
        if (jobData?.status === 'processing') {
            return (
                <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-500/15 text-amber-200 px-3 py-1 text-sm">
                    <Loader2 className="w-4 h-4 animate-spin" /> Working…
                </span>
            );
        }
        if (jobData?.status === 'completed') {
            return (
                <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/15 text-emerald-200 px-3 py-1 text-sm">
                    <CheckCircle2 className="w-4 h-4" /> Finished
                </span>
            );
        }
        if (jobData?.status === 'failed') {
            return (
                <span className="inline-flex items-center gap-1.5 rounded-full bg-red-500/15 text-red-300 px-3 py-1 text-sm">
                    <XCircle className="w-4 h-4" /> Failed
                </span>
            );
        }
        return null;
    };

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold tracking-tight text-slate-100">Activity</h1>
                <p className="text-sm text-slate-400 mt-1 max-w-2xl">
                    What your last OCR run is doing. You don&apos;t need job IDs — use <Link to="/editor" className="text-blue-400 hover:underline">Your OCR text</Link> for the result.
                </p>
            </div>

            <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-xl">
                <CardHeader>
                    <CardTitle className="text-slate-100 flex items-center gap-2">
                        <Activity className="w-5 h-5 text-emerald-400" /> Latest run
                    </CardTitle>
                    <CardDescription className="text-slate-400">
                        Tracks the most recent OCR from Scanner, Import, or Pipelines.
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-5">
                    {!activeJobId && !lastOcrJobId ? (
                        <p className="text-sm text-slate-500">Nothing running yet. Scan or upload and start OCR first.</p>
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
                                    {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <><RefreshCw className="w-4 h-4 mr-1.5" /> Refresh</>}
                                </Button>
                                <Button size="sm" variant="outline" className="border-slate-600 text-slate-200" asChild>
                                    <Link to="/editor"><FileText className="w-4 h-4 mr-1.5" /> View text</Link>
                                </Button>
                            </div>

                            {jobData?.error && (
                                <div className="flex items-start gap-2 text-red-400 bg-red-500/10 p-3 rounded-md border border-red-500/20 text-sm">
                                    <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                                    <span>{typeof jobData.error === 'string' ? jobData.error : 'Error'}</span>
                                </div>
                            )}

                            {jobData && !jobData.error && (
                                <details className="group">
                                    <summary className="cursor-pointer text-xs text-slate-500 hover:text-slate-400 list-none flex items-center gap-1">
                                        <ChevronRight className="w-3 h-3 group-open:rotate-90 transition-transform" />
                                        Technical details (JSON)
                                    </summary>
                                    <pre className="mt-2 p-3 rounded-md bg-slate-950 border border-slate-800 font-mono text-[11px] text-slate-400 overflow-auto max-h-64">
                                        {JSON.stringify(jobData, null, 2)}
                                    </pre>
                                </details>
                            )}
                        </>
                    )}

                    <button
                        type="button"
                        onClick={() => setAdvancedOpen((o) => !o)}
                        className="text-left text-xs text-slate-500 hover:text-slate-400 flex items-center gap-1 pt-2 border-t border-slate-800 w-full"
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
                            <Button type="button" size="sm" variant="outline" className="text-xs" onClick={() => {
                                const id = advancedIdInput.trim();
                                if (!id) return;
                                setActiveJobId(id);
                                void fetchJob(id);
                            }} disabled={!advancedIdInput.trim()}>
                                Load
                            </Button>
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}
