Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\Users\harik\OneDrive\Desktop\daily tasks and work\daily_tracker"
WshShell.Run """C:\Users\harik\OneDrive\Desktop\daily tasks and work\daily_tracker\.venv\Scripts\pythonw.exe"" ""C:\Users\harik\OneDrive\Desktop\daily tasks and work\daily_tracker\daily_popup.py""", 0, False
