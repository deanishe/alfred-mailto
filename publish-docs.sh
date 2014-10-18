#!/bin/sh

# Publish documentation to gh-pages branch using ghp-import

if [[ -z "$1" ]]; then
    echo "You must specify a commit message."
    exit 1
fi

basedir=$(cd $(dirname $0); pwd)
docdir="${basedir}/src/help"

ghp-import -n -p -m "$1" "${docdir}"
