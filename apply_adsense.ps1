$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

# 读取根目录现有的 adsense 片段
$snippet = Get-Content -Path "$root\adsense" -Raw

# 仅处理根目录下的 .html 文件（不递归子目录）
Get-ChildItem -File -Path $root -Filter *.html | ForEach-Object {
    $path = $_.FullName
    $text = Get-Content -Path $path -Raw

    # 已包含则跳过
    if ($text -match 'pagead2\.googlesyndication\.com/pagead/js/adsbygoogle\.js\?client=ca-pub-7274710287377352') {
        return
    }

    # 插入到 </head> 之前（不区分大小写，仅替换第一次出现）
    $new = [regex]::Replace($text, '(?i)</head>', ($snippet + [Environment]::NewLine + '</head>'), 1)

    if ($new -ne $text) {
        Set-Content -Path $path -Value $new -Encoding utf8
        Write-Host "Injected adsense into: $($_.Name)"
    } else {
        Write-Host "No </head> found or no change for: $($_.Name)"
    }
}


