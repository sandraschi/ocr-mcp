import {
  ArrowUpDown,
  Check,
  Copy,
  Database,
  Eye,
  FileText,
  Filter,
  Grid,
  List,
  RefreshCw,
  Search,
  Trash2,
  X,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useOcrTextStore } from "@/store";

interface CorpusDocument {
  id: string;
  source_path: string;
  title: string;
  tags: string[];
  ocr_excerpt?: string;
  backend?: string;
  created_at: number;
  updated_at?: number;
}

export function Depot() {
  const navigate = useNavigate();
  const { setOcrText } = useOcrTextStore();
  const [documents, setDocuments] = useState<CorpusDocument[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedBackend, setSelectedBackend] = useState("all");
  const [sortBy, setSortBy] = useState("created_at");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");
  const [selectedDoc, setSelectedDoc] = useState<CorpusDocument | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const fetchCorpus = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        sort_by: sortBy,
        sort_order: sortOrder,
        limit: "50",
      });
      if (searchQuery.trim()) params.append("query", searchQuery.trim());
      if (selectedBackend !== "all") params.append("backend", selectedBackend);

      const res = await fetch(`/api/corpus?${params.toString()}`);
      if (res.ok) {
        const data = await res.json();
        setDocuments(data.results || []);
        setTotalCount(data.total || (data.results || []).length);
      }
    } catch (err) {
      console.error("Failed to fetch corpus:", err);
    } finally {
      setLoading(false);
    }
  }, [searchQuery, selectedBackend, sortBy, sortOrder]);

  useEffect(() => {
    fetchCorpus();
  }, [fetchCorpus]);

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm("Are you sure you want to remove this document entry from the corpus depot?")) return;
    try {
      const res = await fetch(`/api/corpus/${id}`, { method: "DELETE" });
      if (res.ok) {
        setDocuments((prev) => prev.filter((d) => d.id !== id));
        setTotalCount((prev) => Math.max(0, prev - 1));
        if (selectedDoc?.id === id) setSelectedDoc(null);
      }
    } catch (err) {
      console.error("Delete failed:", err);
    }
  };

  const handleCopyText = async (text: string, id: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedId(id);
      setTimeout(() => setCopiedId(null), 2000);
    } catch {
      /* noop */
    }
  };

  const handleOpenInEditor = (text: string) => {
    setOcrText(text);
    navigate("/editor");
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap justify-between items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-100 flex items-center gap-3">
            <Database className="w-8 h-8 text-blue-500" /> Corpus Depot
          </h1>
          <p className="text-slate-400">Searchable, sortable, and filterable repository of raw scans & OCR results.</p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={fetchCorpus}
            className="border-slate-800 bg-slate-900 text-slate-300"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? "animate-spin" : ""}`} /> Refresh
          </Button>
          <div className="flex border border-slate-800 rounded-md bg-slate-900 p-0.5">
            <Button
              variant="ghost"
              size="icon"
              className={`h-8 w-8 ${viewMode === "grid" ? "bg-slate-800 text-white" : "text-slate-400"}`}
              onClick={() => setViewMode("grid")}
            >
              <Grid className="w-4 h-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className={`h-8 w-8 ${viewMode === "list" ? "bg-slate-800 text-white" : "text-slate-400"}`}
              onClick={() => setViewMode("list")}
            >
              <List className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <Card className="bg-slate-900/50 border-slate-800">
        <CardContent className="p-4">
          <div className="flex flex-wrap items-center gap-4">
            {/* Search Input */}
            <div className="relative flex-1 min-w-[240px]">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
              <Input
                placeholder="Search by title, path, tags, or OCR content..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9 bg-slate-950 border-slate-800 text-slate-100 placeholder:text-slate-500"
              />
            </div>

            {/* Backend Filter */}
            <div className="flex items-center gap-2 min-w-[180px]">
              <Filter className="w-4 h-4 text-slate-500" />
              <select
                value={selectedBackend}
                onChange={(e) => setSelectedBackend(e.target.value)}
                className="rounded-md border-0 py-2 pl-3 pr-8 bg-slate-950 text-slate-200 ring-1 ring-inset ring-slate-800 text-sm focus:ring-2 focus:ring-blue-600"
              >
                <option value="all">All Backends</option>
                <option value="unlimited-ocr">unlimited-ocr</option>
                <option value="paddleocr-vl">paddleocr-vl</option>
                <option value="deepseek-ocr">deepseek-ocr</option>
                <option value="tesseract">tesseract</option>
                <option value="easyocr">easyocr</option>
                <option value="pymupdf_digital_bypass">pymupdf_digital_bypass</option>
              </select>
            </div>

            {/* Sort Controls */}
            <div className="flex items-center gap-2">
              <ArrowUpDown className="w-4 h-4 text-slate-500" />
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="rounded-md border-0 py-2 pl-3 pr-8 bg-slate-950 text-slate-200 ring-1 ring-inset ring-slate-800 text-sm focus:ring-2 focus:ring-blue-600"
              >
                <option value="created_at">Sort by Date</option>
                <option value="title">Sort by Title</option>
                <option value="backend">Sort by Backend</option>
              </select>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setSortOrder(sortOrder === "asc" ? "desc" : "asc")}
                className="border-slate-800 bg-slate-950 text-slate-300"
              >
                {sortOrder.toUpperCase()}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Depot Counter */}
      <div className="flex justify-between items-center text-sm text-slate-400">
        <span>
          Showing {documents.length} of {totalCount} indexed depot documents
        </span>
      </div>

      {/* Grid or List View */}
      {loading ? (
        <div className="flex justify-center items-center py-20">
          <RefreshCw className="w-8 h-8 text-blue-500 animate-spin" />
        </div>
      ) : documents.length === 0 ? (
        <Card className="bg-slate-900/30 border-slate-800 py-16 text-center">
          <CardContent className="space-y-4">
            <Database className="w-12 h-12 text-slate-600 mx-auto" />
            <h3 className="text-lg font-semibold text-slate-300">No Depot Documents Found</h3>
            <p className="text-sm text-slate-500 max-w-md mx-auto">
              No registered documents match your current filter or search criteria. Perform OCR operations or Auto-Index
              documents to populate the depot.
            </p>
          </CardContent>
        </Card>
      ) : viewMode === "grid" ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {documents.map((doc) => (
            <Card
              key={doc.id}
              onClick={() => setSelectedDoc(doc)}
              className="bg-slate-900/50 border-slate-800 hover:border-slate-700 cursor-pointer transition-all duration-200 overflow-hidden flex flex-col group"
            >
              <CardHeader className="p-4 pb-2 flex flex-row items-start justify-between space-y-0">
                <div className="space-y-1 overflow-hidden pr-2">
                  <CardTitle className="text-base font-semibold text-slate-100 truncate group-hover:text-blue-400 transition-colors">
                    {doc.title}
                  </CardTitle>
                  <p className="text-xs text-slate-500 truncate" title={doc.source_path}>
                    {doc.source_path}
                  </p>
                </div>
                {doc.backend && (
                  <span className="inline-flex items-center rounded-md bg-blue-950/80 border border-blue-800/60 px-2 py-0.5 text-xs font-medium text-blue-300 shrink-0">
                    {doc.backend}
                  </span>
                )}
              </CardHeader>

              <CardContent className="p-4 pt-2 flex-1 flex flex-col justify-between space-y-3">
                <div className="bg-slate-950 p-3 rounded border border-slate-800/80 text-xs font-mono text-slate-400 h-24 overflow-hidden text-ellipsis">
                  {doc.ocr_excerpt || <span className="italic text-slate-600">No OCR excerpt attached</span>}
                </div>

                <div className="flex items-center justify-between text-xs text-slate-500 pt-2 border-t border-slate-800/50">
                  <span>{new Date(doc.created_at * 1000).toLocaleString()}</span>
                  <div className="flex items-center gap-1">
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7 text-slate-400 hover:text-red-400"
                      onClick={(e) => handleDelete(doc.id, e)}
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        /* List View */
        <Card className="bg-slate-900/50 border-slate-800 overflow-hidden">
          <div className="divide-y divide-slate-800">
            {documents.map((doc) => (
              <button
                type="button"
                key={doc.id}
                onClick={() => setSelectedDoc(doc)}
                className="w-full text-left p-4 hover:bg-slate-800/40 cursor-pointer flex flex-wrap items-center justify-between gap-4 transition-colors"
              >
                <div className="space-y-1 flex-1 min-w-[280px]">
                  <div className="flex items-center gap-3">
                    <h4 className="font-semibold text-slate-200 text-sm hover:text-blue-400">{doc.title}</h4>
                    {doc.backend && (
                      <span className="inline-flex items-center rounded bg-blue-950 border border-blue-800 px-2 py-0.5 text-xs text-blue-300">
                        {doc.backend}
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-500 truncate" title={doc.source_path}>
                    {doc.source_path}
                  </p>
                </div>

                <div className="text-xs text-slate-400 max-w-xs truncate font-mono bg-slate-950 px-3 py-1.5 rounded border border-slate-800">
                  {doc.ocr_excerpt || <span className="italic text-slate-600">No excerpt</span>}
                </div>

                <div className="flex items-center gap-4 text-xs text-slate-500 shrink-0">
                  <span>{new Date(doc.created_at * 1000).toLocaleDateString()}</span>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 text-slate-400 hover:text-red-400"
                    onClick={(e) => handleDelete(doc.id, e)}
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </button>
            ))}
          </div>
        </Card>
      )}

      {/* Document Detail Drawer / Modal */}
      {selectedDoc && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <Card className="bg-slate-900 border-slate-800 w-full max-w-3xl max-h-[85vh] flex flex-col shadow-2xl">
            <CardHeader className="p-4 border-b border-slate-800 flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-lg font-bold text-slate-100">{selectedDoc.title}</CardTitle>
                <p className="text-xs text-slate-400 truncate mt-0.5">{selectedDoc.source_path}</p>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setSelectedDoc(null)}
                className="text-slate-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </Button>
            </CardHeader>

            <CardContent className="p-6 overflow-y-auto space-y-6 flex-1">
              {/* Metadata Badges */}
              <div className="flex flex-wrap gap-4 text-xs text-slate-400 bg-slate-950 p-4 rounded-lg border border-slate-800">
                <div>
                  <span className="text-slate-500 block">Backend</span>
                  <span className="font-semibold text-blue-400">{selectedDoc.backend || "N/A"}</span>
                </div>
                <div>
                  <span className="text-slate-500 block">Created At</span>
                  <span className="font-semibold text-slate-200">
                    {new Date(selectedDoc.created_at * 1000).toLocaleString()}
                  </span>
                </div>
                <div>
                  <span className="text-slate-500 block">Corpus ID</span>
                  <span className="font-mono text-slate-300">{selectedDoc.id}</span>
                </div>
              </div>

              {/* OCR Text Excerpt */}
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <h4 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                    <FileText className="w-4 h-4 text-blue-400" /> OCR Content Excerpt
                  </h4>
                  {selectedDoc.ocr_excerpt && (
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleCopyText(selectedDoc.ocr_excerpt || "", selectedDoc.id)}
                        className="h-8 text-xs border-slate-700 bg-slate-800 text-slate-200"
                      >
                        {copiedId === selectedDoc.id ? (
                          <Check className="w-3.5 h-3.5 text-emerald-400 mr-1" />
                        ) : (
                          <Copy className="w-3.5 h-3.5 mr-1" />
                        )}
                        {copiedId === selectedDoc.id ? "Copied!" : "Copy Text"}
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleOpenInEditor(selectedDoc.ocr_excerpt || "")}
                        className="h-8 text-xs border-slate-700 bg-slate-800 text-slate-200"
                      >
                        <Eye className="w-3.5 h-3.5 mr-1 text-blue-400" /> Open in Editor
                      </Button>
                    </div>
                  )}
                </div>
                <div className="bg-slate-950 p-4 rounded-lg border border-slate-800 font-mono text-xs text-slate-300 whitespace-pre-wrap max-h-72 overflow-y-auto">
                  {selectedDoc.ocr_excerpt || "No OCR text attached."}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
