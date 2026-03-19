import { useState, useEffect, useCallback } from 'react';
import { useSearchParams, useLocation } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Download, RefreshCw, FileText, FileJson, FileCode2, ChevronDown, ChevronRight } from "lucide-react";
import { useScanStore } from '@/store';

export function Editor() {
    const [searchParams] = useSearchParams();
    const location = useLocation();
    const jobIdParam = searchParams.get('job_id') || '';
    const lastOcrJobId = useScanStore((s) => s.lastOcrJobId);
    /** Internal only — never shown in default UI */
    const [activeJobId, setActiveJobId] = useState(() => jobIdParam || lastOcrJobId || '');
    const [status, setStatus] = useState<any>(null);
    const [loading, setLoading] = useState(false);
    const [editedText, setEditedText] = useState("");
    const [exporting, setExporting] = useState(false);
    const [advancedOpen, setAdvancedOpen] = useState(!!jobIdParam);
    const [advancedIdInput, setAdvancedIdInput] = useState('');

    const fetchJob = useCallback(async (id: string) => {
        if (!id) return;
        setLoading(true);
        try {
            const res = await fetch(`/api/job/${id}`);
            if (res.ok) {
                const data = await res.json();
                setStatus(data);
                if (data.status === 'completed' && data.result) {
                    if (data.result.text != null && data.result.text !== '') {
                        setEditedText(data.result.text);
                    } else if (data.result.success === false && data.result.error) {
                        setEditedText(`[OCR failed]\n\n${data.result.error}`);
                    }
                }
            } else {
                setStatus({ error: "Could not load this result. It may have expired." });
            }
        } catch (err: unknown) {
            setStatus({ error: err instanceof Error ? err.message : "Network error" });
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
        if (!activeJobId || !status || status.status !== 'processing') return;
        const interval = setInterval(() => void fetchJob(activeJobId), 2500);
        return () => clearInterval(interval);
    }, [activeJobId, status?.status, fetchJob]);

    const humanLine = () => {
        if (!activeJobId && !lastOcrJobId) return 'Run a scan or upload, then OCR — your text shows up here. No IDs to copy.';
        if (status?.status === 'processing') return 'Reading your document…';
        if (status?.status === 'completed') {
            const fn = status.filename;
            return fn ? `Done — ${fn}` : 'Done — ready to edit below.';
        }
        if (status?.status === 'failed') return 'Something went wrong.';
        if (status?.error) return String(status.error);
        return 'Ready.';
    };

    const handleExport = async (type: string) => {
        setExporting(true);
        try {
            const payload = {
                export_type: type,
                content: { text: editedText, original_job: activeJobId },
                filename: `ocr_export_${Date.now()}`,
            };

            const res = await fetch(`/api/export`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (res.ok) {
                const data = await res.json();
                let blobParts = data.content;
                if (type === 'json' && typeof data.content !== 'string') {
                    blobParts = JSON.stringify(data.content, null, 2);
                }
                const blob = new Blob([blobParts], { type: data.media_type || 'text/plain' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = data.filename || `export.${type}`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            }
        } catch (err) {
            console.error("Export failed", err);
        } finally {
            setExporting(false);
        }
    };

    const loadAdvancedId = () => {
        const id = advancedIdInput.trim();
        if (!id) return;
        setActiveJobId(id);
        void fetchJob(id);
    };

    return (
        <div className="space-y-4 flex flex-col h-[calc(100vh-8rem)]">
            <div className="shrink-0">
                <h1 className="text-3xl font-bold tracking-tight text-slate-100">Your OCR text</h1>
                <p className="text-sm text-slate-400 mt-1 max-w-2xl">
                    Follows your latest scan or upload automatically. Edit below, then export.
                </p>
            </div>

            <div className="flex flex-wrap items-center gap-3 shrink-0 rounded-lg border border-slate-800 bg-slate-900/40 px-4 py-3">
                <p className="text-sm text-slate-300 flex-1 min-w-[12rem]">{humanLine()}</p>
                <Button
                    onClick={() => activeJobId && fetchJob(activeJobId)}
                    disabled={loading || !activeJobId}
                    className="bg-slate-800 hover:bg-slate-700 text-white shrink-0"
                >
                    {loading ? <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> : <RefreshCw className="w-4 h-4 mr-2" />}
                    Refresh
                </Button>
            </div>

            <button
                type="button"
                onClick={() => setAdvancedOpen((o) => !o)}
                className="text-left text-xs text-slate-500 hover:text-slate-400 flex items-center gap-1 shrink-0"
            >
                {advancedOpen ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                Advanced — load by internal job ID (support / debugging only)
            </button>
            {advancedOpen && (
                <div className="flex flex-wrap gap-2 items-center shrink-0 p-3 rounded-md bg-slate-950/80 border border-slate-800">
                    <input
                        type="text"
                        placeholder="job_… or scan_ocr_…"
                        className="flex-1 min-w-[10rem] rounded-md border-0 py-1.5 px-2 bg-slate-900 text-slate-200 text-xs font-mono ring-1 ring-slate-700"
                        value={advancedIdInput}
                        onChange={(e) => setAdvancedIdInput(e.target.value)}
                    />
                    <Button type="button" size="sm" variant="outline" className="border-slate-600 text-slate-300 text-xs" onClick={loadAdvancedId} disabled={!advancedIdInput.trim()}>
                        Load
                    </Button>
                    {lastOcrJobId && (
                        <Button
                            type="button"
                            size="sm"
                            variant="ghost"
                            className="text-xs text-slate-500"
                            onClick={() => {
                                setAdvancedIdInput(lastOcrJobId);
                                setActiveJobId(lastOcrJobId);
                                void fetchJob(lastOcrJobId);
                            }}
                        >
                            Paste latest ID
                        </Button>
                    )}
                </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 flex-1 min-h-0">
                <Card className="lg:col-span-3 bg-slate-900/50 border-slate-800 backdrop-blur-xl flex flex-col min-h-0">
                    <CardHeader className="shrink-0">
                        <CardTitle className="text-slate-100 flex items-center gap-2"><FileText className="w-5 h-5 text-blue-400" /> Text</CardTitle>
                        <CardDescription className="text-slate-400">Edit the extracted text, then export.</CardDescription>
                    </CardHeader>
                    <CardContent className="flex flex-col flex-1 min-h-0 pb-6">
                        {status && status.status === 'processing' ? (
                            <div className="flex flex-col items-center justify-center h-full text-slate-400">
                                <RefreshCw className="w-8 h-8 animate-spin mb-4 text-blue-500" />
                                <p>OCR in progress…</p>
                            </div>
                        ) : status && status.error ? (
                            <div className="p-4 bg-red-500/10 border border-red-500/20 text-red-400 rounded-md text-sm">
                                {status.error}
                            </div>
                        ) : (
                            <textarea
                                className="w-full flex-1 min-h-0 rounded-md border-0 py-3 px-4 bg-slate-950 text-slate-100 ring-1 ring-inset ring-slate-800 focus:ring-2 focus:ring-blue-600 sm:text-sm font-mono resize-none overflow-auto"
                                value={editedText}
                                onChange={(e) => setEditedText(e.target.value)}
                                placeholder={activeJobId ? "Waiting for OCR… or nothing returned yet." : "Go to Scanner or Import, run OCR, then come back — text appears here."}
                            />
                        )}
                    </CardContent>
                </Card>

                <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-xl flex flex-col shrink-0 lg:h-fit">
                    <CardHeader>
                        <CardTitle className="text-slate-100"><Download className="w-5 h-5 inline-block mr-2 text-emerald-400" /> Export</CardTitle>
                        <CardDescription className="text-slate-400">Download edited text.</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4 flex-1">
                        <Button
                            className="w-full bg-slate-800 hover:bg-slate-700 text-white justify-start"
                            onClick={() => handleExport('json')}
                            disabled={exporting || !editedText}
                        >
                            <FileJson className="w-4 h-4 mr-3 text-blue-400" /> Export JSON
                        </Button>
                        <Button
                            className="w-full bg-slate-800 hover:bg-slate-700 text-white justify-start"
                            onClick={() => handleExport('csv')}
                            disabled={exporting || !editedText}
                        >
                            <FileText className="w-4 h-4 mr-3 text-emerald-400" /> Export CSV
                        </Button>
                        <Button
                            className="w-full bg-slate-800 hover:bg-slate-700 text-white justify-start"
                            onClick={() => handleExport('xml')}
                            disabled={exporting || !editedText}
                        >
                            <FileCode2 className="w-4 h-4 mr-3 text-purple-400" /> Export XML
                        </Button>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
