import os
import numpy as np
import cv2
from PIL import Image, ImageTk
from ultralytics import YOLO

class DOTOCRDetect:
    def __init__(self) -> None:
        models_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "Models")
        self.model = YOLO(os.path.join(models_path, "BBox4.pt"))
        self.threshold = 0.5
    
    def show_dot(self, frame, index_folder):
        frame = np.array(frame)
        original_frame = frame.copy()
        results = self.model(frame)[0]
        all_bboxes = {}

        for result in results.boxes.data.tolist():
            x1, y1, x2, y2, score, class_id = result
            if score > self.threshold:
                #all_bboxes.append([int(x1), int(y1), int(x2), int(y2), score, class_id])
                padding_size = 5
                padded_top_left = (max(0, int(x1) - padding_size), max(0, int(y1) - padding_size))
                padded_bottom_right = (min(original_frame.shape[1], int(x2) + padding_size), min(original_frame.shape[1], int(y2) + padding_size))
                unique_bbox = original_frame[padded_top_left[1]:padded_bottom_right[1], padded_top_left[0]:padded_bottom_right[0]]
                all_bboxes[results.names[int(class_id)].upper()] = unique_bbox
                #cv2.imwrite(f"./Results/{index_folder}/{results.names[int(class_id)].upper()}.png", unique_bbox)
                
                #image_j = Image.fromarray(unique_bbox.astype('uint8'))
                #image_j.save(f"./Results/{index_folder}/{results.names[int(class_id)].upper()}.png")
                
                #cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 1)
                #cv2.putText(frame, results.names[int(class_id)].upper(), (int(x1), int(y1 - 10)),
                #            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1, cv2.LINE_AA)

        # Convert the image from OpenCV BGR format to PIL RGB format
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # Resize
        #frame = cv2.resize(frame, (self.resized_video_width, self.resized_video_height))
        # Convert the image to PIL format
        image = Image.fromarray(frame)
        # Convert the image to ImageTk format
        #image = ImageTk.PhotoImage(image)
        # Update the image display

        return image, all_bboxes, original_frame