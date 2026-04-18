param(
    [ValidateSet('health', 'standard', 'jmeter-java8', 'pipeline')]
    [string]$Mode = 'health'
)

$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$python = Join-Path $repoRoot '.venv/Scripts/python.exe'
$bzt = Join-Path $repoRoot '.venv/Scripts/bzt.exe'
$java8 = Join-Path $repoRoot 'tools/jdk8u482-b08'

function Assert-Exists([string]$Path, [string]$Label) {
    if (-not (Test-Path $Path)) {
        throw "$Label not found: $Path"
    }
}

Assert-Exists $python 'Python interpreter'
Assert-Exists $bzt 'Taurus executable'

switch ($Mode) {
    'health' {
        & $python -V
        & $python -m pip show bzt setuptools pyyaml
        & $python -m pip check
        & $bzt -h
        break
    }

    'standard' {
        & $bzt test-api.yml
        break
    }

    'jmeter-java8' {
        Assert-Exists $java8 'Java 8 directory'
        $env:JAVA_HOME = $java8
        $env:Path = "$($env:JAVA_HOME)/bin;" + $env:Path
        & $bzt test-api.yml -o execution.0.executor=jmeter
        break
    }

    'pipeline' {
        Write-Host '[1/3] Health check...'
        & $python -V
        & $python -m pip show bzt setuptools pyyaml
        & $python -m pip check

        Write-Host '[2/3] Standard API run...'
        & $bzt test-api.yml

        Write-Host '[3/3] JMeter + Java8 run...'
        Assert-Exists $java8 'Java 8 directory'
        $env:JAVA_HOME = $java8
        $env:Path = "$($env:JAVA_HOME)/bin;" + $env:Path
        & $bzt test-api.yml -o execution.0.executor=jmeter
        break
    }
}
