import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { FileText, AlertCircle, Scan, ArrowLeft, Activity } from "lucide-react";
import { ScanViewer } from '@/components/ui/ScanViewer';
import { useScanStore } from '@/store';

export function ScanViewerPage() {
    const { lastScan, setLastScan, setLastOcrJobId } = useScanStore();
    const navigate = useNavigate();
    const [isProcessingSelection, setIsProcessingSelection] = useState(false);
    const [ocrResult, setOcrResult] = useState<string | null>(null);

    const imageUrl = lastScan.imageUrl;
    const selection = lastScan.selection;

    const setSelection = useCallback((sel: { x: number; y: number; width: number; height: number; imgWidth: number; imgHeight: number } | null) => 
        setLastScan({ selection: sel }), [setLastScan]);

    const handleSelectionProcess = async () => {
        if (!selection || !lastScan.filename) return;
        
        setIsProcessingSelection(true);
        setOcrResult(null);
        
        try {
            const formData = new FormData();
            formData.append('filename', lastScan.filename);
            formData.append('x', selection.x.toString());
            formData.append('y', selection.y.toString());
            formData.append('width', selection.width.toString());
            formData.append('height', selection.height.toString());
            formData.append('backend', 'auto');
            
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
            setOcrResult('OCR job started — latest job is saved. Open Editor or Status (no copy/paste needed).');
            
        } catch (err: unknown) {
            console.error("Failed to process selection:", err);
            setOcrResult(`Error: ${err instanceof Error ? err.message : 'Unknown error'}`);
        } finally {
            setIsProcessingSelection(false);
        }
    };

    if (!imageUrl) {
        return (
            <div className="flex flex-col items-center justify-center h-[70vh] space-y-6 text-center">
                <div className="p-6 bg-slate-900/50 rounded-full border border-slate-800">
                    <Scan className="w-12 h-12 text-slate-500" />
                </div>
                <div className="space-y-2">
                    <h2 className="text-2xl font-bold text-slate-100">No Active Scan</h2>
                    <p className="text-slate-400 max-w-md">
                        You haven't performed any scans in this session. 
                        Go to the Scanner page to start.
                    </p>
                </div>
                <Button onClick={() => navigate('/scanner')} className="bg-blue-600 hover:bg-blue-700">
                    Go to Scanner
                </Button>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div className="flex items-center gap-4">
                    <Button variant="ghost" size="icon" onClick={() => navigate('/scanner')} className="text-slate-400 hover:text-white">
                        <ArrowLeft className="w-5 h-5" />
                    </Button>
                    <div>
                        <h1 className="text-3xl font-bold tracking-tight text-slate-100">Scan Viewer</h1>
                        <p className="text-slate-400">Analyze and process your latest capture.</p>
                    </div>
                </div>
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

            <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
                <Card className="xl:col-span-3 bg-slate-900/50 border-slate-800 overflow-hidden h-[700px]">
                    <CardContent className="p-0 h-full">
                        <ScanViewer 
                            imageUrl={imageUrl} 
                            onSelectionChange={setSelection}
                            isProcessing={isProcessingSelection}
                        />
                    </CardContent>
                </Card>

                <div className="space-y-6">
                    <Card className="bg-slate-900/50 border-slate-800">
                        <CardHeader>
                            <CardTitle className="text-sm font-medium flex items-center gap-2">
                                <FileText className="w-4 h-4 text-blue-400" /> OCR Result
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="bg-slate-950 p-4 rounded-md border border-slate-800 min-h-[200px] text-sm font-mono text-slate-300 whitespace-pre-wrap break-all">
                                {ocrResult || (selection ? "Click 'OCR Selection' to start..." : "Select an area to OCR.")}
                            </div>
                            {ocrResult && (
                                <div className="flex flex-col gap-2">
                                    <Button variant="outline" size="sm" className="w-full border-slate-700 text-slate-300 hover:bg-slate-800" onClick={() => navigate('/editor')}>
                                        <FileText className="w-4 h-4 mr-2" /> View text
                                    </Button>
                                    <Button variant="outline" size="sm" className="w-full border-slate-700 text-slate-300 hover:bg-slate-800" onClick={() => navigate('/status')}>
                                        <Activity className="w-4 h-4 mr-2" /> Activity
                                    </Button>
                                </div>
                            )}
                        </CardContent>
                    </Card>

                    <Card className="bg-slate-900/50 border-slate-800">
                        <CardHeader>
                            <CardTitle className="text-sm font-medium flex items-center gap-2">
                                <AlertCircle className="w-4 h-4 text-purple-400" /> capture info
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-3 text-sm">
                            <div className="flex justify-between">
                                <span className="text-slate-400">Filename:</span>
                                <span className="text-slate-200 truncate ml-2 max-w-[150px]" title={lastScan.filename || ''}>{lastScan.filename}</span>
                            </div>
                            {/* Additional metadata could be added here */}
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    );
}
