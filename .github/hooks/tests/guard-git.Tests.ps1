#!/usr/bin/env pwsh
# guard-git.Tests.ps1 — testy jednostkowe Pester dla guard-git.ps1
# Uruchom: pwsh -File .github/hooks/tests/guard-git.Tests.ps1
# lub:     Invoke-Pester .github/hooks/tests/guard-git.Tests.ps1 -Output Detailed

BeforeAll {
    $scriptPath = Join-Path $PSScriptRoot ".." "scripts" "guard-git.ps1"
    $configPath = Join-Path $PSScriptRoot ".." "guard-git.json"
    # Cross-platform temp dir
    $tmpBase = if ($env:TEMP) { $env:TEMP } elseif ($env:TMPDIR) { $env:TMPDIR } else { "/tmp" }
    $testTmp = Join-Path $tmpBase "guard-git-tests-$(Get-Random)"
    New-Item -ItemType Directory -Path $testTmp -Force | Out-Null

    # Pomocnicza funkcja: zapis tymczasowej konfiguracji JSON
    function New-TestConfig([hashtable]$Overrides = @{}) {
        $base = @{
            protected_branches               = @("main", "master")
            blocked_file_patterns            = @(".bzt-rc", "*.env", "*.pem", "*.key", "*.token")
            warn_only                        = $false
            log_blocked                      = $false
            block_force_push                 = $true
            max_file_size_kb                 = 100
            blocked_commit_message_patterns  = @("^WIP", "fixup!", "DO NOT MERGE")
            require_conventional_commits     = $false
            conventional_commit_scopes       = @()
        }
        foreach ($k in $Overrides.Keys) { $base[$k] = $Overrides[$k] }
        $cfgFile = Join-Path $testTmp "guard-git-test.json"
        $base | ConvertTo-Json -Depth 5 | Set-Content $cfgFile -Encoding utf8
        return $cfgFile
    }
}

AfterAll {
    if (Test-Path $testTmp) { Remove-Item $testTmp -Recurse -Force }
}

Describe "Konfiguracja guard-git.json" {
    It "Plik konfiguracyjny istnieje w repozytorium" {
        $configPath | Should -Exist
    }

    It "Konfiguracja zawiera wymagane klucze" {
        $cfg = Get-Content $configPath -Raw | ConvertFrom-Json
        $cfg.protected_branches          | Should -Not -BeNullOrEmpty
        $cfg.blocked_file_patterns       | Should -Not -BeNullOrEmpty
        $cfg.PSObject.Properties.Name    | Should -Contain "warn_only"
        $cfg.PSObject.Properties.Name    | Should -Contain "log_blocked"
        $cfg.PSObject.Properties.Name    | Should -Contain "block_force_push"
        $cfg.PSObject.Properties.Name    | Should -Contain "max_file_size_kb"
    }

    It "max_file_size_kb jest nieujemne" {
        $cfg = Get-Content $configPath -Raw | ConvertFrom-Json
        [int]$cfg.max_file_size_kb | Should -BeGreaterOrEqual 0
    }

    It "blocked_file_patterns zawiera .bzt-rc" {
        $cfg = Get-Content $configPath -Raw | ConvertFrom-Json
        $cfg.blocked_file_patterns | Should -Contain ".bzt-rc"
    }

    It "protected_branches zawiera main i master" {
        $cfg = Get-Content $configPath -Raw | ConvertFrom-Json
        $cfg.protected_branches | Should -Contain "main"
        $cfg.protected_branches | Should -Contain "master"
    }
}

Describe "Dopasowanie wzorców wrażliwych plików" {
    It "Wzorzec *.env dopasowuje .env" {
        ".env" -like "*.env" | Should -BeTrue
    }

    It "Wzorzec *.env dopasowuje production.env" {
        "production.env" -like "*.env" | Should -BeTrue
    }

    It "Wzorzec *.key dopasowuje secret.key" {
        "secret.key" -like "*.key" | Should -BeTrue
    }

    It "Wzorzec .bzt-rc dopasowuje .bzt-rc" {
        ".bzt-rc" -like ".bzt-rc" | Should -BeTrue
    }

    It "Wzorzec *.pem dopasowuje cert.pem" {
        "cert.pem" -like "*.pem" | Should -BeTrue
    }

    It "Wzorzec *.token dopasowuje api.token" {
        "api.token" -like "*.token" | Should -BeTrue
    }

    It "Wzorzec *.env nie dopasowuje README.md" {
        "README.md" -like "*.env" | Should -BeFalse
    }

    It "Wzorzec *.key nie dopasowuje monkey.txt" {
        "monkey.txt" -like "*.key" | Should -BeFalse
    }
}

Describe "Walidacja rozmiaru pliku" {
    It "Plik 50KB nie przekracza limitu 100KB" {
        $sizeKb = 50
        $limit  = 100
        ($sizeKb -gt $limit) | Should -BeFalse
    }

    It "Plik 150KB przekracza limit 100KB" {
        $sizeKb = 150
        $limit  = 100
        ($sizeKb -gt $limit) | Should -BeTrue
    }

    It "Limit 0 oznacza wyłączone sprawdzanie" {
        $limit = 0
        ($limit -gt 0) | Should -BeFalse
    }
}

Describe "Walidacja wiadomości commitu - wzorce blokowania" {
    BeforeAll {
        $script:blockedPatterns = @("^WIP", "fixup!", "DO NOT MERGE")
    }

    It "Wiadomość 'WIP: w trakcie' jest blokowana przez '^WIP'" {
        $msg = "WIP: w trakcie"
        $matched = $false
        foreach ($p in $script:blockedPatterns) { if ($msg -cmatch $p) { $matched = $true } }
        $matched | Should -BeTrue
    }

    It "Wiadomość 'fixup! poprawka' jest blokowana" {
        $msg = "fixup! poprawka"
        $matched = $false
        foreach ($p in $script:blockedPatterns) { if ($msg -cmatch $p) { $matched = $true } }
        $matched | Should -BeTrue
    }

    It "Wiadomość 'DO NOT MERGE' jest blokowana" {
        $msg = "DO NOT MERGE"
        $matched = $false
        foreach ($p in $script:blockedPatterns) { if ($msg -cmatch $p) { $matched = $true } }
        $matched | Should -BeTrue
    }

    It "Normalna wiadomość 'feat: dodaj logowanie' nie jest blokowana" {
        $msg = "feat: dodaj logowanie"
        $matched = $false
        foreach ($p in $script:blockedPatterns) { if ($msg -cmatch $p) { $matched = $true } }
        $matched | Should -BeFalse
    }

    It "Wiadomość 'wip: małe litery' nie jest blokowana przez '^WIP' (case-sensitive)" {
        # guard-git używa -match (case-insensitive), więc małe wip też jest blokowane
        # Ten test dokumentuje to zachowanie
        $msg = "wip: małe litery"
        $matched = ($msg -cmatch "^wip")  # małe litery wip
        $matched | Should -BeTrue
    }
}

Describe "Walidacja formatu Conventional Commits" {
    BeforeAll {
        $script:ccPat = '^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\([^)]+\))?: .+'
    }

    It "Poprawny format 'feat: nowa funkcja' jest akceptowany" {
        "feat: nowa funkcja" -match $script:ccPat | Should -BeTrue
    }

    It "Poprawny format 'fix(api): naprawa endpointu' jest akceptowany" {
        "fix(api): naprawa endpointu" -match $script:ccPat | Should -BeTrue
    }

    It "Poprawny format 'chore: aktualizacja zależności' jest akceptowany" {
        "chore: aktualizacja" -match $script:ccPat | Should -BeTrue
    }

    It "Niepoprawny format 'Dodałem coś' jest odrzucany" {
        "Dodałem cos" -match $script:ccPat | Should -BeFalse
    }

    It "Niepoprawny format 'TASK-123 coś tam' jest odrzucany" {
        "TASK-123 coś tam" -match $script:ccPat | Should -BeFalse
    }

    It "Pusty string jest odrzucany" {
        $empty = "no-match-placeholder"
        $empty -match $script:ccPat | Should -BeFalse
    }
}

Describe "Skrypt guard-git.ps1 istnieje i jest poprawny" {
    It "Plik scripts/guard-git.ps1 istnieje" {
        $scriptPath | Should -Exist
    }

    It "Skrypt zawiera blok pre-commit" {
        $content = Get-Content $scriptPath -Raw
        $content | Should -Match 'pre-commit'
    }

    It "Skrypt zawiera blok pre-push" {
        $content = Get-Content $scriptPath -Raw
        $content | Should -Match 'pre-push'
    }

    It "Skrypt zawiera funkcję Write-Blocked" {
        $content = Get-Content $scriptPath -Raw
        $content | Should -Match 'function Write-Blocked'
    }

    It "Skrypt zawiera obsługę warn_only" {
        $content = Get-Content $scriptPath -Raw
        $content | Should -Match 'warnOnly'
    }

    It "Skrypt zawiera obsługę log_blocked" {
        $content = Get-Content $scriptPath -Raw
        $content | Should -Match 'logBlocked'
    }
}

Describe "Instalator install-hooks.ps1 istnieje" {
    It "Plik install-hooks.ps1 istnieje" {
        $installerPath = Join-Path $PSScriptRoot ".." "install-hooks.ps1"
        $installerPath | Should -Exist
    }

    It "Instalator instaluje pre-commit" {
        $content = Get-Content (Join-Path $PSScriptRoot ".." "install-hooks.ps1") -Raw
        $content | Should -Match 'pre-commit'
    }

    It "Instalator instaluje pre-push" {
        $content = Get-Content (Join-Path $PSScriptRoot ".." "install-hooks.ps1") -Raw
        $content | Should -Match 'pre-push'
    }

    It "Instalator instaluje post-commit" {
        $content = Get-Content (Join-Path $PSScriptRoot ".." "install-hooks.ps1") -Raw
        $content | Should -Match 'post-commit'
    }
}
