#!/usr/bin/env powershell
# Deploy MCP Server to Production Server
# نصب سرور MCP روی سرور تولید

param(
    [string]$ServerIP = "185.204.171.107",
    [string]$Username = "ubuntu",
    [switch]$Force
)

Write-Host "🚀 Deploying Bivaset MCP Server to Production..." -ForegroundColor Green
Write-Host "Target Server: $Username@$ServerIP" -ForegroundColor Yellow

# Check if required files exist
$RequiredFiles = @(
    "mcp_server_standalone.py",
    "mcp_production_config.json",
    "requirements.txt"
)

foreach ($file in $RequiredFiles) {
    if (-not (Test-Path $file)) {
        Write-Host "❌ Required file not found: $file" -ForegroundColor Red
        exit 1
    }
}

Write-Host "✅ All required files found" -ForegroundColor Green

# Create deployment package
Write-Host "📦 Creating deployment package..." -ForegroundColor Blue
$TempDir = "mcp_deployment_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
New-Item -ItemType Directory -Path $TempDir -Force | Out-Null

# Copy files to deployment directory
Copy-Item "mcp_server_standalone.py" "$TempDir/"
Copy-Item "mcp_production_config.json" "$TempDir/"
Copy-Item "requirements.txt" "$TempDir/"
Copy-Item "MCP_README.md" "$TempDir/" -ErrorAction SilentlyContinue

# Create deployment script for the server
$DeployScript = @"
#!/bin/bash
# MCP Server Production Deployment Script
# اسکریپت نصب سرور MCP در محیط تولید

set -e

echo "🚀 Installing Bivaset MCP Server on Production..."

# Update system
sudo apt update -y

# Install Python and required packages
sudo apt install -y python3 python3-pip python3-venv postgresql-client

# Create MCP user and directory
sudo useradd -r -s /bin/false mcpuser 2>/dev/null || true
sudo mkdir -p /opt/bivaset-mcp
sudo chown mcpuser:mcpuser /opt/bivaset-mcp

# Copy files
sudo cp mcp_server_standalone.py /opt/bivaset-mcp/
sudo cp mcp_production_config.json /opt/bivaset-mcp/
sudo cp requirements.txt /opt/bivaset-mcp/
sudo cp MCP_README.md /opt/bivaset-mcp/ 2>/dev/null || true

# Create virtual environment
cd /opt/bivaset-mcp
sudo python3 -m venv venv
sudo chown -R mcpuser:mcpuser venv

# Install Python dependencies
sudo -u mcpuser ./venv/bin/pip install --upgrade pip
sudo -u mcpuser ./venv/bin/pip install -r requirements.txt

# Create systemd service
sudo tee /etc/systemd/system/bivaset-mcp.service > /dev/null << 'EOF'
[Unit]
Description=Bivaset MCP Server
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=simple
User=mcpuser
Group=mcpuser
WorkingDirectory=/opt/bivaset-mcp
ExecStart=/opt/bivaset-mcp/venv/bin/python mcp_server_standalone.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

# Create log directory
sudo mkdir -p /var/log/bivaset-mcp
sudo chown mcpuser:mcpuser /var/log/bivaset-mcp

# Set permissions
sudo chown -R mcpuser:mcpuser /opt/bivaset-mcp
sudo chmod +x /opt/bivaset-mcp/mcp_server_standalone.py

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable bivaset-mcp
sudo systemctl start bivaset-mcp

# Check status
sleep 5
sudo systemctl status bivaset-mcp --no-pager

echo "✅ MCP Server installation completed!"
echo "📊 Service status:"
sudo systemctl is-active bivaset-mcp
echo "📝 To view logs: sudo journalctl -u bivaset-mcp -f"
echo "🔧 To restart: sudo systemctl restart bivaset-mcp"
"@

$DeployScript | Out-File -FilePath "$TempDir/install_mcp.sh" -Encoding UTF8

Write-Host "✅ Deployment package created: $TempDir" -ForegroundColor Green

# Upload files to server
Write-Host "📤 Uploading files to production server..." -ForegroundColor Blue
try {
    scp -r $TempDir/* "$Username@${ServerIP}:~/"
    Write-Host "✅ Files uploaded successfully" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to upload files: $_" -ForegroundColor Red
    exit 1
}

# Execute deployment on server
Write-Host "🔧 Running deployment on server..." -ForegroundColor Blue
try {
    ssh "$Username@$ServerIP" "chmod +x install_mcp.sh && ./install_mcp.sh"
    Write-Host "✅ Deployment completed successfully!" -ForegroundColor Green
} catch {
    Write-Host "❌ Deployment failed: $_" -ForegroundColor Red
    exit 1
}

# Test MCP server
Write-Host "🧪 Testing MCP server..." -ForegroundColor Blue
try {
    ssh "$Username@$ServerIP" "sudo systemctl status bivaset-mcp --no-pager"
    Write-Host "✅ MCP Server is running!" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Please check server status manually" -ForegroundColor Yellow
}

# Cleanup
Remove-Item -Recurse -Force $TempDir

Write-Host "`n🎉 MCP Server deployment completed!" -ForegroundColor Green
Write-Host "Server: $Username@$ServerIP" -ForegroundColor Yellow
Write-Host "Service: bivaset-mcp" -ForegroundColor Yellow
Write-Host "Logs: sudo journalctl -u bivaset-mcp -f" -ForegroundColor Yellow
Write-Host "Restart: sudo systemctl restart bivaset-mcp" -ForegroundColor Yellow
