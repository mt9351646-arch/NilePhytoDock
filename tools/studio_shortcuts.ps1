param([string]$Version='0.6.1')
$ErrorActionPreference='Stop'
$nileRelease=(Resolve-Path -LiteralPath ('release\NilePhytoDock Studio '+$Version)).Path
$nileExecutable=Join-Path $nileRelease 'NilePhytoDock.exe'
if(-not (Test-Path -LiteralPath $nileExecutable)){throw 'The Studio executable has not been copied yet.'}
Copy-Item -LiteralPath 'app\resources\brand\NilePhytoDock-Studio.ico' -Destination (Join-Path $nileRelease 'NilePhytoDock.ico') -Force
$nileShell=New-Object -ComObject WScript.Shell
$nileShortcutPaths=@((Join-Path $nileRelease 'Start NilePhytoDock Studio.lnk'),(Join-Path ([Environment]::GetFolderPath('Desktop')) ('NilePhytoDock Studio '+$Version+'.lnk')))
foreach($nileShortcutPath in $nileShortcutPaths){
    if(Test-Path -LiteralPath $nileShortcutPath){
        $nileExisting=$nileShell.CreateShortcut($nileShortcutPath)
        if($nileExisting.TargetPath -and $nileExisting.TargetPath -ne $nileExecutable){throw 'A different existing shortcut would be overwritten.'}
    }
    $nileShortcut=$nileShell.CreateShortcut($nileShortcutPath)
    $nileShortcut.TargetPath=$nileExecutable
    $nileShortcut.WorkingDirectory=$nileRelease
    $nileShortcut.IconLocation=(Join-Path $nileRelease 'NilePhytoDock.ico')+',0'
    $nileShortcut.Description=('NilePhytoDock Studio '+$Version+' - Ahmed G Soliman and Malak Taha')
    $nileShortcut.Save()
}
$nileShortcutPaths | ForEach-Object { $nileCheck=$nileShell.CreateShortcut($_); [pscustomobject]@{Shortcut=$_;Target=$nileCheck.TargetPath;Icon=$nileCheck.IconLocation} } | ConvertTo-Json | Set-Content -LiteralPath ('data\validation\release_'+$Version+'\shortcuts.json') -Encoding utf8
Write-Output 'Studio and desktop shortcuts created with explicit icon paths.'
