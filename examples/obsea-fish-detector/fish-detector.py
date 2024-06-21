#!/usr/bin/env python3
"""
author: Enoc Martínez
institution: Universitat Politècnica de Catalunya (UPC)
email: enoc.martinez@upc.edu
license: MIT
created: 7/5/24
"""
from argparse import ArgumentParser
import os
from datetime import datetime, timezone
from ultralytics import YOLO
from PIL import Image, UnidentifiedImageError
import logging
from logging.handlers import TimedRotatingFileHandler
import time
import json

def get_pic_size(pic: str) -> int:
    """
    Returns the max size of a pic
    :param pic:
    :return: max size (width or height)
    """
    im = Image.open(pic)
    width, height = im.size
    im.close()
    return max(width, height)

def setup_log(name, path="log"):
    """
    Setups the logging module
    :param name: log name (.log will be appended)
    :param path: where the logs will be stored
    :param log_level: log level as string, it can be "debug, "info", "warning" and "error"
    """
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    if not os.path.exists(path):
        os.makedirs(path)

    filename = os.path.join(path, name)
    if not filename.endswith(".log"):
        filename += ".log"

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    log_formatter = logging.Formatter('%(asctime)s.%(msecs)03d %(levelname)-7s: %(message)s',
                                      datefmt='%Y/%m/%d %H:%M:%S')
    handler = TimedRotatingFileHandler(filename, when="midnight", backupCount=7)
    handler.setFormatter(log_formatter)
    logger.addHandler(handler)

    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(log_formatter)
    logger.addHandler(consoleHandler)

    logger.info("")
    logger.info(f"===== {name} =====")

    return logger

def timestamp_from_filename(filename) -> datetime:
    """
    Gets a timestamp from a filename
    :param filename:
    :return: datetime object
    """
    found = True

    # Let's assume that year 20XX can be used as a locator
    # Try to get datetime as

    idx = filename.find("20")
    if idx > -1:
        # try to parse datetime as YYYYmmdd-HHMMSS
        timestamp = datetime.strptime(filename[idx:idx+15], "%Y%m%d-%H%M%S")
        timestamp = timestamp.replace(tzinfo=timezone.utc)
        found = True

    if not found:
        raise ValueError("Could not find timestamp!")

    return timestamp

def yolov8_result_to_list(results, save_image=""):
    # Process results list
    for result in results:

        boxes = result.boxes  # Boxes object for bbox outputs
        if save_image:
            im_array = result.plot(line_width=1)  # plot a BGR numpy array of predictions
            im = Image.fromarray(im_array[..., ::-1])  # RGB PIL image
            im.save(save_image)  # save image

        detections = []
        for box in boxes:
            cls = int(box.cls)
            taxa = result.names[cls]
            confidence = round(float(box.conf), 3)
            bb = []
            for x in box.xyxyn[0]:
                bb.append(round(float(x), 3))
            detections.append({"taxa": taxa, "confidence": confidence, "bounding_box_xyxy": bb})
    return detections

if __name__ == "__main__":
    argparser = ArgumentParser()
    argparser.add_argument("-i", "--input", type=str, help="input text file with image filenames", required=True)
    argparser.add_argument("-d", "--dir", type=str, help="directory containing the images", required=True)
    argparser.add_argument("-o", "--output", type=str, help="output folder", default="output")
    argparser.add_argument("--model", type=str, help="YOLOv8 model", default="yolov8x_obsea_19sp_2538img.pt")
    argparser.add_argument("--start", type=int, help="start index", default=0)
    argparser.add_argument("--end", type=int, help="end index", default=None)
    args = argparser.parse_args()
    log = setup_log("YOLO")

    log.info("Loading model...")
    t = time.time()
    model = YOLO(args.model)
    log.info(f"Model load time {time.time() - t :.03f} secs")

    os.makedirs(args.output, exist_ok=True)

    # Read image paths from input file
    with open(args.input, 'r') as f:
        filenames = [line.strip() for line in f]

    args.start = args.start - 1 

    # Apply range filter
    if args.end is None:
        args.end = len(filenames)
    filenames = filenames[args.start:args.end]
    log.info(f"Applying {args.model} to {len(filenames)} files")

    files = [os.path.join(args.dir, filename) for filename in filenames]

    for pic in files:
        if not os.path.isfile(pic):
            log.warning(f"File not found: {pic}")
            continue

        imgsize = get_pic_size(pic)
        basename = os.path.basename(pic)
        # Output picture with the same name
        output_picture = os.path.join(args.output, basename)
        # Output JSON with same name but different extension
        output_json = os.path.join(args.output, basename.split(".")[0] + ".json")

        t = time.time()
        log.info(f"Running inference on picture {pic}")
        results = model.predict([pic], imgsz=imgsize, iou=0.5, conf=0.5, stream=True)
        detections = yolov8_result_to_list(results, save_image=output_picture)
        log.info(f"Inference took {time.time() - t:.03f} secs")

        with open(output_json, "w") as f:
            f.write(json.dumps(detections, indent=2))

    log.info(f"All tasks done!")
