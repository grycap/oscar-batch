#!/bin/sh

JSON_TEST=$(cat "$INPUT_FILE_PATH")
echo $JSON_TEST

START=$(echo "$JSON_TEST" | jq '.start')
END=$(echo "$JSON_TEST" | jq '.end')

echo "Start: $START"
echo "End: $END"

python3 fish_detector.py -i "$BUCKET_DIR/input/index.txt" -d "$BUCKET_DIR" --start "$START" --end "$END" -o "$BUCKET_DIR/output"

echo "Processed image saved to: $TMP_OUTPUT_DIR/$IMAGE_NAME"
echo "Detection results saved to: $TMP_OUTPUT_DIR/${IMAGE_NAME%.*}.json"