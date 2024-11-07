Set oShell = CreateObject ("Wscript.Shell")
Dim strArgs

scriptDir = Left(WScript.ScriptFullName, InStrRev(WScript.ScriptFullName, "\") - 1)
oShell.CurrentDirectory = scriptDir

strArgs = "cmd /c grud.bat"
oShell.Run strArgs, 0, false
