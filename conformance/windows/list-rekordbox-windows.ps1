$source = @'
using System;
using System.Runtime.InteropServices;
using System.Text;

public static class WindowInspector
{
    public delegate bool EnumWindowsProc(IntPtr handle, IntPtr parameter);

    [DllImport("user32.dll")]
    public static extern bool EnumWindows(EnumWindowsProc callback, IntPtr parameter);

    [DllImport("user32.dll")]
    public static extern uint GetWindowThreadProcessId(IntPtr handle, out uint processId);

    [DllImport("user32.dll", CharSet = CharSet.Unicode)]
    public static extern int GetWindowText(IntPtr handle, StringBuilder text, int maximum);

    [DllImport("user32.dll", CharSet = CharSet.Unicode)]
    public static extern int GetClassName(IntPtr handle, StringBuilder text, int maximum);

    [DllImport("user32.dll")]
    public static extern bool IsWindowVisible(IntPtr handle);
}
'@

Add-Type -TypeDefinition $source

$processIds = @(Get-Process rekordbox -ErrorAction Stop | Select-Object -ExpandProperty Id)
$windows = [System.Collections.Generic.List[object]]::new()
$callback = [WindowInspector+EnumWindowsProc] {
    param([IntPtr]$handle, [IntPtr]$parameter)

    $processId = 0
    [void][WindowInspector]::GetWindowThreadProcessId($handle, [ref]$processId)
    if ($processIds -notcontains $processId) {
        return $true
    }

    $title = [Text.StringBuilder]::new(1024)
    $class = [Text.StringBuilder]::new(256)
    [void][WindowInspector]::GetWindowText($handle, $title, $title.Capacity)
    [void][WindowInspector]::GetClassName($handle, $class, $class.Capacity)
    $windows.Add([pscustomobject]@{
        Handle = $handle.ToInt64()
        ProcessId = $processId
        Visible = [WindowInspector]::IsWindowVisible($handle)
        Class = $class.ToString()
        Title = $title.ToString()
    })

    return $true
}

[void][WindowInspector]::EnumWindows($callback, [IntPtr]::Zero)
$windows | Sort-Object Handle | ConvertTo-Json
