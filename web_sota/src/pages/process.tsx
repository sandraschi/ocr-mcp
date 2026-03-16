import { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Cpu, RefreshCw, Play, CheckCircle2, AlertCircle, FileText, ChevronDown, ChevronUp } from "lucide-react";

interface Pipeline {
    id: string;
    name: string;
    description: string;
    steps: string[];
}

interface BackendInfo {
    name: string;
    description?: string;
    available: boolean;
}

interface JobResult {
    pipeline_id?: string;
    steps_executed?: string[];
    results?: Record<string, any>;
    text?: string;
    quality_score?: number;
    backend_used?: string;
    error?: string;
}

interface PipelineCardProps {
    pipeline: Pipeline;
    backends: BackendInfo[];
}

function PipelineCard({ pipeline, backends }: PipelineCardProps) {
    const [file, setFile] = useState<File | null>(null);
    const [backend, setBackend] = useState('auto');
    const [loading, setLoading] = useState(false);
    const [jobId, setJobId] = useState<string | null>(null);
    const [jobStatus, setJobStatus] = useState<string | null>(null);
    const [result, setResult] = useState<JobResult | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [showResult, setShowResult] = useState(false);
    const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
    const fileRef = useRef<HTMLInputElement>(null);

    const stopPolling = () => {
        if (pollRef.current) {
            clearInterval(pollRef.current);
            pollRef.current = null;
        }
    };

    const pollJob = (id: string) => {
        pollRef.current = setInterval(async () => {
            try {
                const res = await fetch(`/api/job/${id}`);
                if (!res.ok) { stopPolling(); return; }
                const data = await res.json();
                setJobStatus(data.status);
                if (data.status === 'completed') {
                    stopPolling();
                    setLoading(false);
                    setResult(data.result);
                    setShowResult(true);
                } else if (data.status === 'failed') {
                    stopPolling();
                    setLoading(false);
                    setError(data.error || 'Job failed');
                }
            } catch {
                stopPolling();
                setLoading(false);
                setError('Failed to poll job status');
            }
        }, 1500);
    };

    const handleExecute = async () => {
        if (!file) return;
        setLoading(true);
        setError(null);
        setResult(null);
        setJobStatus('starting');
        setJobId(null);
        setShowResult(false);

        const formData = new FormData();
        formData.append('pipeline_id', pipeline.id);
        formData.append('file', file);
        formData.append('backend', backend);

        try {
            const res = await fetch('/api/pipelines/execute', { method: 'POST', body: formData });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            setJobId(data.job_id);
            setJobStatus('processing');
            pollJob(data.job_id);
        } catch (err: unknown) {
            setLoading(false);
            setError(err instanceof Error ? err.message : 'Request failed');
        }
    };

    const stepLabel: Record<string, string> = {
        deskew_image: 'Deskew',
        enhance_image: 'Enhance',
        process_document: 'OCR',
        assess_ocr_quality: 'Quality Check',
        convert_image_format: 'Convert Format',
    };

    return (
        <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-xl flex flex-col">
            <CardHeader>
                <CardTitle className="text-slate-200 text-lg">{pipeline.name}</CardTitle>
                <CardDescription className="text-slate-400 text-sm">{pipeline.description}</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-4 flex-1">
                {/* Steps pills */}
                <div className="flex flex-wrap gap-1.5">
                    {pipeline.steps.map((step, i) => (
                        <span key={i} className="text-xs px-2 py-1 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
                            {stepLabel[step] || step}
                        </span>
                    ))}
                </div>

                {/* File picker */}
                <div>
                    <input
                        ref={fileRef}
                        type="file"
                        accept="image/*,.pdf"
                        className="hidden"
                        onChange={e => { setFile(e.target.files?.[0] || null); setResult(null); setError(null); }}
                        title="Upload file for OCR"
                    />
                    <button
                        onClick={() => fileRef.current?.click()}
                        className="w-full text-left text-sm px-3 py-2 rounded-md border border-slate-700 bg-slate-950 text-slate-300 hover:border-slate-500 transition-colors truncate"
                    >
                        {file ? file.name : 'Choose file…'}
                    </button>
                </div>

                {/* Backend selector */}
                <div>
                    <label className="text-xs font-medium text-slate-500 mb-1 block">OCR Backend</label>
                    <select
                        value={backend}
                        onChange={e => setBackend(e.target.value)}
                        className="w-full rounded-md border-0 py-2 pl-3 pr-8 bg-slate-950 text-slate-100 ring-1 ring-inset ring-slate-800 focus:ring-2 focus:ring-purple-600 text-sm"
                        title="Select OCR Backend"
                    >
                        <option value="auto">Auto (best available)</option>
                        {backends.filter(b => b.available).map(b => (
                            <option key={b.name} value={b.name}>{b.name}</option>
                        ))}
                    </select>
                </div>

                {/* Execute button */}
                <Button
                    onClick={handleExecute}
                    disabled={!file || loading}
                    className="bg-purple-600 hover:bg-purple-700 text-white w-full"
                >
                    {loading
                        ? <><RefreshCw className="w-4 h-4 mr-2 animate-spin" />{jobStatus || 'Running…'}</>
                        : <><Play className="w-4 h-4 mr-2" />Run Pipeline</>
                    }
                </Button>

                {/* Error */}
                {error && (
                    <div className="flex items-center gap-2 text-red-400 bg-red-400/10 p-3 rounded-md border border-red-400/20 text-sm">
                        <AlertCircle className="w-4 h-4 shrink-0" />
                        {error}
                    </div>
                )}

                {/* Result */}
                {result && (
                    <div className="border border-emerald-500/20 rounded-md bg-emerald-500/5">
                        <button
                            onClick={() => setShowResult(v => !v)}
                            className="w-full flex items-center justify-between px-3 py-2 text-emerald-400 text-sm font-medium"
                        >
                            <span className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4" />Done {jobId && `· ${jobId.slice(-8)}`}</span>
                            {showResult ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                        </button>
                        {showResult && (
                            <div className="px-3 pb-3 space-y-2">
                                {result.text && (
                                    <textarea
                                        readOnly
                                        value={result.text}
                                        rows={6}
                                        className="w-full text-xs bg-slate-950 text-slate-300 rounded p-2 border border-slate-700 resize-y font-mono"
                                        title="OCR Result"
                                        placeholder="No text extracted"
                                    />
                                )}
                                {result.results && Object.entries(result.results).map(([step, stepResult]: [string, any]) => (
                                    <div key={step} className="text-xs text-slate-400">
                                        <span className="text-slate-500">{stepLabel[step] || step}: </span>
                                        {stepResult?.text
                                            ? <span className="text-slate-300">{String(stepResult.text).slice(0, 120)}{stepResult.text.length > 120 ? '…' : ''}</span>
                                            : <span>{stepResult?.status || stepResult?.reason || JSON.stringify(stepResult).slice(0, 80)}</span>
                                        }
                                    </div>
                                ))}
                                {result.quality_score !== undefined && (
                                    <p className="text-xs text-slate-500">Quality: {(result.quality_score * 100).toFixed(0)}%</p>
                                )}
                            </div>
                        )}
                    </div>
                )}
            </CardContent>
        </Card>
    );
}

export function Process() {
    const [file, setFile] = useState<File | null>(null);
    const [loading, setLoading] = useState(false);
    const [status, setStatus] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [quality, setQuality] = useState("0.8");
    const [pipelines, setPipelines] = useState<Pipeline[]>([]);
    const [backends, setBackends] = useState<BackendInfo[]>([]);

    useEffect(() => {
        fetch('/api/pipelines').then(r => r.json()).then(d => setPipelines(d.pipelines || [])).catch(console.error);
        fetch('/api/backends').then(r => r.json()).then(d => setBackends(d.backends || [])).catch(console.error);
    }, []);

    const handleOptimize = async () => {
        if (!file) return;
        setLoading(true);
        setStatus(null);
        setError(null);

        const formData = new FormData();
        formData.append('file', file);
        formData.append('target_quality', quality);
        formData.append('max_attempts', '3');

        try {
            const response = await fetch('/api/optimize', { method: 'POST', body: formData });
            if (!response.ok) throw new Error('Optimization request failed');
            const data = await response.json();
            setStatus(`Optimization job started — ID: ${data.job_id}`);
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : 'Unknown error');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-8 max-w-5xl">
            <h1 className="text-3xl font-bold tracking-tight text-slate-100">Action Pipelines</h1>

            {/* Pipeline cards */}
            {pipelines.length > 0 && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {pipelines.map(pipe => (
                        <PipelineCard key={pipe.id} pipeline={pipe} backends={backends} />
                    ))}
                </div>
            )}

            {/* Quality Optimizer (separate utility) */}
            <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-xl">
                <CardHeader>
                    <CardTitle className="text-slate-100 flex items-center gap-2">
                        <Cpu className="w-5 h-5 text-purple-400" />
                        Quality Optimizer
                    </CardTitle>
                    <CardDescription className="text-slate-400">
                        Automatically tries backends until hitting a target quality score.
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="flex items-center gap-4">
                        <input
                            type="file"
                            onChange={e => { setFile(e.target.files?.[0] || null); setStatus(null); setError(null); }}
                            className="block text-sm text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-purple-500/10 file:text-purple-400 hover:file:bg-purple-500/20"
                            accept="image/*,.pdf"
                            title="Choose file for optimization"
                            placeholder="No file chosen"
                        />
                    </div>
                    <div className="max-w-xs space-y-1">
                        <label className="text-sm font-medium text-slate-300">Target Quality (0.0–1.0)</label>
                        <input
                            type="number" step="0.1" min="0.1" max="1.0"
                            className="block w-full rounded-md border-0 py-2 px-3 bg-slate-950 text-slate-100 ring-1 ring-inset ring-slate-800 focus:ring-2 focus:ring-purple-600 text-sm"
                            value={quality}
                            onChange={e => setQuality(e.target.value)}
                            title="Target Quality Score"
                            placeholder="0.8"
                        />
                    </div>

                    {error && (
                        <div className="flex items-center gap-2 text-red-400 bg-red-400/10 p-3 rounded-md border border-red-400/20 text-sm">
                            <AlertCircle className="w-4 h-4" />{error}
                        </div>
                    )}
                    {status && (
                        <div className="flex items-center gap-2 text-emerald-400 bg-emerald-400/10 p-3 rounded-md border border-emerald-400/20 text-sm">
                            <CheckCircle2 className="w-4 h-4" />{status}
                        </div>
                    )}

                    <Button onClick={handleOptimize} disabled={!file || loading} className="bg-purple-600 hover:bg-purple-700 text-white">
                        {loading ? <><RefreshCw className="w-4 h-4 mr-2 animate-spin" />Processing…</> : <><FileText className="w-4 h-4 mr-2" />Start Optimizer</>}
                    </Button>
                </CardContent>
            </Card>
        </div>
    );
}
