import {
  Activity,
  AlertCircle,
  ArrowLeft,
  Check,
  Copy,
  Download,
  FileText,
  Mail,
  MessageSquare,
  Printer,
  Scan,
  Share2,
} from "lucide-react";
import { useCallback, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScanViewer } from "@/components/ui/ScanViewer";
import { useScanStore } from "@/store";

export function ScanViewerPage() {
  const { lastScan, setLastScan, setLastOcrJobId } = useScanStore();
  const navigate = useNavigate();
  const [isProcessingSelection, setIsProcessingSelection] = useState(false);
  const [ocrResult, setOcrResult] = useState<string | null>(null);
  const [copiedMsg, setCopiedMsg] = useState<string | null>(null);

  const imageUrl = lastScan.imageUrl;
  const selection = lastScan.selection;

  const setSelection = useCallback(
    (
      sel: {
        x: number;
        y: number;
        width: number;
        height: number;
        imgWidth: number;
        imgHeight: number;
      } | null,
    ) => setLastScan({ selection: sel }),
    [setLastScan],
  );

  const handleSelectionProcess = async () => {
    if (!selection || !lastScan.filename) return;

    setIsProcessingSelection(true);
    setOcrResult(null);

    try {
      const formData = new FormData();
      formData.append("filename", lastScan.filename);
      formData.append("x", selection.x.toString());
      formData.append("y", selection.y.toString());
      formData.append("width", selection.width.toString());
      formData.append("height", selection.height.toString());
      formData.append("backend", "auto");

      const response = await fetch("/api/ocr_selection", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to process selection");
      }

      const data = await response.json();
      if (data.job_id) setLastOcrJobId(data.job_id);
      setOcrResult("OCR job started — latest job is saved. Open Editor or Status (no copy/paste needed).");
    } catch (err: unknown) {
      console.error("Failed to process selection:", err);
      setOcrResult(`Error: ${err instanceof Error ? err.message : "Unknown error"}`);
    } finally {
      setIsProcessingSelection(false);
    }
  };

  const handlePrint = () => {
    if (!imageUrl) return;
    const printWin = window.open("", "_blank");
    if (printWin) {
      printWin.document.write(`
        <!DOCTYPE html>
        <html>
          <head>
            <title>Print Raw Scan - ${lastScan.filename || "scan"}</title>
            <style>
              body { margin: 0; padding: 20px; display: flex; justify-content: center; align-items: center; background: #fff; }
              img { max-width: 100%; max-height: 95vh; object-fit: contain; }
              @media print { body { padding: 0; } img { max-width: 100%; width: 100%; height: auto; } }
            </style>
          </head>
          <body>
            <img src="${imageUrl}" onload="window.print(); window.close();" />
          </body>
        </html>
      `);
      printWin.document.close();
    }
  };

  const handleDownload = () => {
    if (!imageUrl) return;
    const a = document.createElement("a");
    a.href = imageUrl;
    a.download = lastScan.filename || `raw-scan-${Date.now()}.png`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  const handleEmail = () => {
    const subject = encodeURIComponent(`Scanned Document: ${lastScan.filename || "scan"}`);
    const fullUrl = `${window.location.origin}${imageUrl}`;
    const body = encodeURIComponent(
      `Here is the raw scanned document.\n\nFilename: ${lastScan.filename || "scan"}\nImage URL: ${fullUrl}\n`,
    );
    window.location.href = `mailto:?subject=${subject}&body=${body}`;
  };

  const handleDiscordShare = async () => {
    const fullUrl = `${window.location.origin}${imageUrl}`;
    const discordPayload = `![Scanned Document](${fullUrl})`;
    try {
      await navigator.clipboard.writeText(discordPayload);
      setCopiedMsg("Discord markdown link copied!");
      setTimeout(() => setCopiedMsg(null), 3000);
    } catch {
      setCopiedMsg("Failed to copy link");
    }
  };

  const handleCopyLink = async () => {
    const fullUrl = `${window.location.origin}${imageUrl}`;
    try {
      await navigator.clipboard.writeText(fullUrl);
      setCopiedMsg("Image link copied!");
      setTimeout(() => setCopiedMsg(null), 3000);
    } catch {
      setCopiedMsg("Failed to copy link");
    }
  };

  if (!imageUrl) {
    return (
      <div className="flex flex-col items-center justify-center h-[70vh] space-y-6 text-center">
        <div className="p-6 bg-slate-900/50 rounded-full border border-slate-800">
          <Scan className="w-12 h-12 text-slate-500" />
        </div>
        <div className="space-y-2">
          <h2 className="text-2xl font-bold text-slate-100">No Active Raw Scan</h2>
          <p className="text-slate-400 max-w-md">
            You haven't performed any scans in this session. Go to Dashboard and click "Quick Scan (Raw)" to start.
          </p>
        </div>
        <Button onClick={() => navigate("/")} className="bg-blue-600 hover:bg-blue-700">
          Go to Dashboard
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap justify-between items-center gap-4">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => navigate("/")} className="text-slate-400 hover:text-white">
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-slate-100">Raw Scan Webpage</h1>
            <p className="text-slate-400">View, export, print, email, share to Discord, or OCR selection.</p>
          </div>
        </div>

        {/* Export & Action Controls Toolbar */}
        <div className="flex flex-wrap items-center gap-2">
          <Button
            onClick={handlePrint}
            variant="outline"
            size="sm"
            className="gap-1.5 border-slate-700 bg-slate-800 text-slate-200 hover:bg-slate-700"
            title="Print raw scan"
          >
            <Printer className="w-4 h-4 text-blue-400" /> Print
          </Button>

          <Button
            onClick={handleDownload}
            variant="outline"
            size="sm"
            className="gap-1.5 border-slate-700 bg-slate-800 text-slate-200 hover:bg-slate-700"
            title="Download raw scan image"
          >
            <Download className="w-4 h-4 text-emerald-400" /> Export / Save
          </Button>

          <Button
            onClick={handleEmail}
            variant="outline"
            size="sm"
            className="gap-1.5 border-slate-700 bg-slate-800 text-slate-200 hover:bg-slate-700"
            title="Send raw scan via email"
          >
            <Mail className="w-4 h-4 text-amber-400" /> Email
          </Button>

          <Button
            onClick={handleDiscordShare}
            variant="outline"
            size="sm"
            className="gap-1.5 border-slate-700 bg-slate-800 text-slate-200 hover:bg-slate-700"
            title="Copy Discord markdown image embed link"
          >
            <MessageSquare className="w-4 h-4 text-indigo-400" /> Discord Link
          </Button>

          <Button
            onClick={handleCopyLink}
            variant="outline"
            size="sm"
            className="gap-1.5 border-slate-700 bg-slate-800 text-slate-200 hover:bg-slate-700"
            title="Copy direct image URL"
          >
            <Copy className="w-4 h-4 text-purple-400" /> Copy URL
          </Button>

          {selection && (
            <Button
              onClick={handleSelectionProcess}
              disabled={isProcessingSelection}
              className="gap-2 bg-blue-600 hover:bg-blue-700 text-white"
            >
              <FileText className="w-4 h-4" />
              {isProcessingSelection ? "Processing..." : "OCR Selection"}
            </Button>
          )}
        </div>
      </div>

      {copiedMsg && (
        <div className="bg-emerald-950/80 border border-emerald-800 text-emerald-300 px-4 py-2 rounded-md text-sm flex items-center gap-2">
          <Check className="w-4 h-4" /> {copiedMsg}
        </div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
        <Card className="xl:col-span-3 bg-slate-900/50 border-slate-800 overflow-hidden h-[700px]">
          <CardContent className="p-0 h-full">
            <ScanViewer imageUrl={imageUrl} onSelectionChange={setSelection} isProcessing={isProcessingSelection} />
          </CardContent>
        </Card>

        <div className="space-y-6">
          <Card className="bg-slate-900/50 border-slate-800">
            <CardHeader>
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Share2 className="w-4 h-4 text-emerald-400" /> Quick Actions
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Button
                variant="outline"
                size="sm"
                className="w-full justify-start border-slate-800 bg-slate-950 text-slate-300 hover:bg-slate-800"
                onClick={handlePrint}
              >
                <Printer className="w-4 h-4 mr-2 text-blue-400" /> Print Raw Document
              </Button>
              <Button
                variant="outline"
                size="sm"
                className="w-full justify-start border-slate-800 bg-slate-950 text-slate-300 hover:bg-slate-800"
                onClick={handleDownload}
              >
                <Download className="w-4 h-4 mr-2 text-emerald-400" /> Save Image File
              </Button>
              <Button
                variant="outline"
                size="sm"
                className="w-full justify-start border-slate-800 bg-slate-950 text-slate-300 hover:bg-slate-800"
                onClick={handleEmail}
              >
                <Mail className="w-4 h-4 mr-2 text-amber-400" /> Email Scan
              </Button>
              <Button
                variant="outline"
                size="sm"
                className="w-full justify-start border-slate-800 bg-slate-950 text-slate-300 hover:bg-slate-800"
                onClick={handleDiscordShare}
              >
                <MessageSquare className="w-4 h-4 mr-2 text-indigo-400" /> Copy for Discord
              </Button>
            </CardContent>
          </Card>

          <Card className="bg-slate-900/50 border-slate-800">
            <CardHeader>
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <FileText className="w-4 h-4 text-blue-400" /> OCR Result
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="bg-slate-950 p-4 rounded-md border border-slate-800 min-h-[160px] text-sm font-mono text-slate-300 whitespace-pre-wrap break-all">
                {ocrResult || (selection ? "Click 'OCR Selection' to start..." : "Select an area to OCR.")}
              </div>
              {ocrResult && (
                <div className="flex flex-col gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full border-slate-700 text-slate-300 hover:bg-slate-800"
                    onClick={() => navigate("/editor")}
                  >
                    <FileText className="w-4 h-4 mr-2" /> View text
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full border-slate-700 text-slate-300 hover:bg-slate-800"
                    onClick={() => navigate("/status")}
                  >
                    <Activity className="w-4 h-4 mr-2" /> Activity
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>

          <Card className="bg-slate-900/50 border-slate-800">
            <CardHeader>
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-purple-400" /> Capture Info
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-400">Filename:</span>
                <span className="text-slate-200 truncate ml-2 max-w-[150px]" title={lastScan.filename || ""}>
                  {lastScan.filename || "scan.png"}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Scan Status:</span>
                <span className="text-emerald-400 font-medium">Ready</span>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
