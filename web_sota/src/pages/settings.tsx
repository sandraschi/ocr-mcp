import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Settings as SettingsIcon, Database, ScanLine, Cpu, CheckCircle2, Key, Loader2, FlaskConical } from "lucide-react";

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

interface MistralSettingsResponse {
    key_configured: boolean;
    base_url: string;
    key_hint: string | null;
}

const DEFAULT_BACKEND_KEY = 'ocr_default_backend';

export function Settings() {
    const [backends, setBackends] = useState<BackendInfo[]>([]);
    const [scanners, setScanners] = useState<ScannerInfo[]>([]);
    const [defaultBackend, setDefaultBackend] = useState<string>(() => {
        return localStorage.getItem(DEFAULT_BACKEND_KEY) || 'auto';
    });
    const [saved, setSaved] = useState(false);

    const [mistralBaseUrl, setMistralBaseUrl] = useState('https://api.mistral.ai/v1');
    const [mistralKeyInput, setMistralKeyInput] = useState('');
    const [mistralHint, setMistralHint] = useState<string | null>(null);
    const [mistralConfigured, setMistralConfigured] = useState(false);
    const [mistralSaved, setMistralSaved] = useState(false);
    const [mistralError, setMistralError] = useState<string | null>(null);
    const [mistralTesting, setMistralTesting] = useState(false);
    const [mistralTestOk, setMistralTestOk] = useState<boolean | null>(null);
    const [mistralTestMessage, setMistralTestMessage] = useState<string | null>(null);

    const loadBackends = () => {
        fetch('/api/backends').then(r => r.json()).then(d => setBackends(d.backends || [])).catch(() => { });
    };

    const loadMistral = () => {
        fetch('/api/settings/mistral')
            .then(r => r.json())
            .then((d: MistralSettingsResponse) => {
                setMistralConfigured(d.key_configured);
                setMistralHint(d.key_hint);
                if (d.base_url) setMistralBaseUrl(d.base_url);
            })
            .catch(() => { });
    };

    useEffect(() => {
        loadBackends();
        fetch('/api/scanners').then(r => r.json()).then(d => setScanners(d.scanners || [])).catch(() => { });
        loadMistral();
    }, []);

    const saveDefaultBackend = () => {
        localStorage.setItem(DEFAULT_BACKEND_KEY, defaultBackend);
        setSaved(true);
        setTimeout(() => setSaved(false), 2000);
    };

    const saveMistral = async () => {
        setMistralError(null);
        const trimmedKey = mistralKeyInput.trim();
        const payload: Record<string, string> = {
            base_url: mistralBaseUrl.trim() || 'https://api.mistral.ai/v1',
        };
        if (trimmedKey) payload.api_key = trimmedKey;
        try {
            const r = await fetch('/api/settings/mistral', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
            const data = await r.json().catch(() => ({}));
            if (!r.ok) {
                setMistralError(typeof data.detail === 'string' ? data.detail : 'Save failed');
                return;
            }
            setMistralKeyInput('');
            setMistralConfigured(Boolean(data.key_configured));
            setMistralHint(data.key_hint ?? null);
            if (data.base_url) setMistralBaseUrl(data.base_url);
            loadBackends();
            setMistralSaved(true);
            setTimeout(() => setMistralSaved(false), 2000);
        } catch {
            setMistralError('Network error');
        }
    };

    const clearMistralTest = () => {
        setMistralTestOk(null);
        setMistralTestMessage(null);
    };

    const testMistral = async () => {
        setMistralError(null);
        clearMistralTest();
        setMistralTesting(true);
        const payload: Record<string, string> = {};
        const k = mistralKeyInput.trim();
        if (k) payload.api_key = k;
        const bu = mistralBaseUrl.trim();
        if (bu) payload.base_url = bu;
        try {
            const r = await fetch('/api/settings/mistral/test', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
            const data = await r.json().catch(() => ({}));
            if (r.status === 400) {
                const d = data.detail;
                const msg = typeof d === 'string' ? d : Array.isArray(d) ? String(d[0]) : 'Bad request';
                setMistralTestOk(false);
                setMistralTestMessage(msg);
                return;
            }
            if (!r.ok) {
                const d = data.detail;
                setMistralTestOk(false);
                setMistralTestMessage(typeof d === 'string' ? d : `HTTP ${r.status}`);
                return;
            }
            setMistralTestOk(data.valid === true);
            setMistralTestMessage(
                typeof data.message === 'string' ? data.message : data.valid ? 'OK' : 'Check failed',
            );
        } catch {
            setMistralTestOk(false);
            setMistralTestMessage('Network error');
        } finally {
            setMistralTesting(false);
        }
    };

    const clearMistralKey = async () => {
        setMistralError(null);
        try {
            const r = await fetch('/api/settings/mistral', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ api_key: '' }),
            });
            const data = await r.json().catch(() => ({}));
            if (!r.ok) {
                setMistralError(typeof data.detail === 'string' ? data.detail : 'Remove failed');
                return;
            }
            setMistralKeyInput('');
            setMistralConfigured(false);
            setMistralHint(null);
            loadBackends();
        } catch {
            setMistralError('Network error');
        }
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
                {/* Mistral OCR API */}
                <Card className="border-slate-800 bg-slate-950/50">
                    <CardHeader>
                        <CardTitle className="text-white flex items-center gap-2">
                            <Key className="w-5 h-5 text-amber-400" /> Mistral OCR API
                        </CardTitle>
                        <CardDescription className="text-slate-400">
                            Required for the <span className="text-slate-300 font-mono">mistral-ocr</span> backend.
                            Key is stored in the backend process only (not in browser localStorage).
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="space-y-2">
                            <label htmlFor="mistral-key" className="text-sm font-medium text-slate-300">
                                API key
                            </label>
                            <Input
                                id="mistral-key"
                                type="password"
                                autoComplete="off"
                                placeholder={mistralConfigured ? '•••••••• (enter new key to replace)' : 'sk-...'}
                                value={mistralKeyInput}
                                onChange={(e) => setMistralKeyInput(e.target.value)}
                                className="bg-slate-900 border-slate-700 text-slate-100"
                            />
                            {mistralConfigured && mistralHint && (
                                <p className="text-xs text-slate-500">
                                    Current key ends with <span className="font-mono text-slate-400">{mistralHint}</span>
                                </p>
                            )}
                        </div>
                        <div className="space-y-2">
                            <label htmlFor="mistral-base" className="text-sm font-medium text-slate-300">
                                Base URL
                            </label>
                            <Input
                                id="mistral-base"
                                type="url"
                                value={mistralBaseUrl}
                                onChange={(e) => {
                                    setMistralBaseUrl(e.target.value);
                                    clearMistralTest();
                                }}
                                className="bg-slate-900 border-slate-700 text-slate-100 font-mono text-sm"
                            />
                        </div>
                        {mistralError && (
                            <p className="text-sm text-red-400">{mistralError}</p>
                        )}
                        {mistralTestMessage != null && (
                            <p
                                className={`text-sm ${
                                    mistralTestOk === true
                                        ? 'text-emerald-400'
                                        : 'text-red-400'
                                }`}
                                role="status"
                            >
                                {mistralTestOk === true ? '✓ ' : ''}{mistralTestMessage}
                            </p>
                        )}
                        <div className="flex flex-wrap items-center gap-2">
                            <Button
                                type="button"
                                onClick={() => void saveMistral()}
                                className="bg-amber-600 hover:bg-amber-700 text-white"
                            >
                                {mistralSaved
                                    ? <><CheckCircle2 className="w-4 h-4 mr-2" />Saved</>
                                    : 'Save Mistral settings'}
                            </Button>
                            <Button
                                type="button"
                                variant="secondary"
                                className="bg-slate-800 text-slate-100 hover:bg-slate-700 border border-slate-600"
                                onClick={() => void testMistral()}
                                disabled={
                                    mistralTesting
                                    || (!mistralKeyInput.trim() && !mistralConfigured)
                                }
                                title={
                                    !mistralKeyInput.trim() && !mistralConfigured
                                        ? 'Enter an API key or save one first'
                                        : 'GET /models with current or pasted key'
                                }
                            >
                                {mistralTesting ? (
                                    <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Testing…</>
                                ) : (
                                    <><FlaskConical className="w-4 h-4 mr-2" />Test API key</>
                                )}
                            </Button>
                            <Button
                                type="button"
                                variant="outline"
                                className="border-slate-600 text-slate-300"
                                onClick={() => void clearMistralKey()}
                                disabled={!mistralConfigured}
                            >
                                Remove API key
                            </Button>
                        </div>
                    </CardContent>
                </Card>

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
