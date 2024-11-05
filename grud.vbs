Set oShell = CreateObject ("Wscript.Shell")
Dim strArgs
strArgs = "cmd /c grud.bat"
oShell.Run strArgs, 0, false
