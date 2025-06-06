import os
import numpy as np
import cv2
from PIL import Image, ImageTk
import torch
from ultralytics import YOLO
import imutils 
from scipy.stats import entropy
from pathlib import Path
import shutil

class DOTDatasetProcessor:
    def __init__(self, models_path=None) -> None:
        if models_path is None:
           models_path = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "Models")

        
        self.model = YOLO(os.path.join(models_path, "find_tyre_center.pt"))
        self.threshold = 0.8
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
        
        if not bbox:
            height, width, _ = image.shape
            center_x = width // 2
            center_y = height // 2
            return center_x, center_y
        else:
            box_maior = self.get_box(bbox)
            x, y, _, _ = box_maior.cpu().numpy().astype(int)
            return x, y
    
    def calculate_angle(self, points):
        p_line1, p_common, p_line2 = points
        vector1 = np.array(p_line1) - np.array(p_common)
        vector2 = np.array(p_line2) - np.array(p_common)
        
        dot_product = np.dot(vector1, vector2)
        magnitude1 = np.linalg.norm(vector1)
        magnitude2 = np.linalg.norm(vector2)
        cos_angle = dot_product / (magnitude1 * magnitude2)
        
        angle_radians = np.arccos(np.clip(cos_angle, -1.0, 1.0))
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
    
    def yolo_to_bbox(self, yolo_coords, img_width, img_height):
        """Convert YOLO format coordinates to bounding box coordinates"""
        x_center, y_center, width, height = yolo_coords
        
        # Convert relative coordinates to absolute coordinates
        x_center *= img_width
        y_center *= img_height
        width *= img_width
        height *= img_height
        
        # Calculate bounding box coordinates
        x1 = int(x_center - width / 2)
        y1 = int(y_center - height / 2)
        x2 = int(x_center + width / 2)
        y2 = int(y_center + height / 2)
        
        return x1, y1, x2, y2
    
    def parse_yolo_label(self, label_path):
        """Parse YOLO format label file"""
        bounding_boxes = []
        
        if not os.path.exists(label_path):
            return bounding_boxes
        
        with open(label_path, 'r') as f:
            lines = f.readlines()
        
        for line in lines:
            parts = line.strip().split()
            if len(parts) >= 5:
                class_id = int(parts[0])
                x_center = float(parts[1])
                y_center = float(parts[2])
                width = float(parts[3])
                height = float(parts[4])
                
                bounding_boxes.append([class_id, x_center, y_center, width, height])
        
        return bounding_boxes
    
    def cropDot(self, image, bounding_box, img_width, img_height):
        """Crop and rotate a single dot from the image"""
        # Find Tire Center
        xcentro, ycentro = self.find_center(image)
        
        # Convert YOLO format to bounding box
        class_id, x_center, y_center, width, height = bounding_box
        x1, y1, x2, y2 = self.yolo_to_bbox([x_center, y_center, width, height], img_width, img_height)
        
        # Add padding
        padding_size = 10
        padded_top_left = (max(0, x1 - padding_size), max(0, y1 - padding_size))
        padded_bottom_right = (min(image.shape[1], x2 + padding_size), min(image.shape[0], y2 + padding_size))
        
        # Crop the dot
        dot_img = image[padded_top_left[1]:padded_bottom_right[1], padded_top_left[0]:padded_bottom_right[0]]
        
        # Calculate dot center in original image coordinates
        xdot = x_center * img_width
        ydot = y_center * img_height
        dotCenter = (xdot, ydot)
        tire_center = (xcentro, ycentro)
        top_center = (xcentro, 0.0)
        
        # Rotate the dot
        rotated_image = self.rotate_dot(dot_img, dotCenter, tire_center, top_center)
        
        return rotated_image, class_id
    
    def process_dataset(self, dataset_path, output_path, target_classes=None):
        """
        Process the entire YOLO dataset
        
        Args:
            dataset_path: Path to the dataset root (containing train folder)
            output_path: Path where cropped images will be saved
            target_classes: List of class IDs to process (None for all classes)
        """
        dataset_path = Path(dataset_path)
        output_path = Path(output_path)
        
        # Create output directory
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Define paths
        train_images_path = dataset_path / "train" / "images"
        train_labels_path = dataset_path / "train" / "labels"
        
        if not train_images_path.exists() or not train_labels_path.exists():
            raise ValueError(f"Train images or labels folder not found in {dataset_path}")
        
        # Get all image files
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif']
        image_files = []
        for ext in image_extensions:
            image_files.extend(train_images_path.glob(f"*{ext}"))
            image_files.extend(train_images_path.glob(f"*{ext.upper()}"))
        
        processed_count = 0
        total_crops = 0
        image_counter = 1  # Sequential counter for naming
        
        print(f"Found {len(image_files)} images to process...")
        
        for img_path in image_files:
            try:
                # Load image
                image = cv2.imread(str(img_path))
                if image is None:
                    print(f"Warning: Could not load image {img_path}")
                    continue
                
                img_height, img_width = image.shape[:2]
                
                # Find corresponding label file
                label_path = train_labels_path / f"{img_path.stem}.txt"
                
                # Parse labels
                bounding_boxes = self.parse_yolo_label(label_path)
                
                if not bounding_boxes:
                    print(f"No labels found for {img_path.name}")
                    continue
                
                # Process each bounding box
                for i, bbox in enumerate(bounding_boxes):
                    class_id = bbox[0]
                    
                    # Skip if target_classes is specified and this class is not in it
                    if target_classes is not None and class_id not in target_classes:
                        continue
                    
                    try:
                        # Crop and rotate the dot
                        rotated_image, _ = self.cropDot(image, bbox, img_width, img_height)
                        
                        # Save the cropped image with sequential naming
                        output_filename = f"img_{image_counter}.png"
                        output_file_path = output_path / output_filename
                        rotated_image.save(str(output_file_path))
                        
                        total_crops += 1
                        image_counter += 1  # Increment counter for next image
                        print(f"Saved: {output_filename}")
                        
                    except Exception as e:
                        print(f"Error processing bbox {i} in {img_path.name}: {str(e)}")
                        continue
                
                processed_count += 1
                if processed_count % 10 == 0:
                    print(f"Processed {processed_count}/{len(image_files)} images...")
                    
            except Exception as e:
                print(f"Error processing {img_path.name}: {str(e)}")
                continue
        
        print(f"Processing complete!")
        print(f"Processed {processed_count} images")
        print(f"Generated {total_crops} cropped images")
        print(f"Output saved to: {output_path}")

# Example usage
if __name__ == "__main__":
    import argparse
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Process YOLO dataset and crop images')
    parser.add_argument('dataset_path', type=str, help='Path to the dataset root directory')
    parser.add_argument('--output_path', '-o', type=str, default=None, 
                       help='Output directory for cropped images (default: dataset_path/cropped_images)')
    parser.add_argument('--target_classes', '-c', type=int, nargs='+', default=None,
                       help='List of class IDs to process (e.g., -c 0 1 2). If not specified, all classes will be processed')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Set output path
    if args.output_path is None:
        # Default output path: create 'cropped_images' folder in the same directory as dataset
        dataset_parent = Path(args.dataset_path).parent
        output_path = dataset_parent / "cropped_images"
    else:
        output_path = args.output_path
    
    print(f"Dataset path: {args.dataset_path}")
    print(f"Output path: {output_path}")
    if args.target_classes:
        print(f"Target classes: {args.target_classes}")
    else:
        print("Processing all classes")
    
    # Initialize the processor
    processor = DOTDatasetProcessor()
    
    # Process the dataset
    processor.process_dataset(args.dataset_path, output_path, args.target_classes)