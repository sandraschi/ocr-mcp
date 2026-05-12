import { useState, useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiService } from '@services/api'
import {
  Cpu, Download, RotateCw, CheckCircle, XCircle, AlertTriangle,
  Clock, HardDrive, Zap, BarChart3, Activity
} from 'lucide-react'
import { cn } from '../lib/utils'

interface BackendInfo {
  name: string
  description: string
  model_size: string
  available: boolean
  capabilities?: Record<string, any>
  download?: {
    status: string
    progress: number
    job_id?: string
    error?: string
  }
  error?: string
}

interface ModelStatus {
  backends: Record<string, BackendInfo>
  available_count: number
  total_count: number
}

export function BackendsPage() {
  const [downloadingBackend, setDownloadingBackend] = useState<string | null>(null)

  const { data, refetch, isFetching, isError, error } = useQuery<ModelStatus>({
    queryKey: ['modelStatus'],
    queryFn: () => apiService.getModelStatus(),
    retry: 1,
    staleTime: 5000,
    refetchInterval: (query) => {
      const hasDownloading = Object.values(query.state.data?.backends ?? {}).some(
        (b) => b.download?.status === 'downloading'
      )
      return hasDownloading ? 2000 : 30000
    },
  })

  const pollDownload = useCallback(async (backendName: string) => {
    const maxPolls = 120
    for (let i = 0; i < maxPolls; i++) {
      await new Promise((r) => setTimeout(r, 2000))
      try {
        const progress = await apiService.getDownloadProgress(backendName)
        if (progress.status === 'available' || progress.status === 'failed') {
          setDownloadingBackend(null)
          refetch()
          return
        }
      } catch {
        // best effort
      }
    }
    setDownloadingBackend(null)
    refetch()
  }, [refetch])

  const handleDownload = async (name: string) => {
    setDownloadingBackend(name)
    try {
      const res = await apiService.downloadModel(name)
      if (res.status === 'already_available') {
        setDownloadingBackend(null)
        refetch()
        return
      }
      if (res.status === 'downloading' && res.job_id) {
        pollDownload(name)
      }
    } catch (e: any) {
      setDownloadingBackend(null)
    }
  }

  const handleRestart = async () => {
    try {
      await apiService.restartBackend()
      // Wait a moment then refetch
      setTimeout(() => refetch(), 3000)
    } catch (e) {
      // Vite plugin fallback should handle this even when backend is dead
      setTimeout(() => refetch(), 5000)
    }
  }

  const handleProbe = async (name: string) => {
    try {
      await apiService.probeBackend(name)
      refetch()
    } catch (e) {
      // probe error shown elsewhere
    }
  }

  const backends = data?.backends ?? {}
  const list = Object.entries(backends).sort(([, a], [, b]) => {
    if (a.available !== b.available) return a.available ? -1 : 1
    return a.name.localeCompare(b.name)
  })

  const summary = {
    available: data?.available_count ?? 0,
    total: data?.total_count ?? 0,
    ready: list.filter(([, b]) => b.available).length,
    notReady: list.filter(([, b]) => !b.available).length,
  }

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold mb-1">Backends &amp; Models</h1>
        <p className="text-muted-foreground">OCR engine availability, model sizes, and download management</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-4 gap-4">
        <div className="glass rounded-lg p-4">
          <div className="flex items-center gap-2 mb-1">
            <Activity className="w-4 h-4 text-green-500" />
            <span className="text-sm text-muted-foreground">Available</span>
          </div>
          <span className="text-2xl font-bold text-green-500">{summary.available}</span>
          <span className="text-sm text-muted-foreground ml-1">/ {summary.total}</span>
        </div>
        <div className="glass rounded-lg p-4">
          <div className="flex items-center gap-2 mb-1">
            <HardDrive className="w-4 h-4 text-blue-500" />
            <span className="text-sm text-muted-foreground">Ready</span>
          </div>
          <span className="text-2xl font-bold text-blue-500">{summary.ready}</span>
        </div>
        <div className="glass rounded-lg p-4">
          <div className="flex items-center gap-2 mb-1">
            <Clock className="w-4 h-4 text-amber-500" />
            <span className="text-sm text-muted-foreground">Not Installed</span>
          </div>
          <span className="text-2xl font-bold text-amber-500">{summary.notReady}</span>
        </div>
        <div className="glass rounded-lg p-4">
          <div className="flex items-center gap-2 mb-1">
            <Zap className="w-4 h-4 text-purple-500" />
            <span className="text-sm text-muted-foreground">Actions</span>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => refetch()}
              disabled={isFetching}
              className="text-sm text-primary hover:underline"
            >
              {isFetching ? 'Refreshing...' : 'Refresh'}
            </button>
            <span className="text-muted-foreground">|</span>
            <button
              onClick={handleRestart}
              className="text-sm text-amber-500 hover:text-amber-400 hover:underline"
            >
              Restart Backend
            </button>
          </div>
        </div>
      </div>

      {/* Backend List */}
      <div className="space-y-3">
        {list.map(([name, info]) => {
          const dlStatus = info.download?.status
          const dlProgress = info.download?.progress ?? 0
          const isDownloading = dlStatus === 'downloading' || dlStatus === 'verifying'

          return (
            <div
              key={name}
              className={cn(
                'glass rounded-lg p-5 transition-all duration-300',
                info.available && 'border-green-500/30',
                !info.available && !info.error && 'border-amber-500/20',
                info.error && 'border-red-500/20'
              )}
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 mb-2">
                    <div
                      className={cn(
                        'w-3 h-3 rounded-full flex-shrink-0',
                        info.available && 'bg-green-500',
                        isDownloading && 'bg-blue-500 animate-pulse',
                        !info.available && !isDownloading && !info.error && 'bg-amber-500',
                        info.error && 'bg-red-500'
                      )}
                    />
                    <h3 className="font-semibold text-lg">{name}</h3>
                    <span className="text-xs px-2 py-0.5 rounded-full bg-muted text-muted-foreground">
                      {info.model_size}
                    </span>
                    {info.available && (
                      <CheckCircle className="w-4 h-4 text-green-500" />
                    )}
                    {isDownloading && (
                      <RotateCw className="w-4 h-4 text-blue-500 animate-spin" />
                    )}
                    {!info.available && !isDownloading && !info.error && (
                      <AlertTriangle className="w-4 h-4 text-amber-500" />
                    )}
                    {info.error && !isDownloading && (
                      <XCircle className="w-4 h-4 text-red-500" />
                    )}
                  </div>

                  <p className="text-sm text-muted-foreground mb-3">{info.description}</p>

                  {info.error && (
                    <p className="text-xs text-red-400 mb-2">{info.error}</p>
                  )}

                  {dlStatus === 'failed' && info.download?.error && (
                    <p className="text-xs text-red-400 mb-2">Download failed: {info.download.error}</p>
                  )}

                  {/* Progress Bar */}
                  {isDownloading && (
                    <div className="mb-3">
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-muted-foreground">{dlStatus === 'verifying' ? 'Verifying...' : 'Downloading...'}</span>
                        <span className="text-muted-foreground">{dlProgress}%</span>
                      </div>
                      <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
                        <div
                          className="h-full bg-blue-500 rounded-full transition-all duration-700"
                          style={{ width: `${dlProgress}%` }}
                        />
                      </div>
                    </div>
                  )}

                  {/* Capabilities */}
                  {info.capabilities && Object.keys(info.capabilities).length > 0 && (
                    <div className="flex flex-wrap gap-2 mb-3">
                      {(info.capabilities.modes || info.capabilities.features || []).map((f: string) => (
                        <span key={f} className="text-xs px-2 py-0.5 rounded bg-accent text-accent-foreground">
                          {f}
                        </span>
                      ))}
                      {info.capabilities.gpu_support && (
                        <span className="text-xs px-2 py-0.5 rounded bg-purple-500/20 text-purple-400">
                          GPU
                        </span>
                      )}
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2 flex-shrink-0">
                  {info.available && (
                    <button
                      onClick={() => handleProbe(name)}
                      className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-md bg-accent hover:bg-accent/80 transition-colors"
                      title="Test this backend with a sample image"
                    >
                      <BarChart3 className="w-3.5 h-3.5" />
                      Probe
                    </button>
                  )}
                  {!info.available && !isDownloading && (
                    <button
                      onClick={() => handleDownload(name)}
                      disabled={downloadingBackend === name}
                      className={cn(
                        'flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-md transition-all',
                        'bg-primary text-primary-foreground hover:bg-primary/90',
                        downloadingBackend === name && 'opacity-50 cursor-not-allowed'
                      )}
                    >
                      {downloadingBackend === name ? (
                        <>
                          <RotateCw className="w-3.5 h-3.5 animate-spin" />
                          Loading...
                        </>
                      ) : (
                        <>
                          <Download className="w-3.5 h-3.5" />
                          Download
                        </>
                      )}
                    </button>
                  )}
                  {isDownloading && (
                    <span className="text-xs text-blue-400 flex items-center gap-1">
                      <RotateCw className="w-3.5 h-3.5 animate-spin" />
                      {dlStatus === 'verifying' ? 'Verifying' : 'Downloading'}
                    </span>
                  )}
                </div>
              </div>
            </div>
          )
        })}

        {isError && (
          <div className="glass rounded-lg p-6 text-center border-amber-500/20">
            <AlertTriangle className="w-8 h-8 mx-auto mb-2 text-amber-500" />
            <h3 className="font-semibold mb-1">Backend Offline</h3>
            <p className="text-sm text-muted-foreground mb-3">
              The OCR backend server is not running. Start it from web_sota/start.ps1.
            </p>
            <p className="text-xs text-muted-foreground">
              Error: {(error as any)?.message || 'Connection refused'}
            </p>
            <button
              onClick={() => refetch()}
              className="mt-3 text-sm text-primary hover:underline"
            >
              Retry
            </button>
          </div>
        )}

        {list.length === 0 && !isError && (
          <div className="glass rounded-lg p-8 text-center">
            <Cpu className="w-12 h-12 mx-auto mb-3 text-muted-foreground" />
            <p className="text-muted-foreground">No backend status available.</p>
            <p className="text-xs text-muted-foreground mt-1">Start the OCR-MCP server to see backend status.</p>
          </div>
        )}
      </div>
    </div>
  )
}
