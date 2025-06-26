# Clover Sync Script
Write-Host "Setting data source to Clover..." -ForegroundColor Green

# Set data source to Clover
$dataSourceConfig = @{
    data_sources = @{
        sales = "clover"
        inventory = "clover"
    }
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:5000/api/dashboard/data-source-config" -Method PUT -Body $dataSourceConfig -ContentType "application/json"
Write-Host "Data source config response: $($response | ConvertTo-Json)" -ForegroundColor Yellow

Write-Host "Syncing sales data from Clover..." -ForegroundColor Green
$salesResponse = Invoke-RestMethod -Uri "http://localhost:5000/api/clover/sync/sales" -Method POST -ContentType "application/json"
Write-Host "Sales sync response: $($salesResponse | ConvertTo-Json)" -ForegroundColor Yellow

Write-Host "Syncing inventory data from Clover..." -ForegroundColor Green
$inventoryResponse = Invoke-RestMethod -Uri "http://localhost:5000/api/clover/sync/inventory" -Method POST -ContentType "application/json"
Write-Host "Inventory sync response: $($inventoryResponse | ConvertTo-Json)" -ForegroundColor Yellow

Write-Host "Clover sync completed!" -ForegroundColor Green 