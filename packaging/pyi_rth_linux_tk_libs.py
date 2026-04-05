# PyInstaller runtime hook: Tcl/Tk .so (libtcl9.0.so) в _internal и во вложенных каталогах.
import os
import sys

if sys.platform.startswith("linux") and getattr(sys, "frozen", False):
    me = sys._MEIPASS
    lib_dirs = [me]
    try:
        for name in os.listdir(me):
            p = os.path.join(me, name)
            if os.path.isdir(p):
                lib_dirs.append(p)
    except OSError:
        pass
    cur = os.environ.get("LD_LIBRARY_PATH", "")
    parts = [p for p in cur.split(os.pathsep) if p]
    for d in reversed(lib_dirs):
        if d not in parts:
            parts.insert(0, d)
    os.environ["LD_LIBRARY_PATH"] = os.pathsep.join(parts)
