import React, { useState } from 'react'
import { FileText, Table, Info, Download, Copy, Check } from 'lucide-react'
import { Button } from '../../ui/Button'
import { cn } from '../../../lib/utils'
import { OCRResult, TableData } from '../../../services/api'

interface OCRResultViewerProps {
    result: OCRResult
    className?: string
}

export function OCRResultViewer({ result, className }: OCRResultViewerProps) {
    const [activeTab, setActiveTab] = useState<'text' | 'tables' | 'metadata'>('text')
    const [copied, setCopied] = useState(false)

    const handleCopy = () => {
        navigator.clipboard.writeText(result.text)
        setCopied(true)
        setTimeout(() => setCopied(false), 2000)
    }

    return (
        <div className={cn('glass rounded-xl overflow-hidden flex flex-col', className)}>
            {/* Header */}
            <div className="bg-muted/50 p-4 border-b border-border flex items-center justify-between">
                <div className="flex gap-1">
                    <TabButton
                        active={activeTab === 'text'}
                        onClick={() => setActiveTab('text')}
                        icon={<FileText className="w-4 h-4" />}
                        label="Text"
                    />
                    {result.tables && result.tables.length > 0 && (
                        <TabButton
                            active={activeTab === 'tables'}
                            onClick={() => setActiveTab('tables')}
                            icon={<Table className="w-4 h-4" />}
                            label={`Tables (${result.tables.length})`}
                        />
                    )}
                    <TabButton
                        active={activeTab === 'metadata'}
                        onClick={() => setActiveTab('metadata')}
                        icon={<Info className="w-4 h-4" />}
                        label="Details"
                    />
                </div>

                <div className="flex gap-2">
                    <Button variant="ghost" size="sm" onClick={handleCopy} className="h-8 gap-1.5 text-xs">
                        {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                        {copied ? 'Copied' : 'Copy'}
                    </Button>
                    <Button variant="ghost" size="sm" className="h-8 gap-1.5 text-xs">
                        <Download className="w-3.5 h-3.5" />
                        Export
                    </Button>
                </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-auto p-4 min-h-[300px]">
                {activeTab === 'text' && (
                    <div className="prose prose-sm dark:prose-invert max-w-none">
                        <pre className="whitespace-pre-wrap font-sans text-sm p-0 m-0 bg-transparent border-none">
                            {result.text}
                        </pre>
                    </div>
                )}

                {activeTab === 'tables' && result.tables && (
                    <div className="space-y-8">
                        {result.tables.map((table, idx) => (
                            <TableView key={idx} table={table} index={idx + 1} />
                        ))}
                    </div>
                )}

                {activeTab === 'metadata' && (
                    <div className="space-y-6">
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            <MetadataItem label="Confidence" value={`${(result.confidence * 100).toFixed(1)}%`} />
                            <MetadataItem label="Language" value={result.language.toUpperCase()} />
                            <MetadataItem label="Words" value={result.text.split(/\s+/).length.toString()} />
                            <MetadataItem label="Characters" value={result.text.length.toString()} />
                        </div>

                        <div className="border-t border-border pt-4">
                            <h4 className="text-sm font-semibold mb-3">Backend Metadata</h4>
                            <div className="bg-muted/30 rounded-lg p-3 overflow-auto max-h-[200px]">
                                <pre className="text-xs text-muted-foreground whitespace-pre-wrap">
                                    {JSON.stringify(result.metadata, null, 2)}
                                </pre>
                            </div>
                        </div>
                    </div>
                )}
            </div>

            {/* Footer */}
            <div className="bg-muted/30 px-4 py-2 border-t border-border flex items-center justify-between text-[10px] text-muted-foreground">
                <div className="flex items-center gap-3">
                    <span>Processed with <strong>{result.metadata.backend || 'auto'}</strong></span>
                    <span>•</span>
                    <span>Language: {result.language}</span>
                </div>
                <div>ID: {result.metadata.request_id || 'N/A'}</div>
            </div>
        </div>
    )
}

function TabButton({ active, onClick, icon, label }: { active: boolean; onClick: () => void; icon: React.ReactNode; label: string }) {
    return (
        <button
            onClick={onClick}
            className={cn(
                'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all',
                active
                    ? 'bg-primary text-primary-foreground shadow-sm scale-105'
                    : 'text-muted-foreground hover:text-foreground hover:bg-muted'
            )}
        >
            {icon}
            <span>{label}</span>
        </button>
    )
}

function TableView({ table, index }: { table: TableData; index: number }) {
    return (
        <div className="space-y-3">
            <div className="flex items-center gap-2">
                <div className="bg-primary/10 text-primary p-1 rounded">
                    <Table className="w-3.5 h-3.5" />
                </div>
                <h4 className="text-sm font-semibold">Table {index} ({table.rows}x{table.columns})</h4>
            </div>
            <div className="border border-border rounded-lg overflow-hidden overflow-x-auto">
                <table className="w-full text-xs text-left border-collapse">
                    <thead>
                        <tr className="bg-muted/50">
                            {table.headers.map((h, i) => (
                                <th key={i} className="px-3 py-2 border-b border-border font-semibold">{h}</th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {table.data.map((row, ri) => (
                            <tr key={ri} className="border-b border-border last:border-0 hover:bg-muted/20">
                                {row.map((cell, ci) => (
                                    <td key={ci} className="px-3 py-2">{cell}</td>
                                ))}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    )
}

function MetadataItem({ label, value }: { label: string; value: string }) {
    return (
        <div className="space-y-1">
            <span className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold">
                {label}
            </span>
            <div className="text-sm font-medium truncate">
                {value}
            </div>
        </div>
    )
}
