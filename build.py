import sys
sys.path.append(".")
from build_colmesh import build_colmesh
from build_common import build_error
from build_drm import build_drm
import os
import subprocess

# much hardcode very wow
mkloadob_exe_path = "/mnt/d/Programming/Projects/cdc_lib/build_win/tools/resource_mkloadob/cdc_lib_resource_mkloadob.exe"
clean_build = False
did_something = False

def needs_rebuild(src, dest):
    if not os.path.exists(src):
        return True
    if clean_build:
        return True

    src_date = os.path.getmtime(src)
    dest_date = os.path.getmtime(dest)
    if src_date > dest_date:
        did_something = True
        return True
    return False

def build_ob(name, dest):
    if mkloadob_exe_path is None:
        build_error("You have not specified a path to mkloadob.exe!")
    if not needs_rebuild(name, dest):
        return
    process = subprocess.run([mkloadob_exe_path, name, dest], capture_output=True)
    if process.returncode != 0:
        print(process.stdout.decode("utf-8"))
        print(process.stderr.decode("utf-8"))
        build_error("Failed to build '{}'\nCheck output above for errors".format(name))
    print("Rebuilt '{}'".format(name))

buildlist_file = "buildlist.txt"
if len(sys.argv) > 1:
    if sys.argv[1] == "-clean":
        clean_build = True
        if len(sys.argv) > 2:
            buildlist_file = sys.argv[2]
    else:
        buildlist_file = sys.argv[1]

with open(buildlist_file, "r") as f:
    for line in f:
        line = line.strip()
        if len(line) == 0 or line.startswith(";"):
            continue
        s = line.split()
        if len(s) < 3:
            build_error("Invalid line in buildlist: '{}'".format(line))
        process_name, src, dest = s
        if process_name == "copy":
            if not needs_rebuild(src, dest):
                continue
            shutil.copyfile(src, dest)
        elif process_name == "mkloadob":
            build_ob(src, dest)
        elif process_name == "colmesh":
            if not needs_rebuild(src, dest):
                continue
            build_colmesh(src, dest)
        elif process_name == "drm":
            build_drm(src, dest)
        else:
            build_error("Unknown process '{}'".format(process_name))

if not did_something:
    print("Nothing to do!")
