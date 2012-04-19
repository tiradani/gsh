#!/bin/bash

set -o noglob
usage='usage: make_release.sh release_name <gsh_source_location> <gsh_release_location>'

show_tags()
{
    echo "Available releases are: "
    echo
    git tag
}

if [ -z "$2" ] ; then
    if [ -z "$GSH_SRC_LOCATION" ] ; then
        echo 'please set GSH_SRC_LOCATION in the environment or as an argument before proceeding'
        echo
        echo $usage
        exit 1
    fi
else
    export GSH_SRC_LOCATION=$2
fi

cd $GSH_SRC_LOCATION

if [ -z "$1" ] ; then
    echo $usage
    show_tags
    exit 2
fi

releasename=$1


if [ -z "$3" ] ; then
    if [ -z "$GSH_RELEASE_LOCATION" ] ; then
        export GSH_RELEASE_LOCATION=/tmp
    fi
else
    export GSH_RELEASE_LOCATION=$3
fi

git show-ref --verify refs/tags/$releasename >& /dev/null
if [ $? -ne 0 ]; then
    echo "Can't find $releasename."
    show_tags
    exit 3
fi

tarball=${GSH_RELEASE_LOCATION}/${releasename}.tar
git archive --format=tar --prefix=$releasename/ $releasename > ${tarball}
gzip -f ${tarball}

mkdir ${releasename}
mv ${tarball}.gz ${GSH_RELEASE_LOCATION}/${releasename}/gsh.tar.gz
