import {
  Activity,
  CheckCircle2,
  Clipboard,
  Cpu,
  Download,
  Eye,
  EyeOff,
  FileText,
  Loader2,
  RefreshCw,
  ScanLine,
  Server,
  Upload,
  XCircle,
} from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useOcrTextStore, useScanStore } from "@/store";

const DEFAULT_BACKEND_KEY = "ocr_default_backend";

interface ScannerInfo {
  device_id: string;
  name: string;
  type: string;
}

interface BackendInfo {
  name: string;
  available: boolean;
}

interface HealthInfo {
  status: string;
  server: string;
  version: string;
  uptime_seconds: number;
  tool_count: number;
}

export function Dashboard() {
  const navigate = useNavigate();
  const { ocrText, setOcrText, ocrJobId, setOcrJobId, ocrStatus, setOcrStatus } = useOcrTextStore();
  const { lastScan, setLastScan, setLastOcrJobId } = useScanStore();

  const [scanners, setScanners] = useState<ScannerInfo[]>([]);
  const [backends, setBackends] = useState<BackendInfo[]>([]);
  const [health, setHealth] = useState<HealthInfo | null>(null);
  const [selectedScanner, setSelectedScanner] = useState("");
  const [selectedBackend, setSelectedBackend] = useState(
    () => localStorage.getItem(DEFAULT_BACKEND_KEY) || "unlimited-ocr",
  );
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);
  const [droppedFile, setDroppedFile] = useState<File | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [copied, setCopied] = useState(false);
  const [watcherActive, setWatcherActive] = useState(false);
  const [watcherScans, setWatcherScans] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const imageUrl = lastScan.imageUrl;

  // Auto-detect unlimited-ocr or best available
  const effectiveBackend =
    selectedBackend === "auto"
      ? backends.find((b) => b.name === "unlimited-ocr" && b.available)?.name || "auto"
      : selectedBackend;

  const fetchScanners = useCallback(async () => {
    try {
      const res = await fetch("/api/scanners");
      const data = await res.json().catch(() => ({}));
      const list = data.scanners || [];
      setScanners(list);
      if (data.default_scanner && !selectedScanner) {
        setSelectedScanner(data.default_scanner);
      } else if (list.length > 0 && !selectedScanner) {
        setSelectedScanner(list[0].device_id);
      }
    } catch {
      /* noop */
    }
  }, [selectedScanner]);

  const fetchBackends = useCallback(async () => {
    try {
      const res = await fetch("/api/backends");
      const data = await res.json().catch(() => ({}));
      setBackends(data.backends || []);
    } catch {
      /* noop */
    }
  }, []);

  const fetchHealth = useCallback(async () => {
    try {
      const res = await fetch("/api/health");
      if (res.ok) {
        const data = await res.json();
        setHealth(data);
      }
    } catch {
      /* noop */
    }
  }, []);

  const fetchWatcherStatus = useCallback(async () => {
    try {
      const res = await fetch("/api/scanner/watch/status");
      if (res.ok) {
        const data = await res.json();
        setWatcherActive(data.running);
        setWatcherScans(data.scans_triggered || 0);
      }
    } catch { /* noop */ }
  }, []);

  const toggleWatcher = useCallback(async () => {
    if (watcherActive) {
      await fetch("/api/scanner/watch/stop", { method: "POST" });
      setWatcherActive(false);
    } else {
      const deviceId = selectedScanner || (scanners.length > 0 ? scanners[0].device_id : "");
      if (!deviceId) return;
      await fetch("/api/scanner/watch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ device_id: deviceId, mode: "preview", backend: effectiveBackend }),
      });
      setWatcherActive(true);
    }
  }, [watcherActive, selectedScanner, scanners, effectiveBackend]);

  useEffect(() => {
    fetchScanners();
    fetchBackends();
    fetchHealth();
    fetchWatcherStatus();
    const interval = setInterval(fetchHealth, 30000);
    const watcherInterval = setInterval(fetchWatcherStatus, 5000);
    return () => { clearInterval(interval); clearInterval(watcherInterval); };
  }, [fetchScanners, fetchBackends, fetchHealth, fetchWatcherStatus]);

  // Poll job status
  const pollJob = useCallback(
    (jobId: string) => {
      stopPoll();
      pollRef.current = setInterval(async () => {
        try {
          const res = await fetch(`/api/job/${jobId}`);
          if (!res.ok) {
            stopPoll();
            setOcrStatus("failed");
            setError("Job not found");
            return;
          }
          const data = await res.json();
          if (data.status === "completed") {
            stopPoll();
            setOcrStatus("completed");
            setScanning(false);
            const text = data.result?.text || data.result?.markdown || data.text || "";
            if (text) setOcrText(text);
            setStatusMsg("OCR complete");
          } else if (data.status === "failed") {
            stopPoll();
            setOcrStatus("failed");
            setScanning(false);
            setError(data.error || "OCR failed");
          }
        } catch {
          stopPoll();
          setOcrStatus("failed");
          setScanning(false);
          setError("Network error polling job");
        }
      }, 1500);
    },
    [setOcrStatus, setOcrText],
  );

  const stopPoll = () => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  };

  useEffect(() => () => stopPoll(), []);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) {
      setDroppedFile(file);
      setError(null);
      setStatusMsg(null);
    }
  };

  const handleFilePick = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setDroppedFile(file);
      setError(null);
      setStatusMsg(null);
    }
  };

  const handleQuickScanOcr = async () => {
    setError(null);
    setStatusMsg(null);
    setScanning(true);
    setOcrStatus("processing");
    setOcrText("");

    try {
      if (droppedFile) {
        // Upload file
        const formData = new FormData();
        formData.append("file", droppedFile);
        formData.append("ocr_mode", "text");
        formData.append("backend", effectiveBackend);

        const res = await fetch("/api/upload", { method: "POST", body: formData });
        if (!res.ok) throw new Error("Upload failed");
        const data = await res.json();
        const jobId = data.job_id;
        if (!jobId) throw new Error("No job ID returned");
        setOcrJobId(jobId);
        setLastOcrJobId(jobId);
        setStatusMsg("Processing uploaded file...");
        pollJob(jobId);
      } else if (selectedScanner && scanners.length > 0) {
        // Scan then OCR
        const scanForm = new FormData();
        scanForm.append("device_id", selectedScanner);
        scanForm.append("dpi", "300");
        scanForm.append("color_mode", "Color");
        scanForm.append("paper_size", "A4");

        const scanRes = await fetch("/api/scan", { method: "POST", body: scanForm });
        if (!scanRes.ok) throw new Error("Scan failed");
        const scanData = await scanRes.json();
        if (!scanData.success) throw new Error(scanData.message || "Scan failed");

        const filename = scanData.image_info?.filename || scanData.filename;
        setLastScan({ imageUrl: scanData.image_path, filename });

        const ocrForm = new FormData();
        ocrForm.append("filename", filename);
        ocrForm.append("ocr_mode", "text");
        ocrForm.append("backend", effectiveBackend);

        const ocrRes = await fetch("/api/ocr_scanned", { method: "POST", body: ocrForm });
        if (!ocrRes.ok) throw new Error("OCR request failed");
        const ocrData = await ocrRes.json();
        const jobId = ocrData.job_id;
        if (!jobId) throw new Error("No OCR job ID returned");
        setOcrJobId(jobId);
        setLastOcrJobId(jobId);
        setStatusMsg("Scanning + OCR in progress...");
        pollJob(jobId);
      } else {
        setScanning(false);
        setOcrStatus("idle");
        setError("No scanner available and no file selected. Drop a file or connect a scanner.");
      }
    } catch (err: unknown) {
      setScanning(false);
      setOcrStatus("failed");
      setError(err instanceof Error ? err.message : "Unknown error");
    }
  };

  const handleCopy = async () => {
    if (!ocrText) return;
    try {
      await navigator.clipboard.writeText(ocrText);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      /* noop */
    }
  };

  const handleDownloadTxt = () => {
    if (!ocrText) return;
    const blob = new Blob([ocrText], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `ocr-result-${Date.now()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleDownloadMd = () => {
    if (!ocrText) return;
    const blob = new Blob([ocrText], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `ocr-result-${Date.now()}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const backendOk = backends.some((b) => b.available);

  return (
    <div data-testid="dashboard" className="space-y-6">
      {/* KPI row */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card className="border-slate-800 bg-slate-950/50" data-testid="kpi-server">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">Server</CardTitle>
            <Server className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-lg font-bold text-white truncate">{health?.server || "ocr-mcp"}</div>
            <p className="text-xs text-slate-400">{health?.version ? `v${health.version}` : "connecting..."}</p>
          </CardContent>
        </Card>
        <Card className="border-slate-800 bg-slate-950/50" data-testid="kpi-tools">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">Tools</CardTitle>
            <Cpu className="h-4 w-4 text-purple-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">{health?.tool_count ?? "—"}</div>
            <p className="text-xs text-slate-400">MCP tools registered</p>
          </CardContent>
        </Card>
        <Card className="border-slate-800 bg-slate-950/50" data-testid="kpi-backends">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">Backends</CardTitle>
            <Activity className="h-4 w-4 text-emerald-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">
              {backends.filter((b) => b.available).length}/{backends.length}
            </div>
            <p className="text-xs text-slate-400">Available / total</p>
          </CardContent>
        </Card>
        <Card className="border-slate-800 bg-slate-950/50" data-testid="kpi-jobs">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">Status</CardTitle>
            <div className="flex items-center gap-2">
              <span
                data-testid="backend-dot"
                className={`relative flex h-2.5 w-2.5 ${backendOk ? "bg-green-500" : "bg-red-500"} rounded-full`}
              >
                <span
                  className={`absolute inline-flex h-full w-full animate-ping rounded-full ${backendOk ? "bg-green-400" : "bg-red-400"} opacity-75`}
                />
              </span>
              <span className="text-xs text-slate-400">{backendOk ? "Online" : "Offline"}</span>
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-lg font-bold text-white">{ocrJobId ? "Active" : "Idle"}</div>
            <p className="text-xs text-slate-400">{ocrJobId ? ocrStatus : "Waiting for input"}</p>
          </CardContent>
        </Card>
      </div>

      {/* Action bar: scanner + backend + Quick Scan */}
      <Card className="border-slate-800 bg-slate-950/50">
        <CardContent className="p-4">
          <div className="flex flex-wrap items-end gap-4">
            {/* Scanner selector */}
            <div className="min-w-[200px] flex-1">
              <label className="text-xs font-medium text-slate-400 mb-1 block">Scanner</label>
              <select
                value={selectedScanner}
                onChange={(e) => setSelectedScanner(e.target.value)}
                className="w-full rounded-md border-0 py-2 pl-3 pr-8 bg-slate-900 text-slate-100 ring-1 ring-inset ring-slate-700 focus:ring-2 focus:ring-blue-600 text-sm"
                title="Select scanner"
                data-testid="scanner-select"
              >
                {scanners.length === 0 && <option value="">No scanner detected</option>}
                {scanners.map((s) => (
                  <option key={s.device_id} value={s.device_id}>
                    {s.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Backend selector */}
            <div className="min-w-[180px] flex-1">
              <label className="text-xs font-medium text-slate-400 mb-1 block">OCR Backend</label>
              <select
                value={selectedBackend}
                onChange={(e) => {
                  setSelectedBackend(e.target.value);
                  localStorage.setItem(DEFAULT_BACKEND_KEY, e.target.value);
                }}
                className="w-full rounded-md border-0 py-2 pl-3 pr-8 bg-slate-900 text-slate-100 ring-1 ring-inset ring-slate-700 focus:ring-2 focus:ring-purple-600 text-sm"
                title="Select OCR backend"
                data-testid="backend-select"
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
            </div>

            {/* Quick Scan button */}
            <button
              onClick={handleQuickScanOcr}
              disabled={scanning}
              data-testid="quick-scan-ocr"
              className="inline-flex items-center gap-2 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white px-6 py-2.5 text-sm font-semibold transition-colors"
            >
              {scanning ? <Loader2 className="h-5 w-5 animate-spin" /> : <ScanLine className="h-5 w-5" />}
              {scanning ? "Processing..." : droppedFile ? "OCR File" : "Quick Scan & OCR"}
            </button>

            {/* Auto-scan watcher toggle */}
            <button
              onClick={toggleWatcher}
              disabled={scanners.length === 0}
              data-testid="auto-scan-toggle"
              className={`inline-flex items-center gap-2 rounded-lg border px-4 py-2.5 text-sm font-semibold transition-colors ${
                watcherActive
                  ? "border-emerald-600 bg-emerald-600/20 text-emerald-400 hover:bg-emerald-600/30"
                  : "border-slate-700 bg-slate-800 text-slate-300 hover:bg-slate-700"
              } disabled:opacity-30 disabled:cursor-not-allowed`}
              title={watcherActive ? `Auto-scan active (${watcherScans} triggered)` : "Auto-scan: watch for documents"}
            >
              {watcherActive ? <Eye className="h-5 w-5" /> : <EyeOff className="h-5 w-5" />}
              {watcherActive ? `Watching (${watcherScans})` : "Auto-Scan"}
            </button>
          </div>
        </CardContent>
      </Card>

      {/* Drop zone or image preview */}
      {!imageUrl && !scanning && ocrStatus === "idle" ? (
        <button
          type="button"
          data-testid="drop-zone"
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`flex w-full flex-col items-center justify-center rounded-lg border-2 border-dashed p-12 cursor-pointer transition-colors ${
            dragOver ? "border-blue-500 bg-blue-500/10" : "border-slate-700 bg-slate-900/30 hover:border-slate-500"
          }`}
        >
          <input ref={fileInputRef} type="file" accept="image/*,.pdf" className="hidden" onChange={handleFilePick} />
          <Upload className="h-10 w-10 text-slate-500 mb-3" />
          <p className="text-sm font-medium text-slate-300">
            {droppedFile ? droppedFile.name : "Drop an image or PDF here, or click to browse"}
          </p>
          <p className="text-xs text-slate-500 mt-1">
            {scanners.length > 0
              ? "Or select a scanner above and click Quick Scan & OCR."
              : "Supports PNG, JPG, TIFF, PDF"}
          </p>
        </button>
      ) : (imageUrl || scanning || ocrStatus !== "idle") && !droppedFile ? (
        /* Image preview (scanner mode) */
        imageUrl && (
          <Card className="border-slate-800 bg-slate-900/50 overflow-hidden">
            <CardContent className="p-0">
              <div className="flex items-center justify-center max-h-[400px] overflow-hidden bg-slate-950">
                <img src={imageUrl} alt="Scan preview" className="max-w-full max-h-[400px] object-contain" />
              </div>
            </CardContent>
          </Card>
        )
      ) : null}

      {/* Processing indicator */}
      {scanning && (
        <div className="flex items-center gap-3 rounded-lg border border-blue-800 bg-blue-950/20 p-4">
          <Loader2 className="h-5 w-5 animate-spin text-blue-400" />
          <span className="text-sm text-blue-300">{statusMsg || "Processing..."}</span>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 rounded-lg border border-red-800 bg-red-950/20 p-3">
          <XCircle className="h-4 w-4 text-red-400 shrink-0" />
          <span className="text-sm text-red-300">{error}</span>
        </div>
      )}

      {/* OCR Result */}
      <Card className="border-slate-800 bg-slate-900/50">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-slate-100 flex items-center gap-2">
            <FileText className="h-5 w-5 text-blue-400" />
            OCR Result
          </CardTitle>
          <div className="flex items-center gap-2">
            <button
              onClick={handleCopy}
              disabled={!ocrText}
              data-testid="export-copy"
              className="inline-flex items-center gap-1.5 rounded-md border border-slate-700 bg-slate-800 px-3 py-1.5 text-xs text-slate-300 hover:bg-slate-700 disabled:opacity-30 transition-colors"
            >
              <Clipboard className="h-3.5 w-3.5" />
              {copied ? "Copied!" : "Copy"}
            </button>
            <button
              onClick={handleDownloadTxt}
              disabled={!ocrText}
              data-testid="export-txt"
              className="inline-flex items-center gap-1.5 rounded-md border border-slate-700 bg-slate-800 px-3 py-1.5 text-xs text-slate-300 hover:bg-slate-700 disabled:opacity-30 transition-colors"
            >
              <Download className="h-3.5 w-3.5" />
              .txt
            </button>
            <button
              onClick={handleDownloadMd}
              disabled={!ocrText}
              data-testid="export-md"
              className="inline-flex items-center gap-1.5 rounded-md border border-slate-700 bg-slate-800 px-3 py-1.5 text-xs text-slate-300 hover:bg-slate-700 disabled:opacity-30 transition-colors"
            >
              <Download className="h-3.5 w-3.5" />
              .md
            </button>
            {ocrJobId && (
              <button
                onClick={() => navigate(`/editor?job_id=${ocrJobId}`)}
                className="inline-flex items-center gap-1.5 rounded-md border border-slate-700 bg-slate-800 px-3 py-1.5 text-xs text-slate-300 hover:bg-slate-700 transition-colors"
              >
                <FileText className="h-3.5 w-3.5" />
                Full Editor
              </button>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {ocrStatus === "processing" && !ocrText ? (
            <div className="flex items-center justify-center h-32 text-slate-500">
              <Loader2 className="h-6 w-6 animate-spin mr-3 text-blue-400" />
              <span className="text-sm">OCR in progress...</span>
            </div>
          ) : (
            <textarea
              data-testid="ocr-result"
              className="w-full min-h-[200px] max-h-[500px] rounded-md border-0 py-3 px-4 bg-slate-950 text-slate-100 ring-1 ring-inset ring-slate-800 focus:ring-2 focus:ring-blue-600 sm:text-sm font-mono resize-y"
              value={ocrText}
              onChange={(e) => setOcrText(e.target.value)}
              placeholder={
                ocrStatus === "completed" && !ocrText
                  ? "OCR completed but no text was extracted."
                  : "Scan or upload a document, then click Quick Scan & OCR. Result appears here."
              }
            />
          )}
          {ocrStatus === "completed" && ocrText && (
            <div className="mt-2 flex items-center gap-2 text-emerald-400 text-xs">
              <CheckCircle2 className="h-3.5 w-3.5" />
              OCR complete
            </div>
          )}
        </CardContent>
      </Card>

      {/* Recent history strip */}
      {ocrJobId && (
        <div className="flex items-center gap-2 text-xs text-slate-500">
          <RefreshCw className="h-3 w-3" />
          Latest job: <span className="font-mono text-slate-400">{ocrJobId.slice(0, 24)}</span>
          <button onClick={() => navigate("/status")} className="text-blue-400 hover:underline ml-2">
            View activity
          </button>
        </div>
      )}
    </div>
  );
}
