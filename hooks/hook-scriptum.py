from PyInstaller.utils.hooks import collect_data_files

# Include Scriptum JSON tables and other bundled resources in the standalone binary.
datas = collect_data_files("scriptum")
