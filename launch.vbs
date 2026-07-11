' Launches the MarketWatch config UI with no visible console window,
' then opens it in the default browser.
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

appDir = fso.GetParentFolderName(WScript.ScriptFullName)

' 0 = hidden window, False = don't wait for it to exit
shell.CurrentDirectory = appDir
shell.Run "cmd /c cd /d """ & appDir & """ && python app.py", 0, False

WScript.Sleep 1500
shell.Run "http://localhost:5000", 1, False
