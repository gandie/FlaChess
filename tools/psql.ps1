[CmdletBinding(DefaultParameterSetName = "Query")]
param(
    [Parameter(Mandatory = $true, Position = 0, ParameterSetName = "Query")]
    [string] $Query,

    [Parameter(Mandatory = $true, Position = 0, ParameterSetName = "File")]
    [ValidateScript({ Test-Path -LiteralPath $_ -PathType Leaf })]
    [string] $File
)

$dockerArguments = @(
    "compose",
    "exec",
    "-T",
    "postgres",
    "psql",
    "-U",
    "fla_chess",
    "-d",
    "fla_chess",
    "-v",
    "ON_ERROR_STOP=1"
)

if ($PSCmdlet.ParameterSetName -eq "File") {
    Get-Content -LiteralPath $File -Raw | & docker @dockerArguments
}
else {
    $dockerArguments += @("-c", $Query)
    & docker @dockerArguments
}

if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
