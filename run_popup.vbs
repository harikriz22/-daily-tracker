Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\Users\harik\OneDrive\Desktop\daily tasks and work\daily_tracker"
extra = ""
If WScript.Arguments.Count > 0 Then extra = " " & WScript.Arguments(0)
WshShell.Run """C:\Users\harik\OneDrive\Desktop\daily tasks and work\daily_tracker\.venv\Scripts\pythonw.exe"" ""C:\Users\harik\OneDrive\Desktop\daily tasks and work\daily_tracker\daily_popup.py""" & extra, 0, False
