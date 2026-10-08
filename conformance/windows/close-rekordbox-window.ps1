param(
    [Parameter(Mandatory = $true)]
    [string]$Title
)

$source = @'
using System;
using System.Runtime.InteropServices;
using System.Text;

public static class RekordboxWindowCloser
{
    public delegate bool EnumWindowsProc(IntPtr handle, IntPtr parameter);

    [DllImport("user32.dll")]
    public static extern bool EnumWindows(EnumWindowsProc callback, IntPtr parameter);

    [DllImport("user32.dll")]
    public static extern uint GetWindowThreadProcessId(IntPtr handle, out uint processId);

    [DllImport("user32.dll", CharSet = CharSet.Unicode)]
    public static extern int GetWindowText(IntPtr handle, StringBuilder text, int maximum);

    [DllImport("user32.dll")]
    public static extern bool PostMessage(IntPtr handle, uint message, IntPtr wParam, IntPtr lParam);
}
'@

Add-Type -TypeDefinition $source

$processIds = @(Get-Process rekordbox -ErrorAction Stop | Select-Object -ExpandProperty Id)
$closed = [System.Collections.Generic.List[object]]::new()
$callback = [RekordboxWindowCloser+EnumWindowsProc] {
    param([IntPtr]$handle, [IntPtr]$parameter)

    $processId = 0
    [void][RekordboxWindowCloser]::GetWindowThreadProcessId($handle, [ref]$processId)
    if ($processIds -notcontains $processId) {
        return $true
    }

    $windowTitle = [Text.StringBuilder]::new(1024)
    [void][RekordboxWindowCloser]::GetWindowText($handle, $windowTitle, $windowTitle.Capacity)
    if ($windowTitle.ToString() -ne $Title) {
        return $true
    }

    $posted = [RekordboxWindowCloser]::PostMessage(
        $handle,
        0x0010,
        [IntPtr]::Zero,
        [IntPtr]::Zero
    )
    $closed.Add([pscustomobject]@{
        Handle = $handle.ToInt64()
        ProcessId = $processId
        Title = $windowTitle.ToString()
        ClosePosted = $posted
    })

    return $true
}

[void][RekordboxWindowCloser]::EnumWindows($callback, [IntPtr]::Zero)
$closed | ConvertTo-Json
