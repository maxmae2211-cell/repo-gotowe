param(
    [ValidateSet('health', 'standard', 'jmeter-java8', 'pipeline')]
    [string]$Mode = 'health',
    [string]$Config = 'test-api.yml'
)

$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

# Taurus installed globally in Python310 (see gettaurus.org/install/Installation/ - Windows)
$python = "C:\Users\maxma\AppData\Local\Programs\Python\Python310\python.exe"
$bzt    = "C:\Users\maxma\AppData\Local\Programs\Python\Python310\Scripts\bzt.exe"
$java8  = Join-Path $repoRoot 'tools/jdk8u482-b08'
$configPath = Join-Path $repoRoot $Config

function Assert-Exists([string]$Path, [string]$Label) {
    if (-not (Test-Path $Path)) {
        throw "$Label not found: $Path"
    }
}

Assert-Exists $python 'Python interpreter'
Assert-Exists $bzt 'Taurus executable'
Assert-Exists $configPath 'Taurus config file'

switch ($Mode) {
    'health' {
        & $python -V
        & $python -m pip show bzt setuptools pyyaml
        & $python -m pip check
        & $bzt -h
        break
    }

    'standard' {
        & $bzt $configPath
        break
    }

    'jmeter-java8' {
        Assert-Exists $java8 'Java 8 directory'
        $env:JAVA_HOME = $java8
        $env:Path = "$($env:JAVA_HOME)/bin;" + $env:Path
        & $bzt $configPath -o execution.0.executor=jmeter
        break
    }

    'pipeline' {
        Write-Host '[1/3] Health check...'
        & $python -V
        & $python -m pip show bzt setuptools pyyaml
        & $python -m pip check

        Write-Host '[2/3] Standard API run...'
        & $bzt $configPath

        Write-Host '[3/3] JMeter + Java8 run...'
        Assert-Exists $java8 'Java 8 directory'
        $env:JAVA_HOME = $java8
        $env:Path = "$($env:JAVA_HOME)/bin;" + $env:Path
        & $bzt $configPath -o execution.0.executor=jmeter
        break
    }
}
