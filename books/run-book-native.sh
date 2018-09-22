#!/usr/bin/env bash
# language=sh
#set -u
set -eo pipefail
#set -x # echo commands

echo run-book-native.sh called with arguments "$@"

short=$1
src=$2
resources=$3
newpwd=$4

echo short: ${short}
echo src: ${src}
echo resources: ${resources}
echo PWD: ${PWD}
echo newpwd: ${newpwd}

cd ${newpwd}

if [ "$CI" = "" ]
then
   branch=`git rev-parse --abbrev-ref HEAD`
else
   branch=${CIRCLE_BRANCH}
fi

org=`git config --get remote.origin.url | cut -f2 -d":"  | cut -f1 -d/ | tr '[:upper:]' '[:lower:]'`

toplevel=`git -C ${src} rev-parse --show-toplevel`
repo=`basename ${toplevel}`

base=http://docs-branches.duckietown.org/${org}/${repo}/branch/${branch}
cross=${base}/all_crossref.html
permalink_prefix=${base}/${short}/out



if [ "$CI" = "" ]
then
   echo "Not on Circle, using parallel compilation."
   cmd="rparmake n=4"
else
   echo "On Circle, not using parallel compilation to avoid running out of memory."
   cmd=rmake

fi

options1=""
#extra_crossrefs=${base}/all_crossref.html
#options1="--extra_crossrefs ${extra_crossrefs}"


dist=duckuments-dist

if [ "$ONLY_FOR_REFS" = "" ]
then
   options2="--output_file ${dist}/${short}/out.html --split ${dist}/${short}/out/"

else
   echo "Skipping polish, ONLY_FOR_REFS"

   # XXX: need to do split because of cross refs
   options2="--split ${dist}/${short}/out/ --ignore_ref_errors --only_refs"
fi

# only andrea and CI build the PDF version

if [ "$USER" = "andrea" ]
then
    options2="${options2} --pdf ${dist}/${short}/out.pdf"
fi

if [ "$CI" = "" ]
then
   echo
else
   options2="${options2} --pdf ${dist}/${short}/out.pdf"
fi


mkdir -p ${dist}

NP=${PWD}/node_modules:${NODE_PATH}

echo Running in dir ${PWD}
#    --likebtn 5ae54e0d6fd08bb24f3a7fa1 \

echo DISABLE_CONTRACTS=1 NODE_PATH=${NP}  mcdp-render-manual \
    --src "${src}" \
    --bookshort "${short}" \
    --resources ${resources}:${dist} \
    --stylesheet v_manual_split \
    --stylesheet_pdf v_manual_blurb_ready \
    --wordpress_integration \
    --output_crossref ${dist}/${short}/crossref.html \
    -o out/${short} \
    --permalink_prefix ${permalink_prefix} \
    ${options1} \
    ${options2} \
    ${EXTRA_MCDP_RENDER_OPTIONS} \
    -c "config echo 1; ${cmd}"

DISABLE_CONTRACTS=1 NODE_PATH=${NP}  mcdp-render-manual \
    --src "${src}" \
    --bookshort "${short}" \
    --resources ${resources}:${dist} \
    --stylesheet v_manual_split \
    --stylesheet_pdf v_manual_blurb_ready \
    --wordpress_integration \
    --output_crossref ${dist}/${short}/crossref.html \
    -o out/${short} \
    --permalink_prefix ${permalink_prefix} \
    ${options1} \
    ${options2} \
    ${EXTRA_MCDP_RENDER_OPTIONS} \
    -c "config echo 1; ${cmd}"
#    --symbols docs/symbols.tex \

DISABLE_CONTRACTS=1 python -m mcdp_docs.make_index resources/books.yaml \
    duckuments-dist/index.html \
    duckuments-dist/all_crossref.html \
    duckuments-dist/errors_and_warnings.pickle
