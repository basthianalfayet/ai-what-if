param(
    [string]$JamPagi = "07:00",
    [string]$JamSiang = "12:00",
    [string]$JamSore = "16:00",
    [string]$JamMalam = "19:00",
    [string]$JamLarut = "21:00",
    [switch]$Hapus
)

$jadwal = @{
    "KerjaPakaiAI Pagi" = @("pagi", $JamPagi)
    "KerjaPakaiAI Siang" = @("siang", $JamSiang)
    "KerjaPakaiAI Sore" = @("sore", $JamSore)
    "KerjaPakaiAI Malam" = @("malam", $JamMalam)
    "KerjaPakaiAI Larut" = @("larut", $JamLarut)
}

if ($Hapus) {
    foreach ($nama in $jadwal.Keys) { Unregister-ScheduledTask -TaskName $nama -Confirm:$false -ErrorAction SilentlyContinue }
    Write-Host "Jadwal KerjaPakaiAI dihapus."
    return
}

$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -RunOnlyIfNetworkAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 1)

foreach ($nama in $jadwal.Keys) {
    $slot, $jam = $jadwal[$nama]
    $action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"`"$dir\run_daily.bat`" $slot`"" -WorkingDirectory $dir
    $trigger = New-ScheduledTaskTrigger -Daily -At $jam
    Register-ScheduledTask -TaskName $nama -Action $action -Trigger $trigger -Settings $settings `
        -Description "Bikin video KerjaPakaiAI slot $slot" -Force | Out-Null
    Write-Host "Jadwal '$nama' terpasang: tiap hari jam $jam."
}
Write-Host "Kalau laptop mati di jam itu, video dibuat begitu laptop menyala lagi."
