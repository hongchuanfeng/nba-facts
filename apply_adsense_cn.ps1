$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$target = Join-Path $root 'cn'
if (-not (Test-Path $target)) { throw "Target directory not found: $target" }
Set-Location $root

$snippet = Get-Content -Path "$root\adsense" -Raw

# 处理 cn 目录内的所有 .html（递归）
Get-ChildItem -File -Path $target -Filter *.html -Recurse | ForEach-Object {
    $path = $_.FullName
    $text = Get-Content -Path $path -Raw

    if ($text -match 'pagead2\.googlesyndication\.com/pagead/js/adsbygoogle\.js\?client=ca-pub-7274710287377352') {
        return
    }

    $new = [regex]::Replace($text, '(?i)</head>', ($snippet + [Environment]::NewLine + '</head>'), 1)

    if ($new -ne $text) {
        Set-Content -Path $path -Value $new -Encoding utf8
        Write-Host "Injected adsense into: $($_.FullName)"
    } else {
        Write-Host "No </head> found or no change for: $($_.FullName)"
    }
}


