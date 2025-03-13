import os
import cv2
from PIL import Image, ImageTk
from ultralytics import YOLO

class SKURead:
    def __init__(self) -> None:
        models_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "Models")
        self.model = YOLO(os.path.join(models_path, "sku_read4.pt"))
        self.threshold = 0.3
    
    def calculate_overlap_by_coords(self, rectCurr, rectOld):
        score1, char1, x1, y1, x2, y2 = rectCurr
        score2, char2, x3, y3, x4, y4 = rectOld
        
        # Calculate the width and height of each rectangle
        w1, h1 = x2 - x1, y2 - y1
        w2, h2 = x4 - x3, y4 - y3

        # Calculate the area of each rectangle
        area1 = w1 * h1
        area2 = w2 * h2

        # Calculate the intersection rectangle
        x_intersect = max(0, min(x2, x4) - max(x1, x3))
        y_intersect = max(0, min(y2, y4) - max(y1, y3))
        intersect_area = x_intersect * y_intersect

        # Calculate the percentage of overlap
        overlap_percentage = (intersect_area / min(area1, area2)) * 100
        if overlap_percentage >= 60.00:
            print(f"[SKU READ] Overlap detected! Percentage: {overlap_percentage:.2f}% (Current acc: '{char1}' -> {score1} | Old acc: '{char2}' -> {score2})")
            bestAccuracy = None
            if score1 > score2:
                return True, rectCurr
            return True, rectOld
        
        return False, None

    def find_sku(self, frame, index_folder):
        original_frame = frame.copy()
        all_bboxes = []
        sku_found = []

        results = self.model(frame)[0]

        sorted_boxes = results.boxes.data.tolist()
        sorted_boxes.sort()
        old_rectangle = None
        
        # Delete the last boxes if num_boxes > 4
        del sorted_boxes[4:]
        for result in sorted_boxes:
            x1, y1, x2, y2, score, class_id = result
            
            if score > self.threshold:
                
                padding_size = 0
                padded_top_left = (max(0, int(x1) - padding_size), max(0, int(y1) - padding_size))
                padded_bottom_right = (min(original_frame.shape[1], int(x2) + padding_size), min(original_frame.shape[1], int(y2) + padding_size))
                unique_bbox = original_frame[padded_top_left[1]:padded_bottom_right[1], padded_top_left[0]:padded_bottom_right[0]]
                
                result_char = results.names[int(class_id)].upper()
                
                #Check for overlaping bboxes (replace by largest score)
                overlaped, new_result = False, None
                if (old_rectangle != None):
                   overlaped, new_result = self.calculate_overlap_by_coords((score, result_char, x1, y1, x2, y2), old_rectangle)
                old_rectangle = ((score, result_char, x1, y1, x2, y2))
                #all_bboxes.append([int(x1), int(y1), int(x2), int(y2), score, class_id])              
                
                
                if not overlaped:
                    all_bboxes.append(unique_bbox)  
        
                    #directory = f"./Results/{index_folder}/char"
                    #if not os.path.exists(directory):
                    #    os.makedirs(directory)
                    
                    #image_j = Image.fromarray(unique_bbox.astype('uint8'))
                    #image_j.save(f"./Results/{index_folder}/char/{result_char}.png")                    
                    
                    sku_found.append(result_char)
                else:
                    sku_found[len(sku_found)-1] = new_result[1]
                #sku_score.append(score)
                
                #cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 1)
                # cv2.putText(frame, result_char, (int(x1), int(y1 + 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 0), 1)
        #print(len(sorted_boxes))
        return "".join(sku_found), all_bboxes, frame