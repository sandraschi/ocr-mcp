import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Upload, CheckCircle2, AlertCircle, RefreshCw, FileText, Activity } from "lucide-react";
import { useScanStore } from '@/store';

export function Import() {
    const setLastOcrJobId = useScanStore((s) => s.setLastOcrJobId);
    const lastOcrJobId = useScanStore((s) => s.lastOcrJobId);
    const [file, setFile] = useState<File | null>(null);
    const [loading, setLoading] = useState(false);
    const [status, setStatus] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setFile(e.target.files[0]);
            setStatus(null);
            setError(null);
        }
    };

    const handleUpload = async () => {
        if (!file) return;
        setLoading(true);
        setStatus(null);
        setError(null);

        const formData = new FormData();
        formData.append('file', file);
        formData.append('ocr_mode', 'auto');
        formData.append('backend', 'auto');

        try {
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) throw new Error('Upload failed');

            const data = await response.json();
            if (data.job_id) setLastOcrJobId(data.job_id);
            setStatus('Upload queued — open Editor or Status to follow progress.');
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : 'Unknown error');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-6">
            <h1 className="text-3xl font-bold tracking-tight text-slate-100">Import Document</h1>
            <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-xl">
                <CardHeader>
                    <CardTitle className="text-slate-100">Upload File for OCR</CardTitle>
                    <CardDescription className="text-slate-400">Select an image or PDF to process.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="flex items-center space-x-4">
                        <input
                            type="file"
                            onChange={handleFileChange}
                            className="block w-full text-sm text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-500/10 file:text-blue-500 hover:file:bg-blue-500/20"
                            accept="image/*,.pdf"
                            title="Upload File"
                        />
                    </div>

                    {error && (
                        <div className="flex items-center gap-2 text-red-400 bg-red-400/10 p-3 rounded-md border border-red-400/20">
                            <AlertCircle className="w-4 h-4" />
                            <span className="text-sm">{error}</span>
                        </div>
                    )}

                    {status && (
                        <div className="flex flex-wrap items-center gap-2 text-emerald-400 bg-emerald-400/10 p-3 rounded-md border border-emerald-400/20">
                            <CheckCircle2 className="w-4 h-4 shrink-0" />
                            <span className="text-sm">{status}</span>
                            {lastOcrJobId && (
                                <>
                                    <Button type="button" variant="outline" size="sm" className="border-emerald-500/50 text-emerald-300" onClick={() => window.location.assign('/editor')}>
                                        <FileText className="w-4 h-4 mr-1" /> View text
                                    </Button>
                                    <Button type="button" variant="outline" size="sm" className="border-emerald-500/50 text-emerald-300" onClick={() => window.location.assign('/status')}>
                                        <Activity className="w-4 h-4 mr-1" /> Activity
                                    </Button>
                                </>
                            )}
                        </div>
                    )}

                    <Button
                        onClick={handleUpload}
                        disabled={!file || loading}
                        className="bg-blue-600 hover:bg-blue-700 text-white"
                    >
                        {loading ? <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> : <Upload className="w-4 h-4 mr-2" />}
                        {loading ? 'Uploading...' : 'Upload & Process'}
                    </Button>
                </CardContent>
            </Card>
        </div>
    );
}
