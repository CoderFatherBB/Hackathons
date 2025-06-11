import cv2
import numpy as np

# Load the pre-trained YOLO model for object detection
weight_path = "yolov3.cfg"
cfg_path = "yolov3.weights"

# Load the YOLO model
net = cv2.dnn.readNet(weight_path, cfg_path)

# Load the COCO dataset labels
with open("coco.names", "r") as f:
    classes = f.read().strip().split("\n")

# Load the video capture (you can replace 0 with a video file path)
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Get the height and width of the frame
    height, width = frame.shape[:2]

    # Create a blob from the frame and set it as input to the YOLO network
    blob = cv2.dnn.blobFromImage(frame, 1 / 255.0, (416, 416), swapRB=True, crop=False)
    net.setInput(blob)

    # Get the output layer names
    layer_names = net.getUnconnectedOutLayersNames()

    # Forward pass through the network
    detections = net.forward(layer_names)
    
    # Initialize the count of detected objects
    object_count = 0
    
    # Loop over the detections
    for detection in detections:
        for obj in detection:
            scores = obj[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]

            if confidence > 0.10:
                # Extract the bounding box coordinates
                box = obj[0:4] * np.array([width, height, width, height])
                (center_x, center_y, box_width, box_height) = box.astype("int")

                # Calculate the top-left corner coordinates
                x = int(center_x - (box_width / 2))
                y = int(center_y - (box_height / 2))

                # Draw a bounding box and label on the framecome then
                cv2.rectangle(frame, (x, y), (x + int(box_width), y + int(box_height)), (0, 255, 0), 2)
                text = f"{classes[class_id]}: {confidence:.2f}"
                cv2.putText(frame, text, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                # Increment the count of detected objects
                object_count += 1

                break;

    # Display the resulting frame
    cv2.putText(frame, f"Objects detected: {object_count}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    cv2.imshow("Frame", frame)
   
    # Break the loop if the 'q' key is pressed
    if cv2.waitKey(30) & 0xFF == ord("q"):
        break


# Release video capture and close all windows
cap.release()
cv2.destroyAllWindows()