# Lista (y opcionalmente borra) los deployments FALLIDOS del repo en GitHub.
# Requiere `gh auth login`. Sin -Borrar solo muestra lo que borraría.
#   .\tools\deploys_fallidos.ps1            # vista previa
#   .\tools\deploys_fallidos.ps1 -Borrar    # borra solo los fallidos (permanente)
param([switch]$Borrar)

$repo = "jorgefajardom-coder/Ai-builders-Hackaton"
# En Windows PowerShell 5.1, ConvertFrom-Json devuelve una lista JSON como UN objeto: se envuelve en @()
# y se indexa para obtener elementos reales (Select-Object -First 1 devolvía la lista entera).
$deploys = @(gh api "repos/$repo/deployments?per_page=100" | ConvertFrom-Json)
if ($deploys.Count -eq 1 -and $deploys[0] -is [array]) { $deploys = $deploys[0] }
$fallidos = @()
foreach ($d in $deploys) {
    $statuses = @(gh api "repos/$repo/deployments/$($d.id)/statuses" | ConvertFrom-Json)
    if ($statuses.Count -eq 1 -and $statuses[0] -is [array]) { $statuses = $statuses[0] }
    $estado = if ($statuses.Count -gt 0) { $statuses[0].state } else { "" }
    if ($estado -in @("failure", "error")) { $fallidos += $d }
}

Write-Host "Deployments fallidos: $($fallidos.Count) de $($deploys.Count)"
foreach ($d in $fallidos) { Write-Host ("  {0}  {1}  {2}  {3}" -f $d.id, $d.environment, $d.sha.Substring(0, 7), $d.created_at) }

if (-not $Borrar) { Write-Host "`nVista previa: no se borró nada. Para borrar: .\tools\deploys_fallidos.ps1 -Borrar"; exit 0 }

foreach ($d in $fallidos) {
    gh api -X POST "repos/$repo/deployments/$($d.id)/statuses" -f state=inactive | Out-Null
    gh api -X DELETE "repos/$repo/deployments/$($d.id)"
    Write-Host "borrado $($d.id)"
}
