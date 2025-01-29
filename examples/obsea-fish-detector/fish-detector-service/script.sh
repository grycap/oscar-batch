#!/bin/sh

FILE_NAME=`basename "$INPUT_FILE_PATH"`
OUTPUT_FILE="$TMP_OUTPUT_DIR/$FILE_NAME"

JSON=$(cat "$INPUT_FILE_PATH")
echo $JSON

ZIP_FILE=$(echo "$JSON" | jq -r '.zip_file')

python3 fish_detector.py -i "$BUCKET_DIR/$ZIP_FILE" -o "$OUTPUT_FILE"

echo $?
