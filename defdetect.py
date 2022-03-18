import cv2
import numpy as np
import time
import glob
import random
from pymodbus.client.sync import ModbusSerialClient

net = cv2.dnn.readNetFromDarknet("yolov3_training.cfg",r"yolov3_training_last.weights")
classes = ['pass','er01','er02']

client = ModbusSerialClient(method = 'rtu', port='COM2', baudrate= 9600, stopbits = 1, bytesize = 8, parity = 'N', timeout = 1)
client.connect()

images_path = glob.glob(r"images\ 123.jpg")
layer_names = net.getLayerNames()
output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]
colors = np.random.uniform(0, 255, size=(len(classes), 3))
random.shuffle(images_path)

def connectbus():
    while True:
        read_data = client.read_holding_registers(address=0, count=1, unit=2)
        bus_in = read_data.registers[0]
        return bus_in

def detection():
    for img_path in images_path:

        img = cv2.imread(img_path)
        img = cv2.resize(img, None, fx=1.4, fy=1.4)
        height, width, channels = img.shape

        blob = cv2.dnn.blobFromImage(img, 0.00392, (416, 416), (0, 0, 0), True, crop=False)

        net.setInput(blob)
        outs = net.forward(output_layers)

        class_ids = []
        confidences = []
        boxes = []
        for out in outs:
            for detection in out:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                if confidence > 0.3:
                    # Object detected
                    print(class_id)
                    center_x = int(detection[0] * width)
                    center_y = int(detection[1] * height)
                    w = int(detection[2] * width)
                    h = int(detection[3] * height)

                    # Rectangle coordinates
                    x = int(center_x - w / 2)
                    y = int(center_y - h / 2)

                    boxes.append([x, y, w, h])
                    confidences.append(float(confidence))
                    class_ids.append(class_id)

        indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)
        print(indexes)
        font = cv2.FONT_HERSHEY_PLAIN
        for i in range(len(boxes)):
            if i in indexes:
                x, y, w, h = boxes[i]
                label = str(classes[class_ids[i]])
                if label == "pass":
                    client.write_register(address=1, value=random.randint(0, 100), unit=2)
                else:
                    client.write_register(address=2, value=random.randint(0, 100), unit=2)
                color = colors[class_ids[i]]
                cv2.rectangle(img, (x, y), (x + w, y + h), color, 2)
                cv2.putText(img, label, (x, y - 5), font, 1, color, 2)
                
                # return label

        cv2.imshow("Image", img)
        key = cv2.waitKey(1)

cv2.destroyAllWindows()