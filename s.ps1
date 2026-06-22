$secretLine = Get-Content .env |
    Where-Object { $_ -match '^GITHUB_WEBHOOK_SECRET=' } |
    Select-Object -First 1

$secret = ($secretLine -split '=', 2)[1].Trim()
if (-not $secret) {
    throw "GITHUB_WEBHOOK_SECRET is missing or empty in .env."
}
$body = '{"zen":"Repo Guardian local webhook test"}'
$key = [Text.Encoding]::UTF8.GetBytes($secret)
$data = [Text.Encoding]::UTF8.GetBytes($body)

$hmac = [System.Security.Cryptography.HMACSHA256]::new($key)

try {
    $hashBytes = $hmac.ComputeHash($data)
    $hash = -join ($hashBytes | ForEach-Object { $_.ToString("x2") })
}
finally {
    $hmac.Dispose()
}

$headers = @{
    "X-GitHub-Event" = "ping"
    "X-GitHub-Delivery" = [Guid]::NewGuid().ToString()
    "X-Hub-Signature-256" = "sha256=$hash"
}

$response = Invoke-RestMethod `
    -Uri "http://localhost:8000/api/webhooks/github" `
    -Method Post `
    -Headers $headers `
    -ContentType "application/json" `
    -Body $body

$response | ConvertTo-Json -Compress
