import os
import cv2
from PIL import Image, ImageTk
from ultralytics import YOLO
import shutil

class DOTDetect:
    def __init__(self, resized_video_width, resized_video_height) -> None:
        self.resized_video_height = resized_video_height
        self.resized_video_width = resized_video_width

        models_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "Models")
        self.model = YOLO(os.path.join(models_path, "BBoxGeral11.pt"))
        self.threshold = 0.3
    
    def show_dot(self, ret, frame, resize_x=0, resize_y=0):
        if not ret:
            return None, None, None
        
        original_frame = frame.copy()
        results = self.model(frame)[0]
        all_bboxes = []

        for result in results.boxes.data.tolist():
            x1, y1, x2, y2, score, class_id = result
            if score > self.threshold:
                all_bboxes.append([int(x1), int(y1), int(x2), int(y2), score, class_id])
                cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 4)
                cv2.putText(frame, results.names[int(class_id)].upper(), (int(x1), int(y1 - 10)),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.3, (0, 255, 0), 3, cv2.LINE_AA)

        #if (len(all_bboxes) > 0):
        # Convert the image from OpenCV BGR format to PIL RGB format
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # Resize
        if resize_x != 0 or resize_y != 0:
            frame = cv2.resize(frame, (resize_x, resize_y))
        else:
            frame = cv2.resize(frame, (self.resized_video_width, self.resized_video_height))
        # Convert the image to PIL format   
        image = Image.fromarray(frame)
        # Convert the image to ImageTk format
        image = ImageTk.PhotoImage(image)
        # Update the image display
        #else:
        #    image = None
        
        return image, all_bboxes, original_frame
    
    def find_dot(self, jpg_files, pictures_path, valid_out_path, invalid_out_path):
        # if not jpg_files:
        #     print("No JPG image found in the folder.")
        #     return [], None
        
        image_path = os.path.join(pictures_path, jpg_files[0])
        
        #try:
        image = cv2.imread(image_path)
        #    break
        #except (FileNotFoundError):
        #    continue

        results = self.model(image)[0]

        all_bboxes = []

        found_dot = False
        for result in results.boxes.data.tolist():
            x1, y1, x2, y2, score, class_id = result
            if score > self.threshold:
                found_dot = True
                all_bboxes.append([int(x1), int(y1), int(x2), int(y2), score, class_id])

        os.remove(image_path)
        #shutil.move(image_path, (valid_out_path if found_dot else invalid_out_path))

        return all_bboxes, image