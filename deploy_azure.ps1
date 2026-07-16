<#
.SYNOPSIS
    Pharma Analytics — Azure Deployment Script
.DESCRIPTION
    Logs in to Azure, creates a Resource Group + Storage Account + Blob Container,
    retrieves the connection string, and writes it to the local .env file.
#>

param(
    [string]$ResourceGroup  = "pharma-analytics-rg",
    [string]$Location       = "eastus",
    [string]$StorageAccount = "pharmaanalyticsdata",
    [string]$ContainerName  = "pharma-analytics-data"
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host "  PHARMA ANALYTICS — AZURE DEPLOYMENT" -ForegroundColor Cyan
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host ""

# ── Step 1: Verify Azure CLI ─────────────────────────────────────────────────
Write-Host "[1/6] Checking Azure CLI..." -ForegroundColor Yellow
try {
    $azVersion = az version --output json 2>$null | ConvertFrom-Json
    Write-Host "  Azure CLI $($azVersion.'azure-cli') found" -ForegroundColor Green
} catch {
    Write-Host "  ERROR: Azure CLI not found. Install it with:" -ForegroundColor Red
    Write-Host "    winget install --id Microsoft.AzureCLI" -ForegroundColor Red
    exit 1
}

# ── Step 2: Login ─────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "[2/6] Logging in to Azure..." -ForegroundColor Yellow
Write-Host "  Using device code authentication. Follow the instructions below:" -ForegroundColor Gray
az login --use-device-code
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERROR: Login failed." -ForegroundColor Red
    exit 1
}
$account = az account show --output json | ConvertFrom-Json
Write-Host "  Logged in as: $($account.user.name)" -ForegroundColor Green
Write-Host "  Subscription: $($account.name)" -ForegroundColor Green

# ── Step 3: Create Resource Group ─────────────────────────────────────────────
Write-Host ""
Write-Host "[3/6] Creating Resource Group: $ResourceGroup ($Location)..." -ForegroundColor Yellow
az group create --name $ResourceGroup --location $Location --output none
Write-Host "  Resource group ready" -ForegroundColor Green

# ── Step 4: Create Storage Account ────────────────────────────────────────────
Write-Host ""
Write-Host "[4/6] Creating Storage Account: $StorageAccount..." -ForegroundColor Yellow
Write-Host "  (This may take 30-60 seconds)" -ForegroundColor Gray

# Storage account names must be globally unique, lowercase, 3-24 chars, no hyphens
az storage account create `
    --name $StorageAccount `
    --resource-group $ResourceGroup `
    --location $Location `
    --sku Standard_LRS `
    --kind StorageV2 `
    --access-tier Hot `
    --output none

if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERROR: Storage account creation failed." -ForegroundColor Red
    Write-Host "  The name '$StorageAccount' may already be taken globally." -ForegroundColor Red
    Write-Host "  Try a unique name: -StorageAccount 'pharmaanalyticsXYZ'" -ForegroundColor Yellow
    exit 1
}
Write-Host "  Storage account created" -ForegroundColor Green

# ── Step 5: Create Blob Container ─────────────────────────────────────────────
Write-Host ""
Write-Host "[5/6] Creating Blob Container: $ContainerName..." -ForegroundColor Yellow

$connString = az storage account show-connection-string `
    --name $StorageAccount `
    --resource-group $ResourceGroup `
    --output tsv

az storage container create `
    --name $ContainerName `
    --connection-string $connString `
    --output none

Write-Host "  Container created" -ForegroundColor Green

# ── Step 6: Update .env file ─────────────────────────────────────────────────
Write-Host ""
Write-Host "[6/6] Updating .env file..." -ForegroundColor Yellow

$envFile = Join-Path $PSScriptRoot ".env"

if (Test-Path $envFile) {
    # Read the current .env content
    $envContent = Get-Content $envFile -Raw

    # Replace or append AZURE_STORAGE_CONNECTION_STRING
    if ($envContent -match "AZURE_STORAGE_CONNECTION_STRING=") {
        $envContent = $envContent -replace "AZURE_STORAGE_CONNECTION_STRING=.*", "AZURE_STORAGE_CONNECTION_STRING=$connString"
    } else {
        $envContent += "`n# Azure`nAZURE_STORAGE_CONNECTION_STRING=$connString`n"
    }

    # Replace or append AZURE_CONTAINER_NAME
    if ($envContent -match "AZURE_CONTAINER_NAME=") {
        $envContent = $envContent -replace "AZURE_CONTAINER_NAME=.*", "AZURE_CONTAINER_NAME=$ContainerName"
    } else {
        $envContent += "AZURE_CONTAINER_NAME=$ContainerName`n"
    }

    Set-Content $envFile -Value $envContent.TrimEnd() -NoNewline
    Write-Host "  .env file updated with Azure credentials" -ForegroundColor Green
} else {
    Write-Host "  WARNING: .env file not found at $envFile" -ForegroundColor Yellow
    Write-Host "  Copy .env.example to .env and re-run, or add manually:" -ForegroundColor Yellow
}

# ── Summary ───────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host "  DEPLOYMENT COMPLETE" -ForegroundColor Cyan
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host ""
Write-Host "  Resource Group:    $ResourceGroup" -ForegroundColor White
Write-Host "  Storage Account:   $StorageAccount" -ForegroundColor White
Write-Host "  Container:         $ContainerName" -ForegroundColor White
Write-Host "  Location:          $Location" -ForegroundColor White
Write-Host ""
Write-Host "  Connection String:" -ForegroundColor White
Write-Host "  $($connString.Substring(0, [Math]::Min(80, $connString.Length)))..." -ForegroundColor DarkGray
Write-Host ""
Write-Host "  Next steps:" -ForegroundColor Yellow
Write-Host "    python sync_to_azure.py        # Upload data to Azure" -ForegroundColor White
Write-Host "    python run_pipeline.py          # Run pipeline + auto-sync" -ForegroundColor White
Write-Host ""
