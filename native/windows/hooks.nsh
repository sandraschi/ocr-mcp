; Kill UI + backend before install/uninstall (backend locks resources/*.exe).
; Fleet client registration: mcp-clients.nsh (canonical copy vendored by
; native/build.ps1 from mcp-central-docs - do not edit it here).
!define MCP_REG_NAME "ocr-mcp"
!define MCP_REG_EXE "ocr-mcp-backend.exe"
!include "${__FILEDIR__}\mcp-clients.nsh"
!macro KillOcrMcpFleetProcesses
  DetailPrint "Stopping ocr-mcp processes..."
  ExecWait 'taskkill /F /IM ocr-mcp-backend.exe /T' $0
  ExecWait 'taskkill /F /IM ocr-mcp-native.exe /T' $0
  !if "${INSTALLMODE}" == "currentUser"
    nsis_tauri_utils::KillProcessCurrentUser "ocr-mcp-backend.exe"
    Pop $0
    nsis_tauri_utils::KillProcessCurrentUser "ocr-mcp-native.exe"
    Pop $0
  !else
    nsis_tauri_utils::KillProcess "ocr-mcp-backend.exe"
    Pop $0
    nsis_tauri_utils::KillProcess "ocr-mcp-native.exe"
    Pop $0
  !endif
  Sleep 2000
!macroend

!macro NSIS_HOOK_PREINSTALL
  !insertmacro KillOcrMcpFleetProcesses
!macroend

!macro NSIS_HOOK_PREUNINSTALL
  !insertmacro KillOcrMcpFleetProcesses
  !insertmacro McpClientsUnregister
!macroend

!macro NSIS_HOOK_POSTINSTALL
  !insertmacro McpClientsRegister
!macroend
