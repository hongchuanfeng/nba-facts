$ErrorActionPreference = 'Stop'

function Read-Text($Path) { [System.IO.File]::ReadAllText($Path, [System.Text.Encoding]::UTF8) }
function Write-Text($Path, $Content) { [System.IO.File]::WriteAllText($Path, $Content, [System.Text.Encoding]::UTF8) }

function Find-DivBlock {
  param([string]$Html)
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
      $depth += 1; $idx = $nextOpen.Index + $nextOpen.Length
    } else { $depth -= 1; $idx = $nextClose.Index + $nextClose.Length; if ($depth -eq 0) { return @($openStart,$openEnd,$nextClose.Index,$nextClose.Index+$nextClose.Length) } }
  }
  return @($openStart,$openEnd,-1,-1)
}

function Escape-HTML($text) {
  $text = $text -replace '&','&amp;'; $text = $text -replace '<','&lt;'; $text = $text -replace '>','&gt;'; return $text
}

function Extract-Name($title) {
  $m = [regex]::Match($title, '^[\u4e00-\u9fa5]{2,4}')
  if ($m.Success) { return $m.Value }
  return $null
}

function Split-Paragraphs($detail) {
  # Split by CJK full stop U+3002 while keeping reasonable chunk sizes
  $parts = @()
  $buf = ''
  $fullStop = [string][char]0x3002
  $segments = [regex]::Split($detail, [string][char]0x3002)
  foreach ($seg in $segments) {
    if ([string]::IsNullOrWhiteSpace($seg)) { continue }
    $seg2 = ($seg.Trim() + $fullStop)
    if (($buf + $seg2).Length -lt 180) { $buf += $seg2 }
    else { if ($buf.Length -gt 0) { $parts += $buf; $buf = '' }; $parts += $seg2 }
  }
  if ($buf.Length -gt 0) { $parts += $buf }
  if ($parts.Count -eq 0) { $parts = @($detail) }
  return $parts
}

function Build-Inner($title, $detail) {
  $name = Extract-Name $title
  $escapedTitleName = if ($name) { $name } else { '冷知识' }
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
  return @"
                <!-- 信息徽章与阅读提示 -->
                <div class="flex flex-wrap items-center gap-2 mb-6 text-sm">
                    <span class="px-3 py-1 rounded-full bg-nba-purple/10 text-nba-purple">$escapedTitleName</span>
                    <span class="px-3 py-1 rounded-full bg-nba-gold/10 text-nba-gold">冷知识</span>
                    <span class="ml-auto text-gray-500 flex items-center"><i class="fa fa-clock-o mr-1"></i> 3 min read</span>
                </div>

                <!-- 渐变分隔线 -->
                <div class="relative mb-6">
                    <div class="h-1 w-24 bg-gradient-to-r from-nba-purple to-nba-gold rounded"></div>
                </div>

                <!-- 正文（首字下沉、美化排版） -->
                <div class="prose lg:prose-xl max-w-none text-gray-800">
$paraHtml                </div>

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
                            “$firstSentence”
                        </blockquote>
                    </div>
                </div>
"@
}

$jsonPath = Join-Path $PSScriptRoot 'nba.json'
$data = (Read-Text $jsonPath) | ConvertFrom-Json

$updated = 0
$skipped = 0
foreach ($item in $data) {
  $link = $item.localLink
  if (-not $link) { continue }
  # 跳过 nba_1.html，处理 nba_2..nba_153
  if ($link -eq 'nba_1.html') { continue }
  $htmlPath = Join-Path $PSScriptRoot $link
  if (-not (Test-Path $htmlPath)) { continue }
  $detail = $item.detail
  if (-not $detail) { $skipped += 1; continue }
  $html = Read-Text $htmlPath
  $res = Find-DivBlock -Html $html
  $openStart,$openEnd,$closeStart,$closeEnd = $res
  if ($openStart -lt 0 -or $closeStart -lt 0) { $skipped += 1; continue }
  $inner = Build-Inner -title $item.title -detail $detail
  $newHtml = $html.Substring(0, $openEnd) + $inner + $html.Substring($closeStart)
  if ($newHtml -ne $html) { Write-Text $htmlPath $newHtml; $updated += 1 }
}

Write-Host "Formatted pages updated: $updated; Skipped: $skipped"


