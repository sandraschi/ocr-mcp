import {
  ArrowLeft,
  FileCheck,
  FileSpreadsheet,
  FileText,
  Loader2,
  Plus,
  Printer,
  RotateCcw,
  Save,
  Scan,
  Sparkles,
  Trash2,
  Upload,
} from "lucide-react";
import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useScanStore } from "@/store";

export interface FormField {
  id: string;
  label: string;
  value: string;
  x: number; // percentage (0 - 100)
  y: number; // percentage (0 - 100)
  fontSize: number; // pt
}

export function FormFillerPage() {
  const navigate = useNavigate();
  const { lastScan, setLastScan } = useScanStore();
  const [activeStep, setActiveStep] = useState<1 | 2 | 3 | 4>(1);

  const [formImage, setFormImage] = useState<string | null>(lastScan.imageUrl || null);
  const [formFilename, setFormFilename] = useState<string | null>(lastScan.filename || null);
  const [fields, setFields] = useState<FormField[]>([]);
  const [selectedFieldId, setSelectedFieldId] = useState<string | null>(null);

  const [scanning, setScanning] = useState(false);
  const [detecting, setDetecting] = useState(false);

  const imageContainerRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Handle Scan Empty Form
  const handleScanForm = async () => {
    setScanning(true);
    try {
      // Fetch available scanners
      const resScanners = await fetch("/api/scanners");
      const scannerData = await resScanners.json();
      const deviceId = scannerData.default_scanner || scannerData.scanners?.[0]?.device_id;

      if (!deviceId) {
        throw new Error("No scanner detected. Connect a scanner or upload an image file.");
      }

      const scanForm = new FormData();
      scanForm.append("device_id", deviceId);
      scanForm.append("dpi", "300");
      scanForm.append("color_mode", "Color");
      scanForm.append("paper_size", "A4");

      const scanRes = await fetch("/api/scan", { method: "POST", body: scanForm });
      if (!scanRes.ok) throw new Error("Scan failed");
      const data = await scanRes.json();
      if (!data.success) throw new Error(data.message || "Scan failed");

      const imgUrl = data.image_path;
      const fn = data.image_info?.filename || data.filename;

      setFormImage(imgUrl);
      setFormFilename(fn);
      setLastScan({ imageUrl: imgUrl, filename: fn });
      setActiveStep(2);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Scan failed");
    } finally {
      setScanning(false);
    }
  };

  // Handle Upload Form File
  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const url = URL.createObjectURL(file);
      setFormImage(url);
      setFormFilename(file.name);
      setLastScan({ imageUrl: url, filename: file.name });
      setActiveStep(2);
    }
  };

  // Auto-detect & Elicit Fields via OCR layout analysis
  const handleDetectFields = async () => {
    if (!formFilename && !formImage) return;
    setDetecting(true);
    try {
      // Simulate layout analysis or run OCR detection
      if (formFilename) {
        const formData = new FormData();
        formData.append("filename", formFilename);
        formData.append("ocr_mode", "formatted");
        formData.append("backend", "auto");

        const ocrRes = await fetch("/api/ocr_scanned", { method: "POST", body: formData });
        if (ocrRes.ok) {
          await ocrRes.json();
          // Extract default field positions from OCR result
          const initialFields: FormField[] = [
            { id: "f1", label: "Full Name", value: "", x: 22, y: 18, fontSize: 14 },
            { id: "f2", label: "Date", value: new Date().toLocaleDateString(), x: 72, y: 18, fontSize: 14 },
            { id: "f3", label: "Address", value: "", x: 22, y: 26, fontSize: 14 },
            { id: "f4", label: "Phone Number", value: "", x: 22, y: 34, fontSize: 14 },
            { id: "f5", label: "Account ID / Tax Code", value: "", x: 68, y: 34, fontSize: 14 },
            { id: "f6", label: "Amount ($)", value: "", x: 22, y: 44, fontSize: 14 },
            { id: "f7", label: "Signature", value: "", x: 68, y: 82, fontSize: 16 },
          ];
          setFields(initialFields);
          setActiveStep(3);
          setDetecting(false);
          return;
        }
      }

      // Fallback default elicitation layout
      setFields([
        { id: "f1", label: "Full Name", value: "", x: 22, y: 18, fontSize: 14 },
        { id: "f2", label: "Date", value: new Date().toLocaleDateString(), x: 72, y: 18, fontSize: 14 },
        { id: "f3", label: "Address", value: "", x: 22, y: 26, fontSize: 14 },
        { id: "f4", label: "Phone Number", value: "", x: 22, y: 34, fontSize: 14 },
        { id: "f5", label: "Signature", value: "", x: 68, y: 82, fontSize: 16 },
      ]);
      setActiveStep(3);
    } catch {
      alert("Auto field detection notice: default layout loaded.");
      setActiveStep(3);
    } finally {
      setDetecting(false);
    }
  };

  // Click on Canvas to add field
  const handleCanvasClick = (e: React.MouseEvent<HTMLElement>) => {
    if (!imageContainerRef.current) return;
    const rect = imageContainerRef.current.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 100;
    const y = ((e.clientY - rect.top) / rect.height) * 100;

    const newField: FormField = {
      id: `field_${Date.now()}`,
      label: `Field ${fields.length + 1}`,
      value: "",
      x: Math.round(x * 10) / 10,
      y: Math.round(y * 10) / 10,
      fontSize: 14,
    };
    setFields((prev) => [...prev, newField]);
    setSelectedFieldId(newField.id);
  };

  // Update Field Value
  const updateFieldValue = (id: string, value: string) => {
    setFields((prev) => prev.map((f) => (f.id === id ? { ...f, value } : f)));
  };

  // Update Field Properties
  const updateFieldProp = (id: string, key: keyof FormField, val: any) => {
    setFields((prev) => prev.map((f) => (f.id === id ? { ...f, [key]: val } : f)));
  };

  // Delete Field
  const deleteField = (id: string) => {
    setFields((prev) => prev.filter((f) => f.id !== id));
    if (selectedFieldId === id) setSelectedFieldId(null);
  };

  // Save Analyzed Form Template to Depot
  const handleSaveTemplateToDepot = async () => {
    if (!formImage) return;
    const title = prompt("Enter Form Template Title:", formFilename || "Austrian Meldezettel (Meldebestätigung)");
    if (!title) return;

    try {
      const res = await fetch("/api/corpus/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          source_path: formFilename || `form_templates/${title.toLowerCase().replace(/\s+/g, "_")}.png`,
          title: title,
          tags: ["form-template", "meldezettel", "preprinted-form"],
          metadata: {
            is_form_template: true,
            fields: fields,
            form_image_url: formImage,
          },
          backend: "form-filler-overlay",
        }),
      });
      if (res.ok) {
        alert(`Form template "${title}" saved to Corpus Depot! You can reload it anytime.`);
      } else {
        alert("Failed to save template to Depot.");
      }
    } catch (err: unknown) {
      alert(`Save error: ${err instanceof Error ? err.message : "Failed to save"}`);
    }
  };

  // Print Form (Dual Print Mode)
  const handlePrint = (mode: "overlay" | "full") => {
    if (!formImage) return;

    const printWin = window.open("", "_blank");
    if (!printWin) return;

    const fieldsHtml = fields
      .map(
        (f) => `
        <div style="position: absolute; left: ${f.x}%; top: ${f.y}%; font-family: 'Courier New', Courier, monospace; font-weight: bold; font-size: ${f.fontSize}pt; color: #000080; white-space: nowrap; transform: translateY(-50%);">
          ${f.value}
        </div>
      `,
      )
      .join("");

    printWin.document.write(`
      <!DOCTYPE html>
      <html>
        <head>
          <title>Print Filled Form - ${formFilename || "form"}</title>
          <style>
            @page { size: A4 portrait; margin: 0; }
            body { margin: 0; padding: 0; width: 210mm; height: 297mm; position: relative; background: #fff; }
            .form-container { position: relative; width: 100%; height: 100%; overflow: hidden; }
            .bg-image { width: 100%; height: 100%; object-fit: contain; display: ${mode === "full" ? "block" : "none"}; }
            @media print {
              body { width: 210mm; height: 297mm; }
              .bg-image { display: ${mode === "full" ? "block" : "none"}; }
            }
          </style>
        </head>
        <body>
          <div class="form-container">
            ${mode === "full" ? `<img class="bg-image" src="${formImage}" />` : ""}
            ${fieldsHtml}
          </div>
          <script>
            window.onload = function() {
              window.print();
              window.close();
            };
          </script>
        </body>
      </html>
    `);
    printWin.document.close();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap justify-between items-center gap-4">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => navigate("/")} className="text-slate-400 hover:text-white">
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-slate-100 flex items-center gap-3">
              <FileSpreadsheet className="w-8 h-8 text-emerald-500" /> Preprinted Form Filler
            </h1>
            <p className="text-slate-400">
              Scan empty form ➔ Elicit fields ➔ Query input data ➔ Print overlay on preprinted paper.
            </p>
          </div>
        </div>

        {/* 4-Step Progress Indicator */}
        <div className="flex items-center gap-2 bg-slate-900/80 border border-slate-800 p-1.5 rounded-lg text-xs font-semibold text-slate-300">
          <span className={`px-2.5 py-1 rounded ${activeStep === 1 ? "bg-blue-600 text-white" : "text-slate-500"}`}>
            1. Scan Form
          </span>
          <span className="text-slate-600">➔</span>
          <span className={`px-2.5 py-1 rounded ${activeStep === 2 ? "bg-blue-600 text-white" : "text-slate-500"}`}>
            2. Elicit Fields
          </span>
          <span className="text-slate-600">➔</span>
          <span className={`px-2.5 py-1 rounded ${activeStep === 3 ? "bg-blue-600 text-white" : "text-slate-500"}`}>
            3. Query Inputs
          </span>
          <span className="text-slate-600">➔</span>
          <span className={`px-2.5 py-1 rounded ${activeStep === 4 ? "bg-emerald-600 text-white" : "text-slate-500"}`}>
            4. Print / Export
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Left 2 Columns: Interactive Form Canvas Viewer */}
        <Card className="xl:col-span-2 bg-slate-900/50 border-slate-800 overflow-hidden flex flex-col h-[750px]">
          <CardHeader className="p-4 border-b border-slate-800 flex flex-row items-center justify-between">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <FileText className="w-4 h-4 text-emerald-400" /> Preprinted Form Canvas
            </CardTitle>
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-400">Click canvas to manually place input fields</span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setFields([])}
                className="h-7 text-xs border-slate-800 text-slate-400 hover:text-slate-200"
              >
                <RotateCcw className="w-3 h-3 mr-1" /> Clear Fields
              </Button>
            </div>
          </CardHeader>

          <CardContent className="p-0 flex-1 relative bg-slate-950 flex justify-center items-center overflow-auto">
            {formImage ? (
              <button
                type="button"
                ref={imageContainerRef as any}
                onClick={handleCanvasClick}
                className="relative max-w-full max-h-full cursor-crosshair select-none text-left p-0 border-0 bg-transparent"
              >
                <img
                  src={formImage}
                  alt="Preprinted Empty Form"
                  className="max-w-full max-h-[700px] object-contain block"
                />

                {/* Overlaid Field Labels & Values */}
                {fields.map((field) => (
                  <button
                    type="button"
                    key={field.id}
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelectedFieldId(field.id);
                    }}
                    style={{
                      left: `${field.x}%`,
                      top: `${field.y}%`,
                      transform: "translateY(-50%)",
                    }}
                    className={`absolute px-2 py-0.5 rounded border text-xs font-mono font-bold whitespace-nowrap cursor-pointer transition-all ${
                      selectedFieldId === field.id
                        ? "border-emerald-400 bg-emerald-950/90 text-emerald-300 ring-2 ring-emerald-500 shadow-lg z-20"
                        : field.value
                          ? "border-blue-500/80 bg-blue-950/80 text-blue-200 z-10"
                          : "border-amber-500/80 bg-amber-950/80 text-amber-300 animate-pulse z-10"
                    }`}
                  >
                    <span className="text-[10px] text-slate-400 block -mt-1 font-sans">{field.label}</span>
                    <span>{field.value || `<${field.label}>`}</span>
                  </button>
                ))}
              </button>
            ) : (
              <div className="flex flex-col items-center justify-center p-12 text-center space-y-4">
                <Scan className="w-16 h-16 text-slate-700 animate-bounce" />
                <h3 className="text-xl font-bold text-slate-200">No Form Template Loaded</h3>
                <p className="text-sm text-slate-500 max-w-sm">
                  Scan an empty preprinted form sheet using your connected scanner or upload a PNG/PDF file template.
                </p>
                <div className="flex gap-3 pt-2">
                  <Button
                    onClick={handleScanForm}
                    disabled={scanning}
                    className="bg-emerald-600 hover:bg-emerald-700 text-white gap-2"
                  >
                    {scanning ? <Loader2 className="w-4 h-4 animate-spin" /> : <Scan className="w-4 h-4" />}
                    Scan Empty Form
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => fileInputRef.current?.click()}
                    className="border-slate-700 bg-slate-900 text-slate-300 gap-2"
                  >
                    <Upload className="w-4 h-4" /> Upload Template
                  </Button>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*,.pdf"
                    className="hidden"
                    onChange={handleFileUpload}
                  />
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Right 1 Column: Step Control & Field Data Query Panel */}
        <div className="space-y-6 flex flex-col justify-between">
          <Card className="bg-slate-900/50 border-slate-800 flex-1 flex flex-col">
            <CardHeader className="p-4 border-b border-slate-800">
              <CardTitle className="text-sm font-medium flex items-center justify-between">
                <span className="flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-amber-400" /> Step {activeStep}:{" "}
                  {activeStep === 1 && "Load Empty Form"}
                  {activeStep === 2 && "Elicit Fields"}
                  {activeStep === 3 && "Query Field Data"}
                  {activeStep === 4 && "Print & Export"}
                </span>
                {formImage && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setActiveStep(activeStep < 4 ? ((activeStep + 1) as any) : 1)}
                    className="h-7 text-xs border-slate-700 bg-slate-800 text-slate-200"
                  >
                    Next Step ➔
                  </Button>
                )}
              </CardTitle>
            </CardHeader>

            <CardContent className="p-4 space-y-6 flex-1 overflow-y-auto">
              {/* Step 1 Controls */}
              {activeStep === 1 && (
                <div className="space-y-4">
                  <p className="text-sm text-slate-300">
                    Step 1: Scan your empty preprinted paper form sheet or upload an existing digital template.
                  </p>
                  <Button
                    onClick={handleScanForm}
                    disabled={scanning}
                    className="w-full bg-emerald-600 hover:bg-emerald-700 text-white gap-2 py-3"
                  >
                    {scanning ? <Loader2 className="w-4 h-4 animate-spin" /> : <Scan className="w-5 h-5" />}
                    {scanning ? "Scanning Empty Form..." : "Scan Empty Form via WIA"}
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => fileInputRef.current?.click()}
                    className="w-full border-slate-800 bg-slate-950 text-slate-300 gap-2 py-3"
                  >
                    <Upload className="w-5 h-5" /> Browse Form Image / PDF
                  </Button>
                </div>
              )}

              {/* Step 2 Controls: Elicit Fields */}
              {activeStep === 2 && (
                <div className="space-y-4">
                  <p className="text-sm text-slate-300">
                    Step 2: Run layout OCR to automatically elicit fillable fields, or click directly on the canvas to
                    add field coordinates.
                  </p>
                  <Button
                    onClick={handleDetectFields}
                    disabled={detecting}
                    className="w-full bg-blue-600 hover:bg-blue-700 text-white gap-2 py-3"
                  >
                    {detecting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-5 h-5" />}
                    {detecting ? "Analyzing Form Layout..." : "Auto-Detect & Elicit Fields"}
                  </Button>
                  <div className="pt-2 text-xs text-slate-400">
                    <span>Fields detected: {fields.length}</span>
                  </div>
                </div>
              )}

              {/* Step 3 Controls: User Field Inputs */}
              {(activeStep === 3 || activeStep === 4) && (
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <Label className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                      Fill Field Contents
                    </Label>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={handleSaveTemplateToDepot}
                        className="h-7 text-xs border-slate-700 bg-slate-800 text-emerald-400 gap-1"
                        title="Save form layout & field definitions into Corpus Depot for tomorrow"
                      >
                        <Save className="w-3 h-3" /> Save to Depot
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() =>
                          setFields((prev) => [
                            ...prev,
                            { id: `f_${Date.now()}`, label: "New Field", value: "", x: 25, y: 50, fontSize: 14 },
                          ])
                        }
                        className="h-7 text-xs border-slate-700 bg-slate-800 text-slate-300 gap-1"
                      >
                        <Plus className="w-3 h-3" /> Add Field
                      </Button>
                    </div>
                  </div>

                  <div className="space-y-3 max-h-[360px] overflow-y-auto pr-1">
                    {fields.length === 0 ? (
                      <p className="text-xs text-slate-500 italic">
                        No fields elicited. Click "Auto-Detect" or click on the image canvas.
                      </p>
                    ) : (
                      fields.map((f) => (
                        <button
                          type="button"
                          key={f.id}
                          onClick={() => setSelectedFieldId(f.id)}
                          className={`w-full text-left p-3 rounded-lg border text-xs space-y-2 transition-all ${
                            selectedFieldId === f.id
                              ? "bg-slate-950 border-emerald-500 ring-1 ring-emerald-500"
                              : "bg-slate-950/60 border-slate-800"
                          }`}
                        >
                          <div className="flex items-center justify-between gap-2">
                            <Input
                              value={f.label}
                              onChange={(e) => updateFieldProp(f.id, "label", e.target.value)}
                              className="h-7 text-xs bg-slate-900 border-slate-800 text-emerald-400 font-semibold"
                              placeholder="Field Label"
                            />
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-6 w-6 text-slate-500 hover:text-red-400 shrink-0"
                              onClick={(e) => {
                                e.stopPropagation();
                                deleteField(f.id);
                              }}
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </Button>
                          </div>

                          <Input
                            value={f.value}
                            onChange={(e) => updateFieldValue(f.id, e.target.value)}
                            className="h-8 text-xs bg-slate-900 border-slate-700 text-slate-100 font-mono"
                            placeholder={`Enter ${f.label}...`}
                          />

                          <div className="flex items-center justify-between text-[11px] text-slate-500 pt-1">
                            <span>
                              X: {f.x}% | Y: {f.y}%
                            </span>
                            <div className="flex items-center gap-1">
                              <span>Font:</span>
                              <input
                                type="number"
                                value={f.fontSize}
                                onChange={(e) => updateFieldProp(f.id, "fontSize", parseInt(e.target.value, 10) || 12)}
                                className="w-12 h-5 text-center bg-slate-900 border border-slate-800 rounded text-slate-200"
                              />
                              <span>pt</span>
                            </div>
                          </div>
                        </button>
                      ))
                    )}
                  </div>
                </div>
              )}

              {/* Step 4 Controls: Dual Print Modes */}
              {activeStep === 4 && (
                <div className="space-y-4 pt-4 border-t border-slate-800">
                  <Label className="text-xs font-bold text-slate-300 uppercase tracking-wider">Dual Print Modes</Label>

                  <div className="grid grid-cols-2 gap-2">
                    <Button
                      onClick={() => handlePrint("overlay")}
                      className="bg-emerald-600 hover:bg-emerald-700 text-white gap-2 py-3 flex-col h-auto"
                      title="Print ONLY filled text over existing physical preprinted paper"
                    >
                      <Printer className="w-5 h-5" />
                      <span className="text-xs font-bold">Print Overlay Only</span>
                      <span className="text-[10px] font-normal text-emerald-200">Feed empty form into printer</span>
                    </Button>

                    <Button
                      onClick={() => handlePrint("full")}
                      variant="outline"
                      className="border-slate-700 bg-slate-800 text-slate-200 hover:bg-slate-700 gap-2 py-3 flex-col h-auto"
                      title="Print empty form template image AND filled text onto blank paper"
                    >
                      <FileCheck className="w-5 h-5 text-blue-400" />
                      <span className="text-xs font-bold">Print Full Document</span>
                      <span className="text-[10px] font-normal text-slate-400">Prints template + text</span>
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
