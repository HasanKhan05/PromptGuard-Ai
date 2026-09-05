$ErrorActionPreference = "Stop"
$Endpoint = "http://localhost:8000/api/chat"
$Models = @(
  "gemini/gemini-3.1-flash-lite",
  "pol/qwen-coder"
)

foreach ($Model in $Models) {
  Write-Host "Testing $Model..."
  $Body = @{
    prompt = "Reply with exactly: PROMPTGUARD ROUTE WORKING"
    model = $Model
  } | ConvertTo-Json

  $Result = Invoke-RestMethod -Uri $Endpoint -Method Post -ContentType "application/json" -Body $Body
  Write-Host $Result
}
