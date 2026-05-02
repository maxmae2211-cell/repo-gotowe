# guard-git.ps1
# PreToolUse hook — blokuje niebezpieczne komendy git
# Czyta wejście JSON ze stdin, zwraca decyzję uprawnień na stdout.

param()

$ALLOW = @{ hookSpecificOutput = @{ hookEventName = "PreToolUse"; permissionDecision = "allow" } }
$DENY = @{ hookSpecificOutput = @{ hookEventName = "PreToolUse"; permissionDecision = "deny" } }
$ASK = @{ hookSpecificOutput = @{ hookEventName = "PreToolUse"; permissionDecision = "ask"; permissionDecisionReason = "Niebezpieczna komenda git wymaga potwierdzenia użytkownika." } }

try {
    $raw = [Console]::In.ReadToEnd()
    $input_json = $raw | ConvertFrom-Json
}
catch {
    # Brak wejścia lub błąd parsowania — przepuszczamy
    $ALLOW | ConvertTo-Json -Compress
    exit 0
}

$toolName = $input_json.toolName
$toolInput = $input_json.toolInput

# Reagujemy tylko na narzędzia uruchamiające komendy
if ($toolName -notin @("run_in_terminal", "execute_command", "bash", "shell")) {
    $ALLOW | ConvertTo-Json -Compress
    exit 0
}

$cmd = ""
if ($toolInput.command) { $cmd = $toolInput.command }
elseif ($toolInput.cmd) { $cmd = $toolInput.cmd }
elseif ($toolInput.input) { $cmd = $toolInput.input }

if (-not $cmd) {
    $ALLOW | ConvertTo-Json -Compress
    exit 0
}

# Wzorce blokujące (bezwzględnie niebezpieczne)
$blockedPatterns = @(
    'git\s+push\s+.*--force(?!-with-lease)',   # force push (ale nie --force-with-lease)
    'git\s+reset\s+--hard',                     # twardy reset
    'git\s+branch\s+-[dD]\s+main',              # usunięcie brancha main
    'git\s+branch\s+-[dD]\s+master',            # usunięcie brancha master
    'git\s+clean\s+-fd',                         # czyszczenie katalogu roboczego
    'Remove-Item.*\.git\b',                      # usunięcie katalogu .git
    'rm\s+-rf?\s+.*\.git\b'                     # rm -rf .git
)

foreach ($pattern in $blockedPatterns) {
    if ($cmd -match $pattern) {
        $DENY.hookSpecificOutput["permissionDecisionReason"] = "ZABLOKOWANO przez hook guard-git: wykryto niebezpieczną komendę git: '$($cmd.Trim())'."
        $DENY | ConvertTo-Json -Compress
        exit 2
    }
}

# Wzorce wymagające potwierdzenia
$askPatterns = @(
    'git\s+push\s+.*--force-with-lease',        # force-with-lease — bezpieczniejszy, ale pytamy
    'git\s+push\s+origin\s+main',               # push bezpośrednio do main
    'git\s+push\s+origin\s+master',             # push bezpośrednio do master
    'git\s+rebase\s+',                           # rebase
    'git\s+branch\s+-[dD]\s+'                   # usunięcie dowolnego brancha
)

foreach ($pattern in $askPatterns) {
    if ($cmd -match $pattern) {
        $ASK | ConvertTo-Json -Compress
        exit 0
    }
}

$ALLOW | ConvertTo-Json -Compress
exit 0
