import os
import cv2
import glob
from pathlib import Path

class DOTDatasetProcessor:
    def __init__(self):
        self.img_counter = 1

    def load_yolo_labels(self, label_path):
        with open(label_path, 'r') as f:
            lines = f.readlines()
        boxes = []
        for line in lines:
            parts = line.strip().split()
            if len(parts) != 5:
                continue
            class_id, x_center, y_center, width, height = map(float, parts)
            boxes.append((int(class_id), x_center, y_center, width, height))
        return boxes

    def yolo_to_pixel_coords(self, box, img_width, img_height):
        _, x_center, y_center, width, height = box
        x1 = int((x_center - width / 2) * img_width)
        y1 = int((y_center - height / 2) * img_height)
        x2 = int((x_center + width / 2) * img_width)
        y2 = int((y_center + height / 2) * img_height)
        return max(0, x1), max(0, y1), min(img_width, x2), min(img_height, y2)

    def process_dataset(self, dataset_path, output_dir, target_classes=None):
        image_dir = os.path.join(dataset_path, "train", "images")
        label_dir = os.path.join(dataset_path, "train", "labels")
        os.makedirs(output_dir, exist_ok=True)

        for image_path in glob.glob(os.path.join(image_dir, "*.jpg")):
            filename = os.path.splitext(os.path.basename(image_path))[0]
            label_path = os.path.join(label_dir, filename + ".txt")

            if not os.path.exists(label_path):
                continue

            img = cv2.imread(image_path)
            if img is None:
                continue

            img_height, img_width = img.shape[:2]
            boxes = self.load_yolo_labels(label_path)

            for box in boxes:
                class_id = box[0]
                if target_classes is not None and class_id not in target_classes:
                    continue

                x1, y1, x2, y2 = self.yolo_to_pixel_coords(box, img_width, img_height)
                crop = img[y1:y2, x1:x2]
                if crop.size == 0:
                    continue

                crop_filename = os.path.join(output_dir, f"img_{self.img_counter}.jpg")
                cv2.imwrite(crop_filename, crop)
                self.img_counter += 1

        print(f"[INFO] Finished. Saved {self.img_counter - 1} cropped images to: {output_dir}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Process YOLO dataset and crop images')
    parser.add_argument('dataset_path', type=str, help='Path to the dataset root directory')
    parser.add_argument('--output_path', '-o', type=str, default=None, 
                        help='Output directory for cropped images (default: dataset_path/../cropped_images_info)')
    parser.add_argument('--target_classes', '-c', type=int, nargs='+', default=None,
                        help='List of class IDs to process (e.g., -c 0 1 2). If not specified, all classes will be processed')

    args = parser.parse_args()

    # Set output path
    if args.output_path is None:
        dataset_parent = Path(args.dataset_path).parent
        output_path = dataset_parent / "cropped_images_info"
    else:
        output_path = Path(args.output_path)

    print(f"Dataset path: {args.dataset_path}")
    print(f"Output path: {output_path}")
    if args.target_classes:
        print(f"Target classes: {args.target_classes}")
    else:
        print("Processing all classes")

    processor = DOTDatasetProcessor()
    processor.process_dataset(args.dataset_path, output_path, args.target_classes)
