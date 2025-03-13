import os
import numpy as np
import cv2
from PIL import Image, ImageTk
import torch
from ultralytics import YOLO
import imutils 
from scipy.stats import entropy

# Class for CROP and ROTATE the DOT

class DOTCrop:
    def __init__(self,) -> None:
        models_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "Models")
        results_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "Results")
        self.model = YOLO(os.path.join(models_path, "find_tyre_center.pt"))
        self.threshold = 0.8
        self.index = len(os.listdir(results_path))
        self.highest_score = 0.0
    
    def get_box(self, box):
        all_boxes = box.xywh
        img_size = np.array(box.orig_shape) / 2
        distances = np.linalg.norm(all_boxes[:, :2].cpu() - img_size, axis=1)
        closest_index = np.argmin(distances)
        return all_boxes[closest_index]

    def find_center(self, image):
        results = self.model(image)[0]
        bbox = results.boxes

        #print(bbox)
        if not bbox:
            height, width, _ = image.shape
            center_x = width // 2
            center_y = height // 2
            return center_x, center_y
        else:
            box_maior = self.get_box(bbox)

            x, y, _, _ = box_maior.cpu().numpy().astype(int)
            #_, _, w1, h1 = box_menor.cpu().numpy().astype(int)

            return x, y

    def calculate_angle(self, points):
        p_line1, p_common, p_line2 = points

        vector1 = np.array(p_line1) - np.array(p_common)
        vector2 = np.array(p_line2) - np.array(p_common)
        
        dot_product = np.dot(vector1, vector2)
        magnitude1 = np.linalg.norm(vector1)
        magnitude2 = np.linalg.norm(vector2)
        cos_angle = dot_product / (magnitude1 * magnitude2)
        
        angle_radians = np.arccos(cos_angle)
        angle_degrees = np.degrees(angle_radians)
        
        # Determinando a orientação das retas
        cross_product = np.cross(vector1, vector2)
        
        if cross_product < 0:
            angle_degrees = -angle_degrees
        
        return angle_degrees
    
    def rotate_dot(self, dot_img, dotCenter, tire_center, top_center):
        final_angle = self.calculate_angle([top_center, tire_center, dotCenter])

        rotated_image = Image.fromarray(dot_img).rotate(final_angle, expand=True)

        return rotated_image

    def cropDot(self, image, bouding_boxes):
        # Find Tire Center
        xcentro, ycentro = self.find_center(image)

        # Crop dot
        x1, y1, x2, y2, score, class_id = bouding_boxes[0]
        
        padding_size = 0
        padded_top_left = (max(0, x1 - padding_size), max(0, y1 - padding_size))
        padded_bottom_right = (min(image.shape[1], x2 + padding_size), min(image.shape[1], y2 + padding_size))
        dot_img = image[padded_top_left[1]:padded_bottom_right[1], padded_top_left[0]:padded_bottom_right[0]]


        xdot = (x1 + x2) / 2
        ydot = (y1 + y2) / 2
        dotCenter = xdot, ydot
        tire_center = xcentro, ycentro
        top_center = xcentro, 0.0

        rotated_image = self.rotate_dot(dot_img, dotCenter, tire_center, top_center)
        
        #directory = f"./Results/{self.index}"
        #if not os.path.exists(directory):
        #    os.makedirs(directory)
        
        #rotated_image.save(f"./Results/{self.index}/img{self.index}.png")

        self.index+=1
        return rotated_image, self.index-1
