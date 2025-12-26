# Скрипт для получения содержимого файла
param(
    [string]$FilePath
)

if (Test-Path $FilePath) {
    Get-Content $FilePath -Raw
} else {
    throw "File $FilePath not found"
}
