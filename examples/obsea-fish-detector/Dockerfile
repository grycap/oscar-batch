FROM ubuntu:22.04 as builder
WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends python3 python3-pip ffmpeg wget jq && \
    rm -rf /var/lib/apt/lists/*

COPY ./fish-detector.py ./requirements.txt ./yolov8x_obsea_19sp_2538img.pt /app/

RUN pip3 install -r requirements.txt && \
    rm -rf /root/.cache/pip

FROM ubuntu:22.04
WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends python3 ffmpeg jq && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /app /app
COPY --from=builder /usr/local/lib/python3.10/dist-packages /usr/local/lib/python3.10/dist-packages
COPY --from=builder /usr/local/bin /usr/local/bin

CMD ["python3", "fish-detector.py"]
