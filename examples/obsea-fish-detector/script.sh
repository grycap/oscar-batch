#!/bin/sh

JSON=$(cat "$INPUT_FILE_PATH")
echo $JSON

START=$(echo "$JSON" | jq '.start')
END=$(echo "$JSON" | jq '.end')

python3 fish_detector.py -i "$BUCKET_DIR/input/index.txt" -d "$BUCKET_DIR" --start "$START" --end "$END" -o "$BUCKET_DIR/output"
