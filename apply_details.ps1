$ErrorActionPreference = 'Stop'

function Read-Text($Path) {
  return [System.IO.File]::ReadAllText($Path, [System.Text.Encoding]::UTF8)
}

function Write-Text($Path, $Content) {
  [System.IO.File]::WriteAllText($Path, $Content, [System.Text.Encoding]::UTF8)
}

function Find-DivBlock {
  param(
    [string]$Html,
    [string]$ClassSelector
  )
  # Match any div whose class attribute contains both tokens p-6 and md:p-8 (order independent)
  $regex = New-Object System.Text.RegularExpressions.Regex('<div\s+[^>]*class\s*=\s*"(?=[^"]*\bp-6\b)(?=[^"]*\bmd:p-8\b)[^"]*"[^>]*>', 'IgnoreCase')
  $m = $regex.Match($Html)
  if (-not $m.Success) { return @(-1,-1,-1,-1) }
  $openStart = $m.Index
  $openEnd = $m.Index + $m.Length
  $idx = $openEnd
  $depth = 1
  $openTag = New-Object System.Text.RegularExpressions.Regex('<div\b','IgnoreCase')
  $closeTag = New-Object System.Text.RegularExpressions.Regex('</div\s*>','IgnoreCase')
  while ($depth -gt 0) {
    $nextOpen = $openTag.Match($Html, $idx)
    $nextClose = $closeTag.Match($Html, $idx)
    if (-not $nextClose.Success) { return @($openStart,$openEnd,-1,-1) }
    if ($nextOpen.Success -and $nextOpen.Index -lt $nextClose.Index) {
      $depth += 1
      $idx = $nextOpen.Index + $nextOpen.Length
    } else {
      $depth -= 1
      $idx = $nextClose.Index + $nextClose.Length
      if ($depth -eq 0) {
        $closeStart = $nextClose.Index
        $closeEnd = $nextClose.Index + $nextClose.Length
        return @($openStart,$openEnd,$closeStart,$closeEnd)
      }
    }
  }
  return @($openStart,$openEnd,-1,-1)
}

function Escape-HTML($text) {
  $text = $text -replace '&','&amp;'
  $text = $text -replace '<','&lt;'
  $text = $text -replace '>','&gt;'
  return $text
}

function Split-Paragraphs($detail) {
  $parts = @()
  $buf = ''
  $fullStop = [string][char]0x3002
  $segments = $detail.Split([char]0x3002)
  foreach ($seg in $segments) {
    if ([string]::IsNullOrWhiteSpace($seg)) { continue }
    $seg2 = ($seg.Trim() + $fullStop)
    if (($buf + $seg2).Length -lt 180) { $buf += $seg2 } else { if ($buf.Length -gt 0) { $parts += $buf; $buf = '' } $parts += $seg2 }
  }
  if ($buf.Length -gt 0) { $parts += $buf }
  if ($parts.Count -eq 0) { $parts = @($detail) }
  return $parts
}

function Build-DetailBlock($detail) {
  $escaped = Escape-HTML $detail
  return @"
                <div class="prose lg:prose-xl max-w-none">
                    <p class="text-lg leading-relaxed whitespace-pre-line">$escaped</p>
                </div>
"@
}

function Build-EnhancedInner($title, $detail) {
  $name = Extract-ProbablePlayerName $title
  if (-not $name) { $name = '冷知识' }
  $paras = Split-Paragraphs $detail
  $paraHtml = ''
  for ($i=0; $i -lt $paras.Count; $i++) {
    $p = Escape-HTML $paras[$i]
    if ($i -eq 0) {
      $paraHtml += "                    <p class=\"text-lg leading-relaxed whitespace-pre-line first-letter:text-5xl first-letter:font-bold first-letter:text-nba-purple first-letter:mr-2 first-letter:float-left\">$p</p>\n"
    } else {
      $paraHtml += "                    <p class=\"text-lg leading-relaxed whitespace-pre-line\">$p</p>\n"
    }
  }
  $firstSentence = $paras[0]
  if ($firstSentence -ne $null) { $firstSentence = $firstSentence.Trim() } else { $firstSentence = '' }
  if ($firstSentence.Length -gt 60) { $firstSentence = $firstSentence.Substring(0,60) + '...' }
  $firstSentence = Escape-HTML $firstSentence

  $header = @"
                <!-- 信息徽章与阅读提示 -->
                <div class="flex flex-wrap items-center gap-2 mb-6 text-sm">
                    <span class="px-3 py-1 rounded-full bg-nba-purple/10 text-nba-purple">$name</span>
                    <span class="px-3 py-1 rounded-full bg-nba-gold/10 text-nba-gold">冷知识</span>
                    <span class="ml-auto text-gray-500 flex items-center"><i class="fa fa-clock-o mr-1"></i> 3 min read</span>
                </div>

                <!-- 渐变分隔线 -->
                <div class="relative mb-6">
                    <div class="h-1 w-24 bg-gradient-to-r from-nba-purple to-nba-gold rounded"></div>
                </div>

                <!-- 正文（首字下沉、美化排版） -->
                <div class="prose lg:prose-xl max-w-none text-gray-800">
"@
  $footer = @"
                </div>

                <!-- 侧栏引述与提示 -->
                <div class="mt-8 grid md:grid-cols-5 gap-6 items-start">
                    <div class="md:col-span-3">
                        <div class="bg-nba-light/60 border border-gray-100 rounded-lg p-4">
                            <div class="flex items-center text-nba-purple font-medium mb-2"><i class="fa fa-lightbulb-o mr-2"></i>小贴士</div>
                            <p class="text-gray-700 leading-relaxed">持续的基本功与专注力，决定了稳定的比赛表现。</p>
                        </div>
                    </div>
                    <div class="md:col-span-2">
                        <blockquote class="rounded-lg bg-gradient-to-br from-nba-purple/10 to-nba-gold/10 border-l-4 border-nba-purple p-4 italic text-gray-700">
                            "$firstSentence"
                        </blockquote>
                    </div>
                </div>
"@
  return $header + $paraHtml + $footer
}

function Extract-ProbablePlayerName($title) {
  # Prefer first 2-4 consecutive CJK characters at the start
  $m = [regex]::Match($title, '^[\u4e00-\u9fa5]{2,4}')
  if ($m.Success) { return $m.Value }
  return $null
}

function Update-HeroImage($html, $title) {
  $name = Extract-ProbablePlayerName $title
  if (-not $name) { return $html }
  $encoded = [System.Uri]::EscapeDataString($name)
  $avatar = ('https://ui-avatars.com/api/?name={0}&background=552583&color=ffffff&size=512' -f $encoded)
  $imgRegex = New-Object System.Text.RegularExpressions.Regex('(<img\s+[^>]*class\s*=\s*"[^"<>]*\bw-full\s+h-full\s+object-cover\b[^"<>]*"[^>]*src\s*=\s*")([^"<>]+)("[^>]*>)','IgnoreCase')
  $m = $imgRegex.Match($html)
  if ($m.Success) {
    return $html.Substring(0, $m.Groups[1].Index) + $m.Groups[1].Value + $avatar + $m.Groups[3].Value + $html.Substring($m.Index + $m.Length)
  }
  $imgClassRegex = New-Object System.Text.RegularExpressions.Regex('(<img\s+[^>]*class\s*=\s*"[^"<>]*\bw-full\s+h-full\s+object-cover\b[^"<>]*"[^>]*)(>)','IgnoreCase')
  $m2 = $imgClassRegex.Match($html)
  if ($m2.Success) {
    $before = $html.Substring(0, $m2.Groups[1].Index + $m2.Groups[1].Length)
    $after = $html.Substring($m2.Groups[2].Index)
    $injected = ' src="' + $avatar + '"'
    return $before + $injected + $after
  }
  return $html
}

$jsonPath = Join-Path $PSScriptRoot 'nba.json'
$jsonRaw = Read-Text $jsonPath
$data = $jsonRaw | ConvertFrom-Json

$updated = 0
$missing = @()
$scanned = 0
$notFoundDiv = 0

foreach ($item in $data) {
  $local = $item.localLink
  if (-not $local) { continue }
  $detail = $item.detail
  if (-not $detail) { continue }
  $title = $item.title
  $htmlPath = Join-Path $PSScriptRoot $local
  if (-not (Test-Path $htmlPath)) { $missing += $local; continue }

  $html = Read-Text $htmlPath
  $res = Find-DivBlock -Html $html -ClassSelector 'p-6 md:p-8'
  $openStart,$openEnd,$closeStart,$closeEnd = $res
  if ($openStart -lt 0 -or $closeStart -lt 0) { $notFoundDiv += 1; continue }
  if ($local -ne 'nba_1.html') { $inner = Build-EnhancedInner -title $title -detail $detail } else { $inner = Build-DetailBlock $detail }
  $newHtml = $html.Substring(0, $openEnd) + $inner + $html.Substring($closeStart)
  $newHtml = Update-HeroImage -html $newHtml -title $title

  if ($newHtml -ne $html) {
    Write-Text $htmlPath $newHtml
    $updated += 1
  }
  $scanned += 1
}

Write-Host "Scanned items: $scanned; Updated files: $updated; Missing div: $notFoundDiv"
if ($missing.Count -gt 0) { Write-Host ("Missing html files: " + ($missing -join ', ')) }


