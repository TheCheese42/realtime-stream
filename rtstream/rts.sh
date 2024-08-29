#!/bin/bash

server="{host}"

if [ $1 ]; then
    uuid=$1
else
    uuid=$(curl -s -X POST "${server}/c")
    echo "[RTS] Created new stream with uuid ${uuid}"
fi

while read -r output; do
    $(curl -s -X PATCH -d "${output}
" "${server}/a/${uuid}" > /dev/null)
    echo ${output}
done
