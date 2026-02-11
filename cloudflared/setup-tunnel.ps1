# Cloudflare Tunnel Setup Script
# Tu dong tao tunnel, DNS record va Public Hostname (ingress) giong UI

param(
    [string]$TunnelName = "odoo-tunnel",
    [string]$ConfigPath = "$PSScriptRoot\config.yml",
    [string]$CredentialsPath = "$PSScriptRoot\credentials.json",
    [string]$AccountId = "",      # Cloudflare Account ID
    [string]$ApiToken = ""        # API Token with Tunnel:Edit permission
)

# Do NOT use $ErrorActionPreference = "Stop" as cloudflared outputs warnings to stderr

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Cloudflare Tunnel Setup Script" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# 1. Kiem tra cloudflared da cai dat chua
Write-Host "[1/6] Checking cloudflared installation..." -ForegroundColor Yellow
$version = $null
try {
    $version = & cloudflared --version 2>&1 | Select-String "cloudflared version"
}
catch {
    # Ignore
}

if ($version) {
    Write-Host "  [OK] $version" -ForegroundColor Green
}
else {
    Write-Host "  [X] cloudflared not installed. Please install it first." -ForegroundColor Red
    Write-Host "    winget install Cloudflare.cloudflared" -ForegroundColor Gray
    exit 1
}

# 2. Kiem tra dang nhap
Write-Host ""
Write-Host "[2/6] Checking Cloudflare authentication..." -ForegroundColor Yellow
$certPath = "$env:USERPROFILE\.cloudflared\cert.pem"
if (-not (Test-Path $certPath)) {
    Write-Host "  [!] Not logged in. Opening browser for authentication..." -ForegroundColor DarkYellow
    & cloudflared tunnel login 2>&1 | Out-Host
    if (-not (Test-Path $certPath)) {
        Write-Host "  [X] Authentication failed." -ForegroundColor Red
        exit 1
    }
}
Write-Host "  [OK] Authenticated with Cloudflare" -ForegroundColor Green

# 3. Tao hoac lay thong tin tunnel
Write-Host ""
Write-Host "[3/6] Setting up tunnel '$TunnelName'..." -ForegroundColor Yellow

# Kiem tra tunnel da ton tai chua - redirect stderr to null properly
$tunnelJson = & cloudflared tunnel list --output json 2>$null
$tunnelList = $tunnelJson | ConvertFrom-Json -ErrorAction SilentlyContinue
$existingTunnel = $tunnelList | Where-Object { $_.name -eq $TunnelName }

if ($existingTunnel) {
    Write-Host "  [OK] Tunnel '$TunnelName' already exists (ID: $($existingTunnel.id))" -ForegroundColor Green
    $tunnelId = $existingTunnel.id
}
else {
    Write-Host "  [!] Creating new tunnel '$TunnelName'..." -ForegroundColor DarkYellow
    $createOutput = & cloudflared tunnel create $TunnelName 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  [X] Failed to create tunnel: $createOutput" -ForegroundColor Red
        exit 1
    }
    # Lay tunnel ID tu output
    $tunnelJson = & cloudflared tunnel list --output json 2>$null
    $tunnelList = $tunnelJson | ConvertFrom-Json -ErrorAction SilentlyContinue
    $existingTunnel = $tunnelList | Where-Object { $_.name -eq $TunnelName }
    $tunnelId = $existingTunnel.id
    Write-Host "  [OK] Tunnel created (ID: $tunnelId)" -ForegroundColor Green
}

# 4. Copy credentials file
Write-Host ""
Write-Host "[4/6] Setting up credentials file..." -ForegroundColor Yellow
$userCredPath = "$env:USERPROFILE\.cloudflared\$tunnelId.json"
if (Test-Path $userCredPath) {
    if (-not (Test-Path $CredentialsPath) -or ((Get-FileHash $userCredPath).Hash -ne (Get-FileHash $CredentialsPath -ErrorAction SilentlyContinue).Hash)) {
        Copy-Item $userCredPath $CredentialsPath -Force
        Write-Host "  [OK] Credentials copied to $CredentialsPath" -ForegroundColor Green
    }
    else {
        Write-Host "  [OK] Credentials already in place" -ForegroundColor Green
    }
}
else {
    Write-Host "  [X] Credentials file not found at $userCredPath" -ForegroundColor Red
    exit 1
}

# 5. Parse config.yml va tao DNS records
Write-Host ""
Write-Host "[5/6] Creating DNS records from config..." -ForegroundColor Yellow

# Doc config file va extract hostnames va services
$configContent = Get-Content $ConfigPath -Raw

# Parse ingress rules from config.yml
$ingressRules = @()
$hostnameMatches = [regex]::Matches($configContent, '(?m)^\s*-\s*hostname:\s*(\S+)\s*\n\s*service:\s*(\S+)')
foreach ($match in $hostnameMatches) {
    $hostname = $match.Groups[1].Value
    $service = $match.Groups[2].Value
    $ingressRules += @{
        hostname = $hostname
        service = $service
    }
    
    Write-Host "  Creating DNS record for: $hostname" -ForegroundColor Gray
    
    # Tao DNS CNAME record tro ve tunnel
    $dnsOutput = & cloudflared tunnel route dns --overwrite-dns $TunnelName $hostname 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [OK] DNS record created: $hostname -> $TunnelName.cfargotunnel.com" -ForegroundColor Green
    }
    else {
        if ($dnsOutput -match "already exists" -or $dnsOutput -match "CNAME") {
            Write-Host "  [OK] DNS record already exists: $hostname" -ForegroundColor Green
        }
        else {
            Write-Host "  [X] Failed to create DNS record: $dnsOutput" -ForegroundColor Red
        }
    }
}

if ($ingressRules.Count -eq 0) {
    Write-Host "  [!] No hostnames found in config. Skipping DNS setup." -ForegroundColor DarkYellow
}

# 6. Tao Public Hostname (ingress) qua API (giong UI)
Write-Host ""
Write-Host "[6/6] Creating Public Hostnames via API..." -ForegroundColor Yellow

# Kiem tra API credentials
if ([string]::IsNullOrEmpty($AccountId) -or [string]::IsNullOrEmpty($ApiToken)) {
    # Try to read from environment variables
    if ($env:CF_ACCOUNT_ID) { $AccountId = $env:CF_ACCOUNT_ID }
    if ($env:CF_API_TOKEN) { $ApiToken = $env:CF_API_TOKEN }
}

if ([string]::IsNullOrEmpty($AccountId) -or [string]::IsNullOrEmpty($ApiToken)) {
    Write-Host "  [!] API credentials not provided. Skipping Public Hostname creation." -ForegroundColor DarkYellow
    Write-Host "      To enable this feature, provide:" -ForegroundColor Gray
    Write-Host "        -AccountId <your-account-id>" -ForegroundColor Gray
    Write-Host "        -ApiToken <your-api-token>" -ForegroundColor Gray
    Write-Host "      Or set environment variables:" -ForegroundColor Gray
    Write-Host "        CF_ACCOUNT_ID and CF_API_TOKEN" -ForegroundColor Gray
    Write-Host ""
    Write-Host "      Your tunnel will still work with local config.yml" -ForegroundColor DarkYellow
}
else {
    # Build ingress config for API
    $ingressConfig = @()
    foreach ($rule in $ingressRules) {
        $ingressConfig += @{
            hostname = $rule.hostname
            service = $rule.service
            originRequest = @{}
        }
    }
    # Add catch-all rule
    $ingressConfig += @{
        service = "http_status:404"
    }
    
    $configBody = @{
        config = @{
            ingress = $ingressConfig
        }
    } | ConvertTo-Json -Depth 10
    
    Write-Host "  Updating tunnel configuration via API..." -ForegroundColor Gray
    
    try {
        $headers = @{
            "Authorization" = "Bearer $ApiToken"
            "Content-Type" = "application/json"
        }
        
        $apiUrl = "https://api.cloudflare.com/client/v4/accounts/$AccountId/cfd_tunnel/$tunnelId/configurations"
        
        $response = Invoke-RestMethod -Uri $apiUrl -Method Put -Headers $headers -Body $configBody -ErrorAction Stop
        
        if ($response.success) {
            Write-Host "  [OK] Public Hostnames created successfully!" -ForegroundColor Green
            foreach ($rule in $ingressRules) {
                Write-Host "       $($rule.hostname) -> $($rule.service)" -ForegroundColor Gray
            }
        }
        else {
            Write-Host "  [X] API returned errors: $($response.errors | ConvertTo-Json)" -ForegroundColor Red
        }
    }
    catch {
        Write-Host "  [X] Failed to update via API: $_" -ForegroundColor Red
        Write-Host "      Your tunnel will still work with local config.yml" -ForegroundColor DarkYellow
    }
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Tunnel ID: $tunnelId" -ForegroundColor White
Write-Host "Config: $ConfigPath" -ForegroundColor White
Write-Host "Credentials: $CredentialsPath" -ForegroundColor White
Write-Host ""
Write-Host "To run the tunnel:" -ForegroundColor Yellow
Write-Host "  cloudflared tunnel --config $ConfigPath run" -ForegroundColor Gray
Write-Host ""
Write-Host "Or use Docker:" -ForegroundColor Yellow
Write-Host "  docker run -v ${PSScriptRoot}:/etc/cloudflared cloudflare/cloudflared:latest tunnel --config /etc/cloudflared/config.yml run" -ForegroundColor Gray
Write-Host ""

# Optional: Hoi co muon chay tunnel ngay khong
$runNow = Read-Host "Do you want to start the tunnel now? (y/N)"
if ($runNow -eq "y" -or $runNow -eq "Y") {
    Write-Host ""
    Write-Host "Starting tunnel..." -ForegroundColor Yellow
    & cloudflared tunnel --config $ConfigPath run
}
