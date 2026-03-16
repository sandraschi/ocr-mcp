import React, { useState } from 'react'
import { FileDown, FileText, Table, FileArchive, Clock, Search, Download, Trash2, Filter, MoreVertical } from 'lucide-react'
import { Button } from '../components/ui/Button'
import { cn } from '../lib/utils'
import { useJobStore, Job } from '../stores/jobStore'

interface ExportFormat {
    id: string
    name: string
    extension: string
    icon: React.ReactNode
}

const EXPORT_FORMATS: ExportFormat[] = [
    { id: 'pdf', name: 'Searchable PDF', extension: '.pdf', icon: <FileText className="w-4 h-4 text-red-500" /> },
    { id: 'docx', name: 'Word Document', extension: '.docx', icon: <FileText className="w-4 h-4 text-blue-500" /> },
    { id: 'xlsx', name: 'Excel Spreadsheet', extension: '.xlsx', icon: <Table className="w-4 h-4 text-green-500" /> },
    { id: 'json', name: 'Structured JSON', extension: '.json', icon: <FileArchive className="w-4 h-4 text-yellow-600" /> },
    { id: 'txt', name: 'Plain Text', extension: '.txt', icon: <FileText className="w-4 h-4 text-gray-500" /> },
]

export function ExportPage() {
    const { jobs, removeJob } = useJobStore()
    const [searchQuery, setSearchQuery] = useState('')
    const [selectedFormat, setSelectedFormat] = useState<string>('pdf')
    const [isExportingAll, setIsExportingAll] = useState(false)

    const completedJobs = jobs.filter(job => job.status === 'completed')
    const filteredJobs = completedJobs.filter(job =>
        job.filename.toLowerCase().includes(searchQuery.toLowerCase())
    )

    const handleDownload = (job: Job, formatId: string) => {
        console.log(`Downloading job ${job.id} in format ${formatId}`)
        // In a real app, this would trigger a download from the backend
    }

    const handleExportAll = async () => {
        setIsExportingAll(true)
        await new Promise(resolve => setTimeout(resolve, 2000))
        setIsExportingAll(false)
        console.log('Exporting all jobs in format:', selectedFormat)
    }

    const formatDate = (date: Date) => {
        return new Intl.DateTimeFormat('en-US', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        }).format(new Date(date))
    }

    return (
        <div className="p-6 max-w-6xl mx-auto">
            <div className="mb-8 border-b border-white/5 pb-8 flex flex-col md:flex-row md:items-end md:justify-between gap-6">
                <div>
                    <h1 className="text-3xl font-bold mb-2 flex items-center gap-2">
                        <FileDown className="w-8 h-8 text-primary" />
                        Export & Download
                    </h1>
                    <p className="text-muted-foreground max-w-2xl">
                        Access and manage your processed documents. Export them in various professional formats or perform batch downloads of all results.
                    </p>
                </div>

                <div className="flex gap-3">
                    <div className="flex bg-muted/30 p-1 rounded-lg border border-white/5">
                        {EXPORT_FORMATS.map(f => (
                            <button
                                key={f.id}
                                onClick={() => setSelectedFormat(f.id)}
                                className={cn(
                                    "px-3 py-1.5 rounded-md text-xs font-medium transition-all",
                                    selectedFormat === f.id
                                        ? "bg-primary text-primary-foreground shadow-sm"
                                        : "hover:bg-white/5 text-muted-foreground"
                                )}
                            >
                                {f.extension.toUpperCase()}
                            </button>
                        ))}
                    </div>
                    <Button
                        disabled={completedJobs.length === 0 || isExportingAll}
                        className="gap-2 shadow-lg shadow-primary/20"
                        onClick={handleExportAll}
                    >
                        {isExportingAll ? (
                            <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        ) : (
                            <Download className="w-4 h-4" />
                        )}
                        Batch Export {selectedFormat.toUpperCase()}
                    </Button>
                </div>
            </div>

            {completedJobs.length === 0 ? (
                <div className="glass rounded-2xl p-20 text-center border border-white/5">
                    <div className="w-20 h-20 bg-muted/30 rounded-full flex items-center justify-center mx-auto mb-6">
                        <Search className="w-10 h-10 text-muted-foreground" />
                    </div>
                    <h3 className="text-xl font-semibold mb-2">No documents ready for export</h3>
                    <p className="text-muted-foreground max-w-md mx-auto mb-8">
                        Complete a document scan or upload and process some files to see them here.
                    </p>
                    <div className="flex justify-center gap-4">
                        <Button variant="outline" asChild>
                            <a href="/upload">Upload Files</a>
                        </Button>
                        <Button asChild>
                            <a href="/scanner">Start Scanning</a>
                        </Button>
                    </div>
                </div>
            ) : (
                <div className="space-y-6">
                    <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
                        <div className="relative w-full md:w-96">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                            <input
                                type="text"
                                placeholder="Search processed documents..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="w-full pl-10 pr-4 py-2 bg-muted/30 border border-white/5 rounded-xl focus:ring-2 focus:ring-primary/40 focus:outline-none transition-all"
                            />
                        </div>

                        <div className="flex items-center gap-3 text-sm text-muted-foreground">
                            <Filter className="w-4 h-4" />
                            <span>Showing {filteredJobs.length} documents</span>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {filteredJobs.map((job) => (
                            <div
                                key={job.id}
                                className="glass group relative p-5 rounded-2xl border border-white/5 hover:border-primary/30 transition-all hover:translate-y-[-2px] hover:shadow-xl hover:shadow-primary/5"
                            >
                                <div className="flex items-start justify-between mb-4">
                                    <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center text-primary group-hover:scale-110 transition-transform">
                                        <FileText className="w-6 h-6" />
                                    </div>
                                    <div className="flex gap-1">
                                        <Button variant="ghost" size="sm" className="w-8 h-8 p-0 opacity-0 group-hover:opacity-100 transition-opacity">
                                            <MoreVertical className="w-4 h-4" />
                                        </Button>
                                        <Button
                                            variant="ghost"
                                            size="sm"
                                            onClick={() => removeJob(job.id)}
                                            className="w-8 h-8 p-0 text-muted-foreground hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity"
                                        >
                                            <Trash2 className="w-4 h-4" />
                                        </Button>
                                    </div>
                                </div>

                                <div className="mb-4">
                                    <h4 className="font-bold truncate text-lg" title={job.filename}>{job.filename}</h4>
                                    <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
                                        <Clock className="w-3.5 h-3.5" />
                                        <span>{formatDate(job.createdAt)}</span>
                                    </div>
                                </div>

                                <div className="grid grid-cols-2 gap-2 mt-4">
                                    {EXPORT_FORMATS.slice(0, 4).map(format => (
                                        <button
                                            key={format.id}
                                            onClick={() => handleDownload(job, format.id)}
                                            className="flex items-center gap-2 px-3 py-2 rounded-lg bg-muted/20 border border-white/5 hover:border-primary/20 hover:bg-primary/5 transition-all text-xs font-medium"
                                        >
                                            {format.icon}
                                            {format.extension.toUpperCase()}
                                        </button>
                                    ))}
                                </div>

                                <Button className="w-full mt-4 gap-2 py-5" variant="secondary" onClick={() => handleDownload(job, 'pdf')}>
                                    <Download className="w-4 h-4" />
                                    Quick Download (PDF)
                                </Button>
                            </div>
                        ))}
                    </div>

                    {filteredJobs.length === 0 && searchQuery && (
                        <div className="p-20 text-center opacity-50">
                            <Search className="w-12 h-12 mx-auto mb-4" />
                            <p>No documents found matching "{searchQuery}"</p>
                        </div>
                    )}
                </div>
            )}
        </div>
    )
}
