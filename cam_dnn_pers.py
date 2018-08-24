# dnn related stuff (detection, recognition)

import cv2
import numpy as np
from cam_boxes import ObjBox
from cam_detect_cfg import cfg


class PersDetector:
    # class labels MobileNet SSD was trained to detect
    CLASSES = ["background", "aeroplane", "bicycle", "bird", "boat",
               "bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
               "dog", "horse", "motorbike", "person", "pottedplant", "sheep",
               "sofa", "train", "tvmonitor"]

    def __init__(self):
        self.net = cv2.dnn.readNetFromCaffe(cfg['pers_det_prototxt'], cfg['pers_det_model'])
        print(f"Loaded person detection model files: {cfg['pers_det_prototxt']} and {cfg['pers_det_model']}.")

    def detect(self, frame):

        (h, w) = frame.shape[:2]
        blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 0.007843, (300, 300), 127.5)

        # pass the blob through the network and obtain the detections and predictions
        self.net.setInput(blob)
        detections = self.net.forward()

        obj_boxes = []
        # loop over the detections
        for i in np.arange(0, detections.shape[2]):
            # extract the confidence (i.e., probability) associated with the prediction
            confidence = detections[0, 0, i, 2]

            # filter out weak detections by ensuring the `confidence` is greater than the minimum confidence
            if confidence < cfg['pers_det_confidence']:
                continue

            # extract the index of the class label from the `detections`,
            # then compute the (x, y)-coordinates of the bounding box for the object
            idx = int(detections[0, 0, i, 1])
            label = PersDetector.CLASSES[idx]
            if label != 'person':
                continue

            box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
            (startX, startY, endX, endY) = box.astype("int")

            obj_box = ObjBox(startX, startY, endX, endY, confidence, idx, label)
            obj_boxes.append(obj_box)

        return obj_boxes


