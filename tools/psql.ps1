param(
    [Parameter(Mandatory = $true)]
    [string] $Query
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
    "ON_ERROR_STOP=1",
    "-c",
    $Query
)

& docker @dockerArguments

if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
