# Per-repo fleet start config for ocr-mcp
# Edit ports/backend target here - start.ps1 is fleet-standard.
@{
    Name         = 'ocr-mcp'
    BackendPort  = 10859
    FrontendPort = 10858
    HealthPath   = '/api/health'
    WebRoot      = 'D:\Dev\repos\ocr-mcp\web_sota'
    Backend = @{
        Kind          = 'uvicorn'
        UvicornTarget = 'backend.app:app'
        SyncExtras    = @('dev')
        Env           = @{ WEB_PORT = '10859' }
    }
    Frontend = @{
        Kind           = 'vite-npm'
        PackageManager = 'npm'
        PortEnvVar     = 'VITE_PORT'
        ApiTargetEnv   = 'VITE_API_TARGET'
    }
}
