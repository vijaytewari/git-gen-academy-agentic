$projectDirectory = $PSScriptRoot
Set-Location -LiteralPath $projectDirectory
& "$projectDirectory/.venv64/Scripts/python.exe" -m streamlit run app.py
