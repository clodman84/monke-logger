import sys

from cx_Freeze import Executable, setup

build_options = {
    "includes": ["database"],
    "excludes": [
        "asyncio",
        "concurrent",
        "distutils",
        "email",
        "html",
        "http",
        "lib2to3",
        "multiprocessing",
        "urllib",
        "xml",
        "unittest",
    ],
}

base = "Win32GUI" if sys.platform == "win32" else None

executables = [Executable("d_gui.py", base=base, target_name="MonkeLogger")]

setup(
    name="MonkeLogger",
    version="0.1",
    description="MonkeLogger",
    options={"build_exe": build_options},
    executables=executables,
)
