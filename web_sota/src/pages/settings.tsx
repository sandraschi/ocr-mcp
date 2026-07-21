import {
  CheckCircle2,
  Cpu,
  Database,
  Eye,
  FlaskConical,
  Key,
  Loader2,
  RefreshCw,
  ScanLine,
  Settings as SettingsIcon,
  Wifi,
  WifiOff,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

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

interface LlmProvider {
  id: string;
  label: string;
  base_url: string;
  models: string[];
  needs_key: boolean;
}

interface MistralSettingsResponse {
  key_configured: boolean;
  base_url: string;
  key_hint: string | null;
}

const DEFAULT_BACKEND_KEY = "ocr_default_backend";
const AUTO_SCAN_KEY = "ocr-auto-scan-enabled";

export function Settings() {
  const [backends, setBackends] = useState<BackendInfo[]>([]);
  const [scanners, setScanners] = useState<ScannerInfo[]>([]);
  const [defaultBackend, setDefaultBackend] = useState<string>(() => {
    return localStorage.getItem(DEFAULT_BACKEND_KEY) || "auto";
  });
  const [saved, setSaved] = useState(false);
  const [llmProviders, setLlmProviders] = useState<LlmProvider[]>([]);
  const [, setLlmProviderMap] = useState<Record<string, LlmProvider>>({});
  const [autoScan, setAutoScan] = useState(() => localStorage.getItem(AUTO_SCAN_KEY) === "true");
  const [watcherStatus, setWatcherStatus] = useState<any>(null);

  const [mistralBaseUrl, setMistralBaseUrl] = useState("https://api.mistral.ai/v1");
  const [mistralKeyInput, setMistralKeyInput] = useState("");
  const [mistralHint, setMistralHint] = useState<string | null>(null);
  const [mistralConfigured, setMistralConfigured] = useState(false);
  const [mistralSaved, setMistralSaved] = useState(false);
  const [mistralError, setMistralError] = useState<string | null>(null);
  const [mistralTesting, setMistralTesting] = useState(false);
  const [mistralTestOk, setMistralTestOk] = useState<boolean | null>(null);
  const [mistralTestMessage, setMistralTestMessage] = useState<string | null>(null);

  const loadBackends = () => {
    fetch("/api/backends")
      .then((r) => r.json())
      .then((d) => setBackends(d.backends || []))
      .catch(() => {});
  };

  const loadMistral = () => {
    fetch("/api/settings/mistral")
      .then((r) => r.json())
      .then((d: MistralSettingsResponse) => {
        setMistralConfigured(d.key_configured);
        setMistralHint(d.key_hint);
        if (d.base_url) setMistralBaseUrl(d.base_url);
      })
      .catch(() => {});
  };

  const loadWatcherStatus = () => {
    fetch("/api/scanner/watch/status")
      .then((r) => r.json())
      .then((d) => setWatcherStatus(d))
      .catch(() => {});
  };

  useEffect(() => {
    loadBackends();
    fetch("/api/scanners")
      .then((r) => r.json())
      .then((d) => setScanners(d.scanners || []))
      .catch(() => {});
    loadMistral();
    loadWatcherStatus();
    fetch("/api/llm/providers")
      .then((r) => r.json())
      .then((d) => {
        const list = d.providers || [];
        setLlmProviders(list);
        const map: Record<string, LlmProvider> = {};
        list.forEach((p: LlmProvider) => {
          map[p.id] = p;
        });
        setLlmProviderMap(map);
      })
      .catch(() => {});
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
      base_url: mistralBaseUrl.trim() || "https://api.mistral.ai/v1",
    };
    if (trimmedKey) payload.api_key = trimmedKey;
    try {
      const r = await fetch("/api/settings/mistral", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await r.json().catch(() => ({}));
      if (!r.ok) {
        setMistralError(typeof data.detail === "string" ? data.detail : "Save failed");
        return;
      }
      setMistralKeyInput("");
      setMistralConfigured(Boolean(data.key_configured));
      setMistralHint(data.key_hint ?? null);
      if (data.base_url) setMistralBaseUrl(data.base_url);
      loadBackends();
      setMistralSaved(true);
      setTimeout(() => setMistralSaved(false), 2000);
    } catch {
      setMistralError("Network error");
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
      const r = await fetch("/api/settings/mistral/test", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await r.json().catch(() => ({}));
      if (r.status === 400) {
        const d = data.detail;
        const msg = typeof d === "string" ? d : Array.isArray(d) ? String(d[0]) : "Bad request";
        setMistralTestOk(false);
        setMistralTestMessage(msg);
        return;
      }
      if (!r.ok) {
        const d = data.detail;
        setMistralTestOk(false);
        setMistralTestMessage(typeof d === "string" ? d : `HTTP ${r.status}`);
        return;
      }
      setMistralTestOk(data.valid === true);
      setMistralTestMessage(typeof data.message === "string" ? data.message : data.valid ? "OK" : "Check failed");
    } catch {
      setMistralTestOk(false);
      setMistralTestMessage("Network error");
    } finally {
      setMistralTesting(false);
    }
  };

  const clearMistralKey = async () => {
    setMistralError(null);
    try {
      const r = await fetch("/api/settings/mistral", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ api_key: "" }),
      });
      const data = await r.json().catch(() => ({}));
      if (!r.ok) {
        setMistralError(typeof data.detail === "string" ? data.detail : "Remove failed");
        return;
      }
      setMistralKeyInput("");
      setMistralConfigured(false);
      setMistralHint(null);
      loadBackends();
    } catch {
      setMistralError("Network error");
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
              Required for the <span className="text-slate-300 font-mono">mistral-ocr</span> backend. Key is stored in
              the backend process only (not in browser localStorage).
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
                placeholder={mistralConfigured ? "•••••••• (enter new key to replace)" : "sk-..."}
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
            {mistralError && <p className="text-sm text-red-400">{mistralError}</p>}
            {mistralTestMessage != null && (
              <p className={`text-sm ${mistralTestOk === true ? "text-emerald-400" : "text-red-400"}`} role="status">
                {mistralTestOk === true ? "✓ " : ""}
                {mistralTestMessage}
              </p>
            )}
            <div className="flex flex-wrap items-center gap-2">
              <Button
                type="button"
                onClick={() => void saveMistral()}
                className="bg-amber-600 hover:bg-amber-700 text-white"
              >
                {mistralSaved ? (
                  <>
                    <CheckCircle2 className="w-4 h-4 mr-2" />
                    Saved
                  </>
                ) : (
                  "Save Mistral settings"
                )}
              </Button>
              <Button
                type="button"
                variant="secondary"
                className="bg-slate-800 text-slate-100 hover:bg-slate-700 border border-slate-600"
                onClick={() => void testMistral()}
                disabled={mistralTesting || (!mistralKeyInput.trim() && !mistralConfigured)}
                title={
                  !mistralKeyInput.trim() && !mistralConfigured
                    ? "Enter an API key or save one first"
                    : "GET /models with current or pasted key"
                }
              >
                {mistralTesting ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Testing…
                  </>
                ) : (
                  <>
                    <FlaskConical className="w-4 h-4 mr-2" />
                    Test API key
                  </>
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
              Which model to use for scan OCR and pipeline jobs when "Auto" is not selected explicitly. Stored locally
              in your browser.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-4">
              <select
                value={defaultBackend}
                onChange={(e) => {
                  setDefaultBackend(e.target.value);
                  setSaved(false);
                }}
                className="rounded-md border-0 py-2 pl-3 pr-10 bg-slate-900 text-slate-100 ring-1 ring-inset ring-slate-700 focus:ring-2 focus:ring-purple-600 text-sm min-w-56"
                title="Default OCR Backend"
              >
                <option value="auto">Auto (best available)</option>
                {backends
                  .filter((b) => b.available)
                  .map((b) => (
                    <option key={b.name} value={b.name}>
                      {b.name}
                    </option>
                  ))}
              </select>
              <Button onClick={saveDefaultBackend} className="bg-purple-600 hover:bg-purple-700 text-white">
                {saved ? (
                  <>
                    <CheckCircle2 className="w-4 h-4 mr-2" />
                    Saved
                  </>
                ) : (
                  "Save Default"
                )}
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
                {backends.map((b) => (
                  <div
                    key={b.name}
                    className="flex items-center justify-between p-3 rounded-md border border-slate-800 bg-slate-900"
                  >
                    <div>
                      <p className="font-medium text-slate-200">{b.name}</p>
                      <p className="text-xs text-slate-500">{b.description || "OCR Engine"}</p>
                    </div>
                    <div
                      className={`text-xs px-2 py-1 rounded border ${
                        b.available
                          ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                          : "bg-red-500/10 text-red-400 border-red-500/20"
                      }`}
                    >
                      {b.available ? "Available" : "Offline"}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Auto-Scan Settings */}
        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Eye className="w-5 h-5 text-emerald-400" /> Auto-Scan
            </CardTitle>
            <CardDescription className="text-slate-400">
              Automatically detect documents on the flatbed via preview-scan polling.
              When content change is detected, scan + OCR triggers automatically.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-300">Auto-detect documents</span>
              <button
                onClick={() => {
                  const next = !autoScan;
                  setAutoScan(next);
                  localStorage.setItem(AUTO_SCAN_KEY, String(next));
                  if (next && scanners.length > 0) {
                    fetch("/api/scanner/watch", {
                      method: "POST",
                      headers: { "Content-Type": "application/json" },
                      body: JSON.stringify({
                        device_id: scanners[0].device_id,
                        mode: "preview",
                        backend: defaultBackend === "auto" ? "unlimited-ocr" : defaultBackend,
                      }),
                    }).then(loadWatcherStatus).catch(() => {});
                  } else if (!next) {
                    fetch("/api/scanner/watch/stop", { method: "POST" }).catch(() => {});
                  }
                }}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  autoScan ? "bg-emerald-600" : "bg-slate-700"
                }`}
                role="switch"
                aria-checked={autoScan}
              >
                <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  autoScan ? "translate-x-6" : "translate-x-1"
                }`} />
              </button>
            </div>
            {watcherStatus && watcherStatus.running && (
              <div className="flex items-center gap-2 text-xs text-emerald-400 bg-emerald-500/10 p-3 rounded-md border border-emerald-500/20">
                <Eye className="h-3.5 w-3.5" />
                Watcher active - {watcherStatus.scans_triggered} scans - interval {watcherStatus.interval_s}s
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
                {scanners.map((s) => (
                  <div
                    key={s.device_id}
                    className="flex items-start justify-between p-3 rounded-md border border-slate-800 bg-slate-900"
                  >
                    <div className="space-y-0.5">
                      <p className="font-medium text-slate-200">{s.name}</p>
                      <p className="text-xs text-slate-500">
                        {s.manufacturer || ""}
                        {s.type ? ` · ${s.type}` : ""}
                        {s.max_dpi ? ` · max ${s.max_dpi} DPI` : ""}
                      </p>
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

        {/* Local LLM */}
        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Cpu className="w-5 h-5 text-cyan-400" /> Local LLM
            </CardTitle>
            <CardDescription className="text-slate-400">
              Auto-detected local inference providers. Use with the AI assistant features.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {llmProviders.length === 0 ? (
              <div className="text-sm text-slate-500">No providers detected. Start Ollama or LM Studio.</div>
            ) : (
              <div className="space-y-2">
                {llmProviders.map((p) => (
                  <div
                    key={p.id}
                    className="flex items-center justify-between p-3 rounded-md border border-slate-800 bg-slate-900"
                  >
                    <div>
                      <p className="font-medium text-slate-200">{p.label}</p>
                      <p className="text-xs text-slate-500 font-mono">{p.base_url}</p>
                      {p.models.length > 0 && (
                        <p className="text-xs text-slate-500 mt-0.5">
                          Models: {p.models.slice(0, 5).join(", ")}
                          {p.models.length > 5 ? ` +${p.models.length - 5} more` : ""}
                        </p>
                      )}
                    </div>
                    <div
                      className={`flex items-center gap-1.5 text-xs px-2 py-1 rounded border ${
                        p.models.length > 0
                          ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                          : "bg-zinc-500/10 text-zinc-400 border-zinc-500/20"
                      }`}
                    >
                      {p.models.length > 0 ? (
                        <>
                          <Wifi className="w-3 h-3" /> Online
                        </>
                      ) : (
                        <>
                          <WifiOff className="w-3 h-3" /> Offline
                        </>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
            <div className="flex gap-2">
              <button
                onClick={() => {
                  fetch("/api/llm/providers")
                    .then((r) => r.json())
                    .then((d) => {
                      const list = d.providers || [];
                      setLlmProviders(list);
                      const map: Record<string, LlmProvider> = {};
                      list.forEach((p: LlmProvider) => {
                        map[p.id] = p;
                      });
                      setLlmProviderMap(map);
                    })
                    .catch(() => {});
                }}
                className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 transition-colors bg-slate-800 hover:bg-slate-700 rounded-md px-3 py-1.5 border border-slate-700"
              >
                <RefreshCw className="w-3 h-3" /> Refresh
              </button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
