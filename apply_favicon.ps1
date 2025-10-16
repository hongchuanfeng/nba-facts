$ErrorActionPreference = 'Stop'

Set-Location "$PSScriptRoot"

function Add-FaviconTag {
  param(
    [Parameter(Mandatory=$true)][string]$Path,
    [Parameter(Mandatory=$true)][string]$Href
  )

  $files = Get-ChildItem -Path $Path -Filter *.html -File
  foreach ($file in $files) {
    $content = Get-Content -Raw -Path $file.FullName
    $alreadyHas = $content -like ('*href="' + $Href + '"*') -or $content -match '<link\s+[^>]*rel=\"icon\"[^>]*>'
    if (-not $alreadyHas) {
      if ($content -match '</head>') {
        $faviconTag = '    <link rel="icon" href="' + $Href + '">'
        $new = $content -replace '</head>', ($faviconTag + "`r`n</head>")
        if ($new -ne $content) {
          Set-Content -Path $file.FullName -Value $new -Encoding UTF8
          Write-Host "Inserted favicon in: $($file.FullName)"
        }
      }
    }
  }
}

# Root-level HTML: href="favicon.ico"
Add-FaviconTag -Path . -Href 'favicon.ico'

# cn/*.html: href="../favicon.ico"
if (Test-Path .\cn) {
  Add-FaviconTag -Path .\cn -Href '../favicon.ico'
}

Write-Host 'Done.'


