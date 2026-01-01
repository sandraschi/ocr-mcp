import React, { useState } from 'react'
import { FileDown, FileText, Table, FileArchive, CheckCircle, ArrowRight, Settings2 } from 'lucide-react'
import { Button } from '../components/ui/Button'
import { cn } from '../lib/utils'

interface ExportFormat {
    id: string
    name: string
    extension: string
    icon: React.ReactNode
    description: string
}

const FORMATS: ExportFormat[] = [
    { id: 'pdf', name: 'Searchable PDF', extension: '.pdf', icon: <FileText className="w-8 h-8 text-red-500" />, description: 'High-quality PDF with embedded text layer for searching.' },
    { id: 'docx', name: 'Word Document', extension: '.docx', icon: <FileText className="w-8 h-8 text-blue-500" />, description: 'Editable Word file preserving layout and formatting.' },
    { id: 'xlsx', name: 'Excel Spreadsheet', extension: '.xlsx', icon: <Table className="w-8 h-8 text-green-500" />, description: 'Extracted tables exported into a structured workbook.' },
    { id: 'json', name: 'Structured JSON', extension: '.json', icon: <FileArchive className="w-8 h-8 text-yellow-600" />, description: 'Full document metadata and extraction in machine-readable format.' },
]

export function ConversionPage() {
    const [selectedFormat, setSelectedFormat] = useState<string | null>(null)
    const [isExporting, setIsExporting] = useState(false)
    const [exportComplete, setExportComplete] = useState(false)

    const handleExport = async () => {
        if (!selectedFormat) return
        setIsExporting(true)
        setExportComplete(false)

        // Simulate export process
        await new Promise(resolve => setTimeout(resolve, 2000))

        setIsExporting(false)
        setExportComplete(true)
    }

    return (
        <div className="p-6 max-w-6xl mx-auto">
            <div className="mb-8">
                <h1 className="text-3xl font-bold mb-2">Format Conversion</h1>
                <p className="text-muted-foreground">
                    Convert your OCR results into professional document formats for editing, sharing, or data analysis.
                </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {/* Format Selection */}
                <div className="space-y-6">
                    <h2 className="text-xl font-semibold flex items-center gap-2">
                        <Settings2 className="w-5 h-5 text-primary" />
                        Select Output Format
                    </h2>
                    <div className="grid grid-cols-1 gap-4">
                        {FORMATS.map((format) => (
                            <button
                                key={format.id}
                                onClick={() => setSelectedFormat(format.id)}
                                className={cn(
                                    'flex items-center gap-4 p-4 rounded-xl border-2 transition-all text-left glass',
                                    selectedFormat === format.id
                                        ? 'border-primary ring-2 ring-primary/20 bg-primary/5'
                                        : 'border-border hover:border-primary/50'
                                )}
                            >
                                <div className="p-3 bg-card rounded-lg shadow-sm">
                                    {format.icon}
                                </div>
                                <div className="flex-1">
                                    <div className="flex items-center justify-between">
                                        <h4 className="font-bold">{format.name}</h4>
                                        <span className="text-xs font-mono text-muted-foreground">{format.extension}</span>
                                    </div>
                                    <p className="text-sm text-muted-foreground mt-1 line-clamp-2">{format.description}</p>
                                </div>
                                <div className={cn(
                                    'w-6 h-6 rounded-full border-2 flex items-center justify-center transition-colors',
                                    selectedFormat === format.id ? 'border-primary bg-primary text-primary-foreground' : 'border-muted'
                                )}>
                                    {selectedFormat === format.id && <CheckCircle className="w-4 h-4" />}
                                </div>
                            </button>
                        ))}
                    </div>
                </div>

                {/* Execution Area */}
                <div className="space-y-6">
                    <h2 className="text-xl font-semibold flex items-center gap-2">
                        <FileDown className="w-5 h-5 text-primary" />
                        Export Configuration
                    </h2>

                    <div className="glass rounded-xl p-6 min-h-[400px] flex flex-col">
                        {!selectedFormat ? (
                            <div className="flex-1 flex flex-col items-center justify-center text-center opacity-50">
                                <Settings2 className="w-16 h-16 mb-4 text-muted-foreground" />
                                <h3 className="text-lg font-medium">No Format Selected</h3>
                                <p className="text-sm text-muted-foreground max-w-[250px]">Choose a format from the list to configure your export options.</p>
                            </div>
                        ) : exportComplete ? (
                            <div className="flex-1 flex flex-col items-center justify-center text-center animate-in zoom-in-95 duration-300">
                                <div className="w-20 h-20 bg-green-100 dark:bg-green-950/30 rounded-full flex items-center justify-center mb-4">
                                    <CheckCircle className="w-10 h-10 text-green-500" />
                                </div>
                                <h3 className="text-xl font-bold mb-2">Export Complete!</h3>
                                <p className="text-muted-foreground mb-6">Your document has been successfully converted and is ready for download.</p>
                                <Button className="w-full gap-2 py-6 text-lg" variant="default">
                                    <FileDown className="w-5 h-5" />
                                    Download {FORMATS.find(f => f.id === selectedFormat)?.extension}
                                </Button>
                                <Button
                                    variant="ghost"
                                    className="mt-4 text-xs text-muted-foreground"
                                    onClick={() => setExportComplete(false)}
                                >
                                    Export another format
                                </Button>
                            </div>
                        ) : (
                            <div className="flex-1 flex flex-col space-y-6 animate-in fade-in duration-300">
                                <div className="p-4 bg-primary/5 rounded-lg border border-primary/10">
                                    <h4 className="text-sm font-semibold mb-2 flex items-center gap-2">
                                        <CheckCircle className="w-4 h-4 text-primary" />
                                        Source Content Ready
                                    </h4>
                                    <p className="text-xs text-muted-foreground">The extracted text and data from your recent analysis will be used for conversion.</p>
                                </div>

                                <div className="flex-1 space-y-4">
                                    <div className="flex items-center justify-between p-3 bg-muted/30 rounded-lg">
                                        <span className="text-sm">Language Preservation</span>
                                        <span className="text-xs px-2 py-0.5 bg-primary/10 text-primary rounded ring-1 ring-primary/20">English</span>
                                    </div>
                                    <div className="flex items-center justify-between p-3 bg-muted/30 rounded-lg">
                                        <span className="text-sm">Layout Reconstruction</span>
                                        <span className="text-xs px-2 py-0.5 bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300 rounded ring-1 ring-green-500/20">Enabled</span>
                                    </div>
                                    <div className="flex items-center justify-between p-3 bg-muted/30 rounded-lg">
                                        <span className="text-sm">Table Detection</span>
                                        <span className="text-xs px-2 py-0.5 bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300 rounded ring-1 ring-green-500/20">Found (3)</span>
                                    </div>
                                </div>

                                <Button
                                    onClick={handleExport}
                                    disabled={isExporting}
                                    className="w-full py-6 text-lg gap-3"
                                >
                                    {isExporting ? (
                                        <>
                                            <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                                            Converting...
                                        </>
                                    ) : (
                                        <>
                                            Start Conversion
                                            <ArrowRight className="w-5 h-5" />
                                        </>
                                    )}
                                </Button>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    )
}
