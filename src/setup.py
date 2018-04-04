from cx_Freeze import setup, Executable

exe_options = {
    "includes": ["ui"],
    "include_files": ["res"],
    "optimize": 2,
}

setup(
    name="StudiLog",
    version="0.1",
    description="",
    options={"build_exe": exe_options},
    executables = [Executable("main.py", base="Win32GUI")]
)
