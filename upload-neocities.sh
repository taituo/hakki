#!/bin/bash
# Lataa site/-kansion Neocitiesiin. Avain ympäristömuuttujasta (ei talleteta mihinkään):
#   NEOCITIES_KEY=<avain-neocities.org/settings> ./upload-neocities.sh
set -u
KEY="${NEOCITIES_KEY:?Aseta NEOCITIES_KEY ympäristömuuttujaan}"
API="https://neocities.org/api"
BATCH=15
n=0
args=()

flush() {
  if ((${#args[@]})); then
    echo "--- lähetetään erä ($n tiedostoa jonossa) ---"
    curl -sS -m 180 -H "Authorization: Bearer $KEY" "${args[@]}" "$API/upload"
    echo
    args=()
  fi
}

while IFS= read -r -d '' f; do
  srv="${f#site/}"
  args+=(-F "$srv=@$f")
  n=$((n + 1))
  if ((n % BATCH == 0)); then flush; fi
done < <(find site -type f -print0 | sort -z)
flush

echo "--- palvelimella nyt ---"
curl -sS -m 30 -H "Authorization: Bearer $KEY" "$API/list" | python3 -c "
import json,sys
d=json.load(sys.stdin)
fs=d.get('files',[])
print('tiedostoja:',len(fs))
print('index.html:', any(f.get('path')=='index.html' for f in fs))
"
