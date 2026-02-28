MKLOADOB="/mnt/d/Programming/Projects/cdc_lib/build_win/tools/resource_mkloadob/cdc_lib_resource_mkloadob.exe"

build_ob () {
    name=$1
    dest=$2
    if test ${name} -nt ${dest} || [ ! -f ${dest} ]
    then
        ${MKLOADOB} ${name} ${dest}
        RESULT=$?
        if [ $RESULT -ne 0 ]
        then
            echo ""
            echo "BUILD ERROR!"
            echo "Failed to build '${name}'"
            echo "Check output above for errors!"
            exit 1
        fi
        echo "Rebuilt '${name}'"
    fi
}

mkdir -p customlevel_bin/pc-w

build_ob level-level.txtdat level-level.dat
build_ob level-zadmd.txtdat level-zadmd.dat
build_ob level-cellgroup.txtdat level-cellgroup.dat
build_ob level-meshimf.txtdat level-meshimf.dat
# TODO: this only needs to be rebuilt if level-mesh.obj changes
python3 build-colmesh.py level-cmesh.obj level-cmesh.cmeshtxt
build_ob level-cmesh.cmeshtxt level-cmesh.dat
build_ob level-tg1.txtdat level-tg1.dat
build_ob level.txtdat level.dat
cp objlist.dat customlevel_bin/pc-w/objlist.dat
python3 build-drm.py mytestlevel.txtdrm customlevel_bin/pc-w/mytestlevel.drm
