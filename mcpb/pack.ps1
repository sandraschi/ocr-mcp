#Requires -Version 5.1
# Forwarder (was a vendored copy of the fleet pipeline): the canonical pack
# pipeline is fleet-mcpb-pack.ps1, reached via the scripts/mcpb-pack.ps1 shim.
# Kept so existing callers of mcpb/pack.ps1 keep working.
& (Join-Path $PSScriptRoot '..\scripts\mcpb-pack.ps1')
exit $LASTEXITCODE
