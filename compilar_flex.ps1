# Ejecutar con WinFlexBison y gcc (MSYS2) en PATH.
$ErrorActionPreference = 'Stop'
$gccCommand = Get-Command gcc -ErrorAction Stop
$flexCommand = Get-Command win_flex -ErrorAction Stop
$pythonCommand = Get-Command py -ErrorAction SilentlyContinue
$pythonArgs = @('-3')
if (-not $pythonCommand) {
    $pythonCommand = Get-Command python -ErrorAction Stop
    $pythonArgs = @()
}
$previousPath = $env:Path
Push-Location $PSScriptRoot
try {
    # Priorizar las DLL del mismo GCC evita conflictos con otras herramientas.
    $env:Path = (Split-Path $gccCommand.Source) + ';' + $previousPath
    & $flexCommand.Source -o flex/lex.yy.c flex/lexer.l
    if ($LASTEXITCODE -ne 0) { throw 'Falló win_flex. Revisa WinFlexBison en PATH.' }
    & $gccCommand.Source flex/lex.yy.c -o flex/mini_lexer.exe
    if ($LASTEXITCODE -ne 0) { throw 'Falló gcc. Revisa MSYS2/GCC en PATH.' }
    Write-Host 'FLEX compilado correctamente: flex/mini_lexer.exe'
    & $pythonCommand.Source @pythonArgs cli.py ejemplos/demo.java --lexer flex --out ejecucion
    if ($LASTEXITCODE -ne 0) { throw 'Falló la prueba de integración con FLEX.' }
}
finally {
    $env:Path = $previousPath
    Pop-Location
}
