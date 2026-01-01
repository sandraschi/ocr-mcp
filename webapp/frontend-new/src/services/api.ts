import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8765'

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
})

// Request interceptor for auth (if needed later)
apiClient.interceptors.request.use((config: any) => {
  // Add auth headers here when implemented
  return config
})

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response: any) => response,
  (error: any) => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

export interface Scanner {
  id: string
  name: string
  manufacturer?: string
  type: string
  status: 'ready' | 'busy' | 'error'
  supports_adf?: boolean
  supports_duplex?: boolean
  max_dpi?: number
}

export interface OCRResult {
  text: string
  confidence: number
  language: string
  tables?: TableData[]
  layout?: LayoutData
  metadata: Record<string, any>
}

export interface TableData {
  rows: number
  columns: number
  headers: string[]
  data: string[][]
}

export interface LayoutData {
  blocks: Array<{
    type: string
    text: string
    confidence: number
    bbox: [number, number, number, number]
  }>
}

export interface ScanResult {
  success: boolean
  device_id: string
  settings: {
    dpi: number
    color_mode: string
    paper_size: string
  }
  image_path: string
  image_info: {
    width: number
    height: number
    mode: string
    filename: string
  }
  message: string
}

export interface ScanSettings {
  dpi: number
  colorMode: string
  paperSize: string
  source: string
  brightness: number
  contrast: number
}

class ApiService {
  getApiBaseUrl(): string {
    return API_BASE_URL
  }

  async getScanners(): Promise<{ scanners: Scanner[] }> {
    const response = await apiClient.get('/api/scanners')
    return response.data
  }

  async scanDocument(
    deviceId: string,
    settings: ScanSettings
  ): Promise<ScanResult> {
    const formData = new FormData()
    formData.append('device_id', deviceId)
    formData.append('dpi', settings.dpi.toString())
    formData.append('color_mode', settings.colorMode)
    formData.append('paper_size', settings.paperSize)

    const response = await apiClient.post('/api/scan', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  }

  async getHealth(): Promise<{
    status: string
    mcp_connected: boolean
    mcp_status: string
    demo_mode: boolean
    instructions?: string
    version: string
  }> {
    const response = await apiClient.get('/api/health')
    return response.data
  }

  async getBackends(): Promise<{
    backends: Array<{
      name: string
      available: boolean
      description: string
    }>
    default_backend: string
  }> {
    const response = await apiClient.get('/api/backends')
    return response.data
  }

  async processFile(
    file: File,
    ocrMode: string = 'text',
    backend: string = 'auto'
  ): Promise<OCRResult> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('ocr_mode', ocrMode)
    formData.append('backend', backend)

    const response = await apiClient.post('/api/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  }

  async getJobStatus(jobId: string): Promise<{
    job_id: string
    status: string
    progress: number
    filename: string
    result?: any
    error?: string
  }> {
    const response = await apiClient.get(`/api/job/${jobId}`)
    return response.data
  }

  async processBatch(
    files: File[],
    ocrMode: string = 'text',
    backend: string = 'auto'
  ): Promise<any> {
    const formData = new FormData()
    files.forEach((file) => {
      formData.append('files', file)
    })
    formData.append('ocr_mode', ocrMode)
    formData.append('backend', backend)

    const response = await apiClient.post('/api/process_batch', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  }

  async optimizeProcessing(
    file: File,
    targetQuality: number = 0.8,
    maxAttempts: number = 3
  ): Promise<any> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('target_quality', targetQuality.toString())
    formData.append('max_attempts', maxAttempts.toString())

    const response = await apiClient.post('/api/optimize', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  }

  async convertFormat(
    file: File,
    targetFormat: string,
    ocrMode: string = 'auto',
    backend: string = 'auto'
  ): Promise<any> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('target_format', targetFormat)
    formData.append('ocr_mode', ocrMode)
    formData.append('backend', backend)

    const response = await apiClient.post('/api/convert', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  }

  async getPipelines(): Promise<{
    pipelines: Array<{
      id: string
      name: string
      description: string
      steps: string[]
    }>
  }> {
    const response = await apiClient.get('/api/pipelines')
    return response.data
  }

  async executePipeline(pipelineId: string, file: File): Promise<any> {
    const formData = new FormData()
    formData.append('pipeline_id', pipelineId)
    formData.append('file', file)

    const response = await apiClient.post('/api/pipelines/execute', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  }
}

export const apiService = new ApiService()