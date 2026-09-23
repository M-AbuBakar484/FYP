


from ultralytics import YOLO
import cv2
import math


# defining function for performing detection on live & uploaded video
def video_detection(path_x):
    # initializing video_capture variable with the video path
    video_capture = path_x

    # Create a Webcam Object to run Yolov8 on webcam
    cap = cv2.VideoCapture(video_capture)

    # uploading our model here
    model = YOLO("../YOLO-Weights/FCDS-Model.pt")

    # defining our data classes here with the sequence
    classNames = ["Afridi", "Baris Arduc", "Bilal", "Faisal", "Imran Khan", "Lee Jian", "Nawaz Sharif", "Ronaldo",
                  "Tom Cruise", "Virat Kohli", "iqra Aziz"]

    # Doing detections using YOLOv8 frame by frame in this loop
    while True:
        success, img = cap.read()

        # stream = True will use the generator, and it is more efficient than normal
        results = model(img, stream=True)

        # Once we have the results, we will loop through them,
        # and we will get the bounding boxes for each of the results,
        # we can check for individual bounding boxes and see how well it performs.
        for r in results:
            boxes = r.boxes
            for box in boxes:
                # here x1y1 (top-left) and x2y2 (bottom-right) coordinates of the bounding boxes
                x1, y1, x2, y2 = box.xyxy[0]

                # here the output of coordinate values is in the form of Tensors,
                # which we can check by uncommenting below print command.
                # print(x1, y1, x2, y2)
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

                # here we are converting output coordinate values from Tensors to integers
                # to create boundary boxes around the object.
                print(x1, y1, x2, y2)

                # now here creating rectangle/bounding-box around each detected object
                cv2.rectangle(img, (x1, y1), (x2, y2), (255, 0, 255), 2)
                # Syntax: cv2.rectangle(image, start_point, end_point, color, thickness)

                # here using box.conf to get the confidence-values which are currently in Tensors,
                # which we can check by uncommenting below print command.
                # print(box.conf[0])

                # here changing confidence-values from Tensors to Integers using math.ceil
                conf = math.ceil((box.conf[0] * 100)) / 100

                # here using int(box.cls[0]) we are getting the class id
                cls = int(box.cls[0])

                # here getting the class name
                class_name = classNames[cls]

                # here setting the label using class-name and confidence values
                label = f'{class_name}{conf}'

                # here, using cv2.getTextSize function, we're finding the size of the label,
                # to create field-rectangle around a detected object as per size of the label.
                t_size = cv2.getTextSize(label, 0, fontScale=1, thickness=2)[0]
                print(t_size)

                # now here creating rectangle above bonding-box
                c2 = x1 + t_size[0], y1 - t_size[1] - 3

                # here setting rectangle color for each class
                if class_name == "Afridi":
                    color = (255, 91, 91)
                elif class_name == "Baris Arduc":
                    color = (0, 119, 190)
                elif class_name == "Bilal":
                    color = (128, 255, 128)
                elif class_name == "Faisal":
                    color = (255, 244, 79)
                elif class_name == "Imran Khan":
                    color = (179, 153, 255)
                elif class_name == "Lee Jian":
                    color = (255, 192, 203)
                elif class_name == "Nawaz Sharif":
                    color = (0, 0, 0)
                elif class_name == "Ronaldo":
                    color = (218, 112, 214)
                elif class_name == "Tom Cruise":
                    color = (0, 206, 209)
                elif class_name == "Virat Kohli":
                    color = (255, 223, 186)
                else:
                    color = (153, 102, 204)

                # here, defining the confidence-value in condition,
                # means that, rectangle will only show if model detects an object above the mentioned confidence.
                if conf > 0.50:
                    # here displaying the rectangle around the detected object
                    cv2.rectangle(img, (x1, y1), (x2, y2), color, 3)
                    cv2.rectangle(img, (x1, y1), c2, color, -1, cv2.LINE_AA)  # filled

                    # here putting the text (class-name, confidence-value) around it
                    cv2.putText(img, label, (x1, y1 - 2), 0, 1, [255, 255, 255], thickness=1, lineType=cv2.LINE_AA)

        # here img variable contains the bounding boxes around the detected object with labels and the confidence score,
        # and Yield keyword displaying individual frames/images of the video.
        yield img


cv2.destroyAllWindows()




