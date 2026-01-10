import React, { useCallback, useState, useEffect } from 'react'
import { Upload, FileText, X, Play, Pause, CheckCircle, AlertCircle } from 'lucide-react'
import { Button } from '../components/ui/Button'
import { cn } from '../lib/utils'
import { useJobStore } from '../stores/jobStore'

interface BatchFile {
  id: string
  file: File
  name: string
  size: number
  status: 'queued' | 'processing' | 'completed' | 'failed'
  progress: number
  error?: string
}

export function BatchPage() {
  const { jobs, processBatch, loading: isProcessing, pollJobStatus, activeJobId } = useJobStore()
  const [files, setFiles] = useState<BatchFile[]>([])
  const [isDragOver, setIsDragOver] = useState(false)

  // Sync store jobs with local files for progress display
  useEffect(() => {
    if (jobs.length > 0) {
      setFiles(prev => prev.map(f => {
        const matchingJob = jobs.find(j => j.filename === f.name)
        if (matchingJob) {
          return {
            ...f,
            status: matchingJob.status as any,
            progress: matchingJob.progress,
            error: matchingJob.error
          }
        }
        return f
      }))
    }
  }, [jobs])

  // Poll for the active job if there is one
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (activeJobId && isProcessing) {
      interval = setInterval(() => {
        pollJobStatus(activeJobId)
      }, 2000)
    }
    return () => clearInterval(interval)
  }, [activeJobId, isProcessing, pollJobStatus])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)

    const droppedFiles = Array.from(e.dataTransfer.files)
    addFilesToBatch(droppedFiles)
  }, [])

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = Array.from(e.target.files || [])
    addFilesToBatch(selectedFiles)
  }, [])

  const addFilesToBatch = (newFiles: File[]) => {
    const batchFiles: BatchFile[] = newFiles.map(file => ({
      id: Math.random().toString(36).substring(7),
      file,
      name: file.name,
      size: file.size,
      status: 'queued',
      progress: 0,
    }))

    setFiles(prev => [...prev, ...batchFiles])
  }

  const removeFile = useCallback((fileId: string) => {
    setFiles(prev => prev.filter(f => f.id !== fileId))
  }, [])

  const clearAllFiles = useCallback(() => {
    setFiles([])
  }, [])

  const startBatchProcessing = useCallback(async () => {
    const queuedFiles = files.filter(f => f.status === 'queued').map(f => f.file)
    if (queuedFiles.length === 0) return

    try {
      await processBatch(queuedFiles)
    } catch (error) {
      console.error('Batch processing failed:', error)
    }
  }, [files, processBatch])

  const getStatusIcon = (status: BatchFile['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />
      case 'failed':
        return <AlertCircle className="w-5 h-5 text-red-500" />
      case 'processing':
        return <div className="w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin" />
      default:
        return <div className="w-5 h-5 border-2 border-muted-foreground border-t-transparent rounded-full" />
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
  }

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Batch Processing</h1>
        <p className="text-muted-foreground">
          Process multiple documents simultaneously with advanced batch operations and progress tracking.
        </p>
      </div>

      {/* Upload Area */}
      <div
        className={cn(
          'glass rounded-xl p-12 text-center transition-all duration-300 border-2 border-dashed group mb-10',
          isDragOver
            ? 'border-primary bg-primary/10 scale-[1.01]'
            : 'border-white/10 hover:border-primary/40 hover:bg-white/5'
        )}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <div className="w-16 h-16 mx-auto mb-6 bg-primary/20 rounded-2xl flex items-center justify-center group-hover:scale-110 transition-transform">
          <Upload className="w-8 h-8 text-primary" />
        </div>
        <h3 className="text-xl font-semibold mb-2">Drop files here for batch processing</h3>
        <p className="text-muted-foreground mb-6">
          or click to browse multiple files (PDF, images up to 50MB each)
        </p>
        <input
          type="file"
          multiple
          accept=".pdf,image/*"
          onChange={handleFileSelect}
          className="hidden"
          id="batch-file-input"
        />
        <Button asChild disabled={isProcessing} size="lg" className="px-8 shadow-lg shadow-primary/20">
          <label htmlFor="batch-file-input" className="cursor-pointer">
            Choose Files
          </label>
        </Button>
      </div>

      {/* File List */}
      {files.length > 0 && (
        <div className="mb-10">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-medium flex items-center gap-2">
              <span className="w-1.5 h-1.5 bg-primary rounded-full"></span>
              Batch Queue ({files.length} files)
            </h3>
            <Button variant="outline" onClick={clearAllFiles} disabled={isProcessing} size="sm">
              Clear All
            </Button>
          </div>

          <div className="space-y-3 max-h-[500px] overflow-y-auto pr-2 custom-scrollbar">
            {files.map((file) => (
              <div
                key={file.id}
                className="flex items-center gap-4 p-4 glass rounded-xl border border-white/5 group transition-all"
              >
                <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-white/5">
                  {getStatusIcon(file.status)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3">
                    <FileText className="w-5 h-5 text-muted-foreground shrink-0" />
                    <div className="truncate">
                      <p className="font-medium truncate">{file.name}</p>
                      <p className="text-xs text-muted-foreground uppercase tracking-wider">
                        {formatFileSize(file.size)}
                        {file.error && (
                          <span className="text-red-400 ml-2">• {file.error}</span>
                        )}
                      </p>
                    </div>
                  </div>

                  {file.status === 'processing' && (
                    <div className="mt-3">
                      <div className="w-full bg-white/5 rounded-full h-1.5 overflow-hidden">
                        <div
                          className="bg-primary h-full rounded-full transition-all duration-300 shadow-[0_0_8px_rgba(139,92,246,0.5)]"
                          style={{ width: `${file.progress}%` }}
                        />
                      </div>
                      <p className="text-[10px] text-muted-foreground mt-1 text-right font-medium">
                        {file.progress}%
                      </p>
                    </div>
                  )}
                </div>

                {!isProcessing && file.status !== 'processing' && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => removeFile(file.id)}
                    className="w-8 h-8 p-0 hover:bg-destructive/10 hover:text-destructive"
                  >
                    <X className="w-4 h-4" />
                  </Button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Controls */}
      {files.length > 0 && (
        <div className="flex gap-3">
          <Button
            onClick={startBatchProcessing}
            disabled={isProcessing || files.every(f => f.status === 'completed' || f.status === 'failed')}
            className="gap-2"
          >
            <Play className="w-4 h-4" />
            {isProcessing ? 'Processing...' : 'Start Batch Processing'}
          </Button>

          {isProcessing && (
            <Button variant="outline" disabled className="gap-2">
              <Pause className="w-4 h-4" />
              Processing...
            </Button>
          )}
        </div>
      )}

      {/* Statistics */}
      {files.length > 0 && (
        <div className="mt-8 grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="glass rounded-lg p-4 text-center">
            <div className="text-2xl font-bold">{files.length}</div>
            <div className="text-sm text-muted-foreground">Total Files</div>
          </div>
          <div className="glass rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-green-600">
              {files.filter(f => f.status === 'completed').length}
            </div>
            <div className="text-sm text-muted-foreground">Completed</div>
          </div>
          <div className="glass rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-blue-600">
              {files.filter(f => f.status === 'processing').length}
            </div>
            <div className="text-sm text-muted-foreground">Processing</div>
          </div>
          <div className="glass rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-red-600">
              {files.filter(f => f.status === 'failed').length}
            </div>
            <div className="text-sm text-muted-foreground">Failed</div>
          </div>
        </div>
      )}
    </div>
  )
}