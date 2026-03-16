import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Settings as SettingsIcon, Database, ScanLine, Cpu, CheckCircle2 } from "lucide-react";

interface BackendInfo {
    name: string;
    description?: string;
    available: boolean;
}

interface ScannerInfo {
    device_id: string;
    name: string;
    type?: string;
    manufacturer?: string;
    max_dpi?: number;
}

const DEFAULT_BACKEND_KEY = 'ocr_default_backend';

export function Settings() {
    const [backends, setBackends] = useState<BackendInfo[]>([]);
    const [scanners, setScanners] = useState<ScannerInfo[]>([]);
    const [defaultBackend, setDefaultBackend] = useState<string>(() => {
        return localStorage.getItem(DEFAULT_BACKEND_KEY) || 'auto';
    });
    const [saved, setSaved] = useState(false);

    useEffect(() => {
        fetch('/api/backends').then(r => r.json()).then(d => setBackends(d.backends || [])).catch(() => { });
        fetch('/api/scanners').then(r => r.json()).then(d => setScanners(d.scanners || [])).catch(() => { });
    }, []);

    const saveDefaultBackend = () => {
        localStorage.setItem(DEFAULT_BACKEND_KEY, defaultBackend);
        setSaved(true);
        setTimeout(() => setSaved(false), 2000);
    };

    return (
        <div className="space-y-6 max-w-4xl pb-12">
            <div>
                <h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
                    <SettingsIcon className="w-6 h-6 text-slate-400" />
                    System Settings
                </h2>
                <p className="text-slate-400">Manage connections and OCR preferences</p>
            </div>

            <div className="grid gap-6">
                {/* Default OCR Backend selector */}
                <Card className="border-slate-800 bg-slate-950/50">
                    <CardHeader>
                        <CardTitle className="text-white flex items-center gap-2">
                            <Cpu className="w-5 h-5 text-purple-400" /> Default OCR Backend
                        </CardTitle>
                        <CardDescription className="text-slate-400">
                            Which model to use for scan OCR and pipeline jobs when "Auto" is not selected explicitly.
                            Stored locally in your browser.
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="flex items-center gap-4">
                            <select
                                value={defaultBackend}
                                onChange={e => { setDefaultBackend(e.target.value); setSaved(false); }}
                                className="rounded-md border-0 py-2 pl-3 pr-10 bg-slate-900 text-slate-100 ring-1 ring-inset ring-slate-700 focus:ring-2 focus:ring-purple-600 text-sm min-w-56"
                                title="Default OCR Backend"
                            >
                                <option value="auto">Auto (best available)</option>
                                {backends.filter(b => b.available).map(b => (
                                    <option key={b.name} value={b.name}>{b.name}</option>
                                ))}
                            </select>
                            <Button onClick={saveDefaultBackend} className="bg-purple-600 hover:bg-purple-700 text-white">
                                {saved
                                    ? <><CheckCircle2 className="w-4 h-4 mr-2" />Saved</>
                                    : 'Save Default'
                                }
                            </Button>
                        </div>
                        <p className="text-xs text-slate-500">
                            Current default: <span className="text-slate-300 font-mono">{defaultBackend}</span>
                        </p>
                    </CardContent>
                </Card>

                {/* OCR Backends list */}
                <Card className="border-slate-800 bg-slate-950/50">
                    <CardHeader>
                        <CardTitle className="text-white flex items-center gap-2">
                            <Database className="w-5 h-5 text-blue-400" /> Available OCR Backends
                        </CardTitle>
                        <CardDescription className="text-slate-400">Loaded OCR engines and their status</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        {backends.length === 0 ? (
                            <div className="text-sm text-slate-500">No external backends loaded (using defaults).</div>
                        ) : (
                            <div className="space-y-2">
                                {backends.map(b => (
                                    <div key={b.name} className="flex items-center justify-between p-3 rounded-md border border-slate-800 bg-slate-900">
                                        <div>
                                            <p className="font-medium text-slate-200">{b.name}</p>
                                            <p className="text-xs text-slate-500">{b.description || 'OCR Engine'}</p>
                                        </div>
                                        <div className={`text-xs px-2 py-1 rounded border ${b.available
                                            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                                            : 'bg-red-500/10 text-red-400 border-red-500/20'}`}>
                                            {b.available ? 'Available' : 'Offline'}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </CardContent>
                </Card>

                {/* Scanners */}
                <Card className="border-slate-800 bg-slate-950/50">
                    <CardHeader>
                        <CardTitle className="text-white flex items-center gap-2">
                            <ScanLine className="w-5 h-5 text-purple-400" /> Scanners & Hardware
                        </CardTitle>
                        <CardDescription className="text-slate-400">Connected physical devices</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        {scanners.length === 0 ? (
                            <div className="text-sm text-slate-500">No hardware scanners detected.</div>
                        ) : (
                            <div className="space-y-2">
                                {scanners.map(s => (
                                    <div key={s.device_id} className="flex items-start justify-between p-3 rounded-md border border-slate-800 bg-slate-900">
                                        <div className="space-y-0.5">
                                            <p className="font-medium text-slate-200">{s.name}</p>
                                            <p className="text-xs text-slate-500">{s.manufacturer || ''}{s.type ? ` · ${s.type}` : ''}{s.max_dpi ? ` · max ${s.max_dpi} DPI` : ''}</p>
                                            <p className="text-xs text-slate-600 font-mono">{s.device_id}</p>
                                        </div>
                                        <div className="text-xs px-2 py-1 rounded bg-blue-500/10 text-blue-400 border-blue-500/20 border shrink-0 mt-0.5">
                                            Ready
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
