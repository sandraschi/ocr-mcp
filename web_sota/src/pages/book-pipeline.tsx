import {
  BookOpen,
  CheckCircle2,
  FileText,
  Loader2,
  ScanLine,
  Upload,
  XCircle,
} from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface Chapter {
  chapter_number: number;
  title: string;
  start_page: number;
  end_page: number | null;
  confidence: number;
}

export function BookPipeline() {
  const [files, setFiles] = useState<File[]>([]);
  const [backend, setBackend] = useState("unlimited-ocr");
  const [title, setTitle] = useState("");
  const [author, setAuthor] = useState("");
  const [running, setRunning] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [chapters, setChapters] = useState<Chapter[]>([]);
  const [epubPath, setEpubPath] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [detectedTitle, setDetectedTitle] = useState("");
  const [detectedAuthor, setDetectedAuthor] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  const handleFiles = (e: React.ChangeEvent<HTMLInputElement>) => {
    const picked = Array.from(e.target.files || []);
    setFiles(picked.sort((a, b) => a.name.localeCompare(b.name)));
    setChapters([]);
    setEpubPath(null);
    setStatus(null);
    setError(null);
  };

  const runPipeline = useCallback(async () => {
    if (files.length === 0) return;
    setRunning(true);
    setError(null);
    setStatus("Uploading pages...");
    setProgress(0);
    setChapters([]);
    setEpubPath(null);

    try {
      const pageTexts: { page_number: number; text: string; confidence: number }[] = [];

      for (let i = 0; i < files.length; i++) {
        setStatus(`OCR page ${i + 1}/${files.length}...`);
        setProgress(Math.round((i / files.length) * 80));

        const formData = new FormData();
        formData.append("file", files[i]);
        formData.append("ocr_mode", "text");
        formData.append("backend", backend);

        const res = await fetch("/api/upload", { method: "POST", body: formData });
        if (!res.ok) throw new Error(`Upload failed on page ${i + 1}`);
        const uploadData = await res.json();
        const jobId = uploadData.job_id;
        if (!jobId) throw new Error(`No job_id for page ${i + 1}`);

        // Poll job
        let text = "";
        for (let poll = 0; poll < 60; poll++) {
          await new Promise((r) => setTimeout(r, 2000));
          const jobRes = await fetch(`/api/job/${jobId}`);
          if (!jobRes.ok) break;
          const jobData = await jobRes.json();
          if (jobData.status === "completed") {
            text = jobData.result?.text || jobData.text || "";
            break;
          }
          if (jobData.status === "failed") break;
        }
        pageTexts.push({ page_number: i + 1, text, confidence: text ? 0.85 : 0 });
      }

      setProgress(80);
      setStatus("Detecting chapters...");

      // Detect chapters
      const chapterRes = await fetch("/api/ocr/detect-chapters", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pages: pageTexts }),
      });

      if (chapterRes.ok) {
        const chapterData = await chapterRes.json();
        if (chapterData.chapters) {
          setChapters(chapterData.chapters);
        }
      }

      // Detect metadata
      const metaRes = await fetch("/api/ocr/detect-metadata", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pages: pageTexts.slice(0, 3) }),
      });
      if (metaRes.ok) {
        const metaData = await metaRes.json();
        if (metaData.title) setDetectedTitle(metaData.title);
        if (metaData.author) setDetectedAuthor(metaData.author);
      }

      setProgress(90);
      setStatus("Assembling EPUB...");

      const epubRes = await fetch("/api/ocr/assemble-epub", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: title || detectedTitle,
          author: author || detectedAuthor,
          chapters: chapters.length > 0 ? chapters.map((ch) => {
            const start = ch.start_page;
            const end = ch.end_page ?? pageTexts.length;
            const chText = pageTexts.slice(start - 1, end).map((p) => p.text).join("\n");
            return { chapter_number: ch.chapter_number, title: ch.title, text: chText };
          }) : [{ chapter_number: 1, title: "Chapter 1", text: pageTexts.map((p) => p.text).join("\n") }],
        }),
      });

      if (epubRes.ok) {
        const epubData = await epubRes.json();
        if (epubData.path) setEpubPath(epubData.path);
      }

      setProgress(100);
      setStatus("Complete!");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Pipeline failed");
    } finally {
      setRunning(false);
    }
  }, [files, backend, title, author, chapters, detectedTitle, detectedAuthor]);

  return (
    <div className="space-y-6 max-w-4xl" data-testid="book-pipeline">
      <div className="flex items-center gap-3">
        <BookOpen className="h-8 w-8 text-amber-400" />
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-100">Book Pipeline</h1>
          <p className="text-sm text-slate-400">
            Scan pages &rarr; OCR &rarr; detect chapters &rarr; assemble EPUB
          </p>
        </div>
      </div>

      <Card className="border-slate-800 bg-slate-900/50">
        <CardHeader>
          <CardTitle className="text-slate-100 flex items-center gap-2">
            <ScanLine className="h-5 w-5 text-blue-400" /> Page Images
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <input
            ref={fileRef}
            type="file"
            multiple
            accept="image/*"
            className="hidden"
            onChange={handleFiles}
          />
          <button
            onClick={() => fileRef.current?.click()}
            className="flex w-full items-center justify-center gap-3 rounded-lg border-2 border-dashed border-slate-700 p-8 text-slate-400 hover:border-slate-500 hover:text-slate-300 transition-colors"
          >
            <Upload className="h-8 w-8" />
            <div className="text-left">
              <p className="text-sm font-medium">Select scanned pages</p>
              <p className="text-xs">page_001.png, page_002.png, ... (sorted alphabetically)</p>
            </div>
          </button>
          {files.length > 0 && (
            <p className="text-sm text-slate-400">{files.length} pages selected</p>
          )}
        </CardContent>
      </Card>

      <Card className="border-slate-800 bg-slate-900/50">
        <CardHeader>
          <CardTitle className="text-slate-100 flex items-center gap-2">
            <FileText className="h-5 w-5 text-purple-400" /> Metadata
          </CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="text-xs font-medium text-slate-400 mb-1 block">Title</label>
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder={detectedTitle || "Book title"}
              className="w-full rounded-md border-0 py-2 px-3 bg-slate-950 text-slate-100 ring-1 ring-inset ring-slate-700 focus:ring-2 focus:ring-blue-600 text-sm"
            />
            {detectedTitle && !title && (
              <p className="text-xs text-emerald-400 mt-1">Detected: {detectedTitle}</p>
            )}
          </div>
          <div>
            <label className="text-xs font-medium text-slate-400 mb-1 block">Author</label>
            <input
              value={author}
              onChange={(e) => setAuthor(e.target.value)}
              placeholder={detectedAuthor || "Author name"}
              className="w-full rounded-md border-0 py-2 px-3 bg-slate-950 text-slate-100 ring-1 ring-inset ring-slate-700 focus:ring-2 focus:ring-blue-600 text-sm"
            />
            {detectedAuthor && !author && (
              <p className="text-xs text-emerald-400 mt-1">Detected: {detectedAuthor}</p>
            )}
          </div>
        </CardContent>
      </Card>

      <button
        onClick={runPipeline}
        disabled={running || files.length === 0}
        className="inline-flex items-center gap-2 rounded-lg bg-amber-600 hover:bg-amber-700 disabled:opacity-50 disabled:cursor-not-allowed text-white px-6 py-3 text-sm font-semibold transition-colors w-full justify-center"
      >
        {running ? (
          <Loader2 className="h-5 w-5 animate-spin" />
        ) : (
          <BookOpen className="h-5 w-5" />
        )}
        {running ? status : "Run Pipeline (OCR + Chapter Detect + EPUB)"}
      </button>

      {(running || progress > 0) && (
        <div className="h-2 rounded-full bg-slate-800 overflow-hidden">
          <div
            className="h-full bg-amber-500 transition-all duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>
      )}

      {status && !running && !error && (
        <div className="flex items-center gap-2 text-emerald-400 bg-emerald-500/10 p-3 rounded-md border border-emerald-500/20 text-sm">
          <CheckCircle2 className="h-4 w-4 shrink-0" />
          {status}
        </div>
      )}

      {error && (
        <div className="flex items-center gap-2 text-red-400 bg-red-500/10 p-3 rounded-md border border-red-500/20 text-sm">
          <XCircle className="h-4 w-4 shrink-0" />
          {error}
        </div>
      )}

      {chapters.length > 0 && (
        <Card className="border-slate-800 bg-slate-900/50">
          <CardHeader>
            <CardTitle className="text-slate-100 flex items-center gap-2">
              <BookOpen className="h-5 w-5 text-amber-400" /> Chapters ({chapters.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-1">
              {chapters.map((ch) => (
                <div key={ch.chapter_number} className="flex items-center gap-3 text-sm py-1">
                  <span className="text-xs font-mono text-slate-500 w-8">{ch.chapter_number}.</span>
                  <span className={`flex-1 ${ch.confidence > 0.7 ? "text-slate-200" : "text-slate-400"}`}>
                    {ch.title}
                  </span>
                  <span className="text-xs text-slate-500">p.{ch.start_page}</span>
                  <span className={`text-xs px-1.5 py-0.5 rounded ${
                    ch.confidence > 0.7 ? "bg-emerald-500/10 text-emerald-400" : "bg-amber-500/10 text-amber-400"
                  }`}>
                    {Math.round(ch.confidence * 100)}%
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {epubPath && (
        <div className="flex items-center gap-2 text-emerald-400 bg-emerald-500/10 p-3 rounded-md border border-emerald-500/20 text-sm">
          <CheckCircle2 className="h-4 w-4 shrink-0" />
          EPUB ready: {epubPath}
        </div>
      )}
    </div>
  );
}
