#!/bin/bash
set -x
echo "Inside copy_dir.sh"
src=$1
dst=$2
cmd=${@:3}
echo "src: $src"
echo "dst: $dst"
echo "cmd: $cmd"

mkdir -p $dst

rsync -av --exclude=.git  --exclude=builds  --exclude node_modules --exclude moving-from-google-drive --exclude=builds-fork $src/ $dst/

du -h -s $dst

echo "Now executing command $cmd"
exec "$cmd"
