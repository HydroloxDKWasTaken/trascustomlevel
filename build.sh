MKLOADOB="/mnt/d/Programming/Projects/cdc_lib/build_win/tools/resource_mkloadob/cdc_lib_resource_mkloadob.exe"

build_ob () {
    name=$1
    dest=$2
    if test ${name} -nt ${dest} || [ ! -f ${dest} ]
    then
        ${MKLOADOB} ${name} ${dest}
        echo "Rebuilt '${name}'"
    fi
}

mkdir -p customlevel_bin/pc-w

build_ob level-level.txtdat level-level.dat
build_ob level-zadmd.txtdat level-zadmd.dat
build_ob level.txtdat level.dat
cp objlist.dat customlevel_bin/pc-w/objlist.dat
python3 build-drm.py mytestlevel.txtdrm customlevel_bin/pc-w/mytestlevel.drm
