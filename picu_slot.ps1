param(
    [ValidateSet("pagi", "siang", "sore", "malam", "larut")]
    [string]$Slot = "pagi",
    [switch]$Uji,
    [string]$Repo = ""
)

if (-not $Repo) {
    Write-Host "Isi -Repo username/nama-repo untuk kanal AI WHAT IF?. Jangan arahkan ke repo kanal lama."
    exit 1
}

# Memicu workflow persis seperti yang dilakukan cron-job.org, untuk mengetes token GitHub.
$aman = Read-Host "Tempel token GitHub (tidak akan terlihat)" -AsSecureString
$token = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($aman))

$inputs = @{ slot = $Slot }
if ($Uji) { $inputs.uji = $true }
$body = @{ ref = "main"; inputs = $inputs } | ConvertTo-Json -Compress

try {
    Invoke-RestMethod -Method Post `
        -Uri "https://api.github.com/repos/$Repo/actions/workflows/video.yml/dispatches" `
        -Headers @{
            Authorization          = "Bearer $token"
            Accept                 = "application/vnd.github+json"
            "X-GitHub-Api-Version" = "2022-11-28"
        } `
        -ContentType "application/json" -Body $body | Out-Null
    Write-Host "Berhasil. Workflow slot '$Slot' dipicu; cek tab Actions di GitHub."
    Write-Host "Body untuk cron-job.org: $body"
} catch {
    $kode = $_.Exception.Response.StatusCode.value__
    switch ($kode) {
        401 { Write-Host "Gagal (401): token salah atau sudah kedaluwarsa." }
        403 { Write-Host "Gagal (403): token belum punya izin Actions: Read and write." }
        404 { Write-Host "Gagal (404): repo tidak ditemukan atau token tidak diberi akses ke repo $Repo." }
        422 { Write-Host "Gagal (422): workflow video.yml di branch main belum punya input slot ini. Sudah di-push?" }
        default { Write-Host "Gagal ($kode): $($_.Exception.Message)" }
    }
}
