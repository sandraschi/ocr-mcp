import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Download, RefreshCw, FileText, FileJson, FileCode2 } from "lucide-react";

export function Editor() {
    const [searchParams] = useSearchParams();
    const jobIdParam = searchParams.get('job_id') || '';
    const [jobId, setJobId] = useState(jobIdParam);
    const [status, setStatus] = useState<any>(null);
    const [loading, setLoading] = useState(false);
    const [editedText, setEditedText] = useState("");
    const [exporting, setExporting] = useState(false);

    useEffect(() => {
        if (jobIdParam) {
            checkJob(jobIdParam);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [jobIdParam]);

    const checkJob = async (id: string) => {
        if (!id) return;
        setLoading(true);
        try {
            const res = await fetch(`/api/job/${id}`);
            if (res.ok) {
                const data = await res.json();
                setStatus(data);
                if (data.status === 'completed' && data.result?.text) {
                    setEditedText(data.result.text);
                }
            } else {
                setStatus({ error: "Job not found or API error" });
            }
        } catch (err: unknown) {
            setStatus({ error: err instanceof Error ? err.message : "Network error" });
        } finally {
            setLoading(false);
        }
    };

    const handleExport = async (type: string) => {
        setExporting(true);
        try {
            const payload = {
                export_type: type,
                content: { text: editedText, original_job: jobId },
                filename: `ocr_export_${jobId || 'new'}`
            };

            const res = await fetch(`/api/export`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (res.ok) {
                const data = await res.json();

                // Create a blob and download it
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

    return (
        <div className="space-y-6 flex flex-col h-[calc(100vh-8rem)]">
            <h1 className="text-3xl font-bold tracking-tight text-slate-100 shrink-0">Output & Editor</h1>

            <div className="flex gap-4 shrink-0">
                <input
                    type="text"
                    placeholder="Enter Job ID to load..."
                    className="flex-1 rounded-md border-0 py-2 px-3 bg-slate-950 text-slate-100 ring-1 ring-inset ring-slate-800 focus:ring-2 focus:ring-blue-600 sm:text-sm sm:leading-6"
                    value={jobId}
                    onChange={(e) => setJobId(e.target.value)}
                />
                <Button onClick={() => checkJob(jobId)} disabled={loading} className="bg-slate-800 hover:bg-slate-700 text-white">
                    {loading ? <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> : <RefreshCw className="w-4 h-4 mr-2" />}
                    Load Job
                </Button>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 flex-1 min-h-0">
                <Card className="lg:col-span-3 bg-slate-900/50 border-slate-800 backdrop-blur-xl flex flex-col min-h-0">
                    <CardHeader className="shrink-0">
                        <CardTitle className="text-slate-100 flex items-center gap-2"><FileText className="w-5 h-5 text-blue-400" /> Text Editor</CardTitle>
                        <CardDescription className="text-slate-400">Review and edit the extracted OCR text before exporting.</CardDescription>
                    </CardHeader>
                    <CardContent className="flex flex-col flex-1 min-h-0 pb-6">
                        {status && status.status === 'processing' ? (
                            <div className="flex flex-col items-center justify-center h-full text-slate-400">
                                <RefreshCw className="w-8 h-8 animate-spin mb-4 text-blue-500" />
                                <p>Job is still processing...</p>
                            </div>
                        ) : status && status.error ? (
                            <div className="p-4 bg-red-500/10 border border-red-500/20 text-red-400 rounded-md">
                                {status.error}
                            </div>
                        ) : (
                            <textarea
                                className="w-full flex-1 min-h-0 rounded-md border-0 py-3 px-4 bg-slate-950 text-slate-100 ring-1 ring-inset ring-slate-800 focus:ring-2 focus:ring-blue-600 sm:text-sm font-mono resize-none overflow-auto"
                                value={editedText}
                                onChange={(e) => setEditedText(e.target.value)}
                                placeholder="OCR output will appear here. Load a job ID to begin."
                            />
                        )}
                    </CardContent>
                </Card>

                <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-xl flex flex-col shrink-0 lg:h-fit">
                    <CardHeader>
                        <CardTitle className="text-slate-100"><Download className="w-5 h-5 inline-block mr-2 text-emerald-400" /> Export</CardTitle>
                        <CardDescription className="text-slate-400">Download formatted results.</CardDescription>
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
