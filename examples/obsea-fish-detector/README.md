# Fish Detector Example

In this example, we utilize the YOLO v8 object detection model to create a fish detector.

## Uploading the Model

To upload the model to Oscar using `oscar-cli`, use the following command:

```bash
oscar-cli apply fish-detector.yaml
```

## Using the Service

To use the service, run the following Python script:

```python
coordinator.py
```

By following these steps, you can perform inference on large collections of images effectively.