import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { BookOpen, HelpCircle } from "lucide-react";

export function Help() {
    return (
        <div className="space-y-6 max-w-4xl mx-auto pb-12">
            <h1 className="text-3xl font-bold tracking-tight text-slate-100 flex items-center gap-3">
                <HelpCircle className="w-8 h-8 text-blue-500" />
                Help & Documentation
            </h1>

            <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-xl">
                <CardHeader>
                    <CardTitle className="text-slate-100 flex items-center gap-2">
                        <BookOpen className="w-5 h-5 text-emerald-400" />
                        Getting Started Guide
                    </CardTitle>
                    <CardDescription className="text-slate-400">Everything you need to know to use OCR-MCP.</CardDescription>
                </CardHeader>
                <CardContent className="prose prose-invert prose-slate max-w-none">
                    <h3>What is OCR-MCP?</h3>
                    <p>
                        OCR-MCP is a fully-featured interface for managing Optical Character Recognition pipelines. It supports local scanning, batch uploading, auto-optimization of image quality, and exporting to multiple file formats like JSON, XML, and CSV.
                    </p>

                    <hr className="border-slate-800 my-6" />

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                        <div>
                            <h4 className="text-blue-400">1. Importing Documents</h4>
                            <p className="text-sm text-slate-300">
                                Use the <strong>Import</strong> tab to upload a file directly from your computer. Once uploaded, a Job ID is issued. Use this Job ID in the Editor tab to review results.
                            </p>
                        </div>

                        <div>
                            <h4 className="text-blue-400">2. Using Scanners</h4>
                            <p className="text-sm text-slate-300">
                                Use the <strong>Scanner Control</strong> tab to trigger flatbed or ADF scanners connected to the host machine. Ensure the backend properly initializes the hardware via WIA/TWAIN bridges.
                            </p>
                        </div>

                        <div>
                            <h4 className="text-blue-400">3. Processing & Pipelines</h4>
                            <p className="text-sm text-slate-300">
                                Need higher quality? The <strong>Process</strong> tab allows you to run iterative optimizations. The Quality Focused pipeline repeatedly scans varying contrast/brightness to secure maximum fidelity text extraction.
                            </p>
                        </div>

                        <div>
                            <h4 className="text-blue-400">4. Editor & Exporting</h4>
                            <p className="text-sm text-slate-300">
                                Once OCR is complete, review the text in the <strong>Editor</strong>. Fix any typos or strange characters. Click Export to download the result in your desired structured data format.
                            </p>
                        </div>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
