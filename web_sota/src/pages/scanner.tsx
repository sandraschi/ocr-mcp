import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { CheckCircle2, AlertCircle, RefreshCw, Scan, ScanLine, Cpu, FileText } from "lucide-react";
import { ScanViewer } from '@/components/ui/ScanViewer';
import { useScanStore } from '@/store';

interface ScannerInfo {
    device_id: string;
    name: string;
    type: string;
}

interface BackendInfo {
    name: string;
    available: boolean;
}

const DEFAULT_BACKEND_KEY = 'ocr_default_backend';

export function Scanner() {
    const [scanners, setScanners] = useState<ScannerInfo[]>([]);
    const [backends, setBackends] = useState<BackendInfo[]>([]);
    const [selectedScanner, setSelectedScanner] = useState<string>("");
    const [selectedBackend, setSelectedBackend] = useState<string>(
        () => localStorage.getItem(DEFAULT_BACKEND_KEY) || 'auto'
    );
    const { lastScan, setLastScan, lastOcrJobId, setLastOcrJobId } = useScanStore();
    const [loading, setLoading] = useState(false);
    const [fetching, setFetching] = useState(true);
    const [status, setStatus] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [isProcessingSelection, setIsProcessingSelection] = useState(false);

    // Derived values from store
    const imageUrl = lastScan.imageUrl;
    const selection = lastScan.selection;
    const lastScanFilename = lastScan.filename;

    const setImageUrl = useCallback((url: string | null) => setLastScan({ imageUrl: url }), [setLastScan]);
    const setSelection = useCallback((sel: { x: number; y: number; width: number; height: number; imgWidth: number; imgHeight: number } | null) => setLastScan({ selection: sel }), [setLastScan]);
    const setLastScanFilename = useCallback((name: string | null) => setLastScan({ filename: name }), [setLastScan]);

    const fetchScanners = async () => {
        setFetching(true);
        setError(null);
        try {
            const res = await fetch('/api/scanners');
            const data = await res.json().catch(() => ({}));
            setScanners(data.scanners || []);
            if (data.error) {
                setError(data.error);
            }
            if (data.default_scanner) {
                setSelectedScanner(data.default_scanner);
            } else if (data.scanners && data.scanners.length > 0) {
                setSelectedScanner(data.scanners[0].device_id);
            }
            if (!res.ok) {
                setError(data.error || "Failed to load scanners");
            }
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : "Failed to fetch scanners");
        } finally {
            setFetching(false);
        }
    };

    useEffect(() => {
        fetchScanners();
        fetch('/api/backends').then(r => r.json()).then(d => setBackends(d.backends || [])).catch(() => { });
    }, []);

    const [ocrLoading, setOcrLoading] = useState(false);

    const handleScan = async () => {
        if (!selectedScanner) return;
        setLoading(true);
        setStatus(null);
        setError(null);
        setImageUrl(null);
        setLastScanFilename(null);

        const formData = new FormData();
        formData.append('device_id', selectedScanner);
        formData.append('dpi', '300');
        formData.append('color_mode', 'Color');
        formData.append('paper_size', 'A4');

        try {
            const response = await fetch('/api/scan', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) throw new Error('Scan failed');

            const data = await response.json();
            if (data.success) {
                setStatus(`Scan successful!`);
                setImageUrl(data.image_path);
                setLastScanFilename(data.image_info.filename);
            } else {
                throw new Error(data.message || 'Scan failed');
            }
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : 'Unknown error');
        } finally {
            setLoading(false);
        }
    };

    const handleOCR = async () => {
        if (!lastScanFilename) return;
        setOcrLoading(true);
        setStatus(null);
        setError(null);

        const formData = new FormData();
        formData.append('filename', lastScanFilename);
        formData.append('ocr_mode', 'text');
        formData.append('backend', selectedBackend);

        try {
            const response = await fetch('/api/ocr_scanned', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) throw new Error('OCR request failed');

            const data = await response.json();
            if (data.job_id) {
                setLastOcrJobId(data.job_id);
                setStatus('OCR running — open View text or Activity when ready.');
            } else {
                throw new Error(data.error || 'Failed to start OCR');
            }
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : 'Unknown error');
        } finally {
            setOcrLoading(false);
        }
    };

    const handleSelectionProcess = async () => {
        if (!selection || !lastScanFilename) return;
        
        setIsProcessingSelection(true);
        setError(null);
        setStatus(null);
        
        try {
            const formData = new FormData();
            formData.append('filename', lastScanFilename);
            formData.append('x', selection.x.toString());
            formData.append('y', selection.y.toString());
            formData.append('width', selection.width.toString());
            formData.append('height', selection.height.toString());
            formData.append('backend', selectedBackend);
            
            const response = await fetch('/api/ocr_selection', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to process selection');
            }

            const data = await response.json();
            if (data.job_id) setLastOcrJobId(data.job_id);
            setStatus('Selection sent for OCR — open View text or Activity when ready.');
            setSelection(null);
            
        } catch (err: unknown) {
            console.error("Failed to process selection:", err);
            setError(`Failed to process selection: ${err instanceof Error ? err.message : 'Unknown error'}`);
        } finally {
            setIsProcessingSelection(false);
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h1 className="text-3xl font-bold tracking-tight text-slate-100">Scanner Control</h1>
                <Button variant="outline" onClick={fetchScanners} disabled={fetching} className="border-slate-700 text-slate-300 hover:bg-slate-800">
                    <RefreshCw className={`w-4 h-4 mr-2 ${fetching ? 'animate-spin' : ''}`} /> Refresh
                </Button>
            </div>

            <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-xl">
                <CardHeader>
                    <CardTitle className="text-slate-100 flex items-center gap-2"><Scan className="w-5 h-5 text-blue-400" /> Auto-Scan</CardTitle>
                    <CardDescription className="text-slate-400">Trigger a hardware scan via connected devices.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                    {fetching ? (
                        <div className="text-slate-400 text-sm flex items-center"><RefreshCw className="animate-spin w-4 h-4 mr-2" /> Loading scanners...</div>
                    ) : scanners.length === 0 ? (
                        <div className="text-slate-400 text-sm p-4 bg-slate-900 rounded-md border border-slate-800">No scanners found nearby or manager not initialized.</div>
                    ) : (
                        <div className="space-y-4">
                            <div className="space-y-2">
                                <label className="text-sm font-medium text-slate-300">Select Scanner</label>
                                <select
                                    className="block w-full rounded-md border-0 py-2 pl-3 pr-10 bg-slate-950 text-slate-100 ring-1 ring-inset ring-slate-800 focus:ring-2 focus:ring-blue-600 sm:text-sm sm:leading-6"
                                    value={selectedScanner}
                                    onChange={(e) => setSelectedScanner(e.target.value)}
                                    title="Select Scanner"
                                >
                                    {scanners.map((s) => (
                                        <option key={s.device_id} value={s.device_id}>{s.name} ({s.type})</option>
                                    ))}
                                </select>
                            </div>

                            <div className="space-y-2">
                                <label className="text-sm font-medium text-slate-300">OCR Backend (for post-scan OCR)</label>
                                <select
                                    className="block w-full rounded-md border-0 py-2 pl-3 pr-10 bg-slate-950 text-slate-100 ring-1 ring-inset ring-slate-800 focus:ring-2 focus:ring-purple-600 sm:text-sm sm:leading-6"
                                    value={selectedBackend}
                                    onChange={(e) => setSelectedBackend(e.target.value)}
                                    title="Select OCR Backend"
                                >
                                    <option value="auto">Auto (best available)</option>
                                    {backends.filter(b => b.available).map(b => (
                                        <option key={b.name} value={b.name}>{b.name}</option>
                                    ))}
                                </select>
                            </div>

                            <Button
                                onClick={handleScan}
                                disabled={!selectedScanner || loading}
                                className="bg-blue-600 hover:bg-blue-700 text-white w-full sm:w-auto"
                            >
                                {loading ? <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> : <ScanLine className="w-4 h-4 mr-2" />}
                                {loading ? 'Scanning...' : 'Trigger Scan'}
                            </Button>
                        </div>
                    )}

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
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        className="ml-2 border-emerald-500/50 text-emerald-300 hover:bg-emerald-500/20"
                                        onClick={() => window.location.assign('/editor')}
                                    >
                                        <FileText className="w-4 h-4 mr-1" />
                                        View text
                                    </Button>
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        className="border-emerald-500/50 text-emerald-300 hover:bg-emerald-500/20"
                                        onClick={() => window.location.assign('/status')}
                                    >
                                        Activity
                                    </Button>
                                </>
                            )}
                        </div>
                    )}

                    {imageUrl && (
                        <div className="mt-6 space-y-4">
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="text-lg font-medium text-slate-100">Scan Preview</h3>
                                {selection && (
                                    <Button 
                                        onClick={handleSelectionProcess}
                                        disabled={isProcessingSelection}
                                        className="gap-2 bg-blue-600 hover:bg-blue-700 text-white"
                                    >
                                        <FileText className="w-4 h-4" />
                                        {isProcessingSelection ? 'Processing...' : 'OCR Selection'}
                                    </Button>
                                )}
                            </div>

                            <p className="text-xs text-slate-500 mb-1">Tip: click &quot;Select Area&quot; above, then drag on the image to select a region for OCR.</p>
                            <div className="h-[600px] border border-slate-700 rounded-md bg-slate-950/50 overflow-hidden">
                                <ScanViewer 
                                    imageUrl={imageUrl} 
                                    onSelectionChange={setSelection}
                                    isProcessing={isProcessingSelection}
                                />
                            </div>

                            <div className="flex justify-end mt-4">
                                <Button
                                    onClick={handleOCR}
                                    disabled={ocrLoading}
                                    className="bg-purple-600 hover:bg-purple-700 text-white"
                                >
                                    {ocrLoading ? <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> : <Cpu className="w-4 h-4 mr-2" />}
                                    OCR Full Scan
                                </Button>
                            </div>
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}
