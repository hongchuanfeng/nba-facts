$ErrorActionPreference = 'Stop'

Set-Location "$PSScriptRoot"

$ga = Get-Content -Raw -Path .\GA

$files = Get-ChildItem -Path .\cn -Filter *.html -File

foreach ($file in $files) {
  $content = Get-Content -Raw -Path $file.FullName
  if ($content -notmatch 'googletagmanager.com/gtag/js\?id=G-8WF0S87W7F') {
    if ($content -match '</head>') {
      $newContent = $content -replace '</head>', ($ga + "`r`n</head>")
      if ($newContent -ne $content) {
        Set-Content -Path $file.FullName -Value $newContent -Encoding UTF8
        Write-Host "Injected GA into: $($file.Name)"
      }
    }
  }
}

Write-Host "Done."


