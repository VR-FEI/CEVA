import os
import yaml
from glob import glob
from pathlib import Path

# Full 31-class label list to remap to
NEW_LABELS = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
              'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'J', 'K',
              'L', 'M', 'O', 'P', 'R', 'T', 'U', 'V', 'W', 'X', 'Y']

def load_yaml(yaml_path):
    with open(yaml_path, 'r') as f:
        return yaml.safe_load(f)

def save_yaml(yaml_path, data):
    with open(yaml_path, 'w') as f:
        yaml.dump(data, f, sort_keys=False)

def remap_label_file(file_path, old_labels_map, new_labels_map, target_classes=None):
    with open(file_path, 'r') as f:
        lines = f.readlines()

    new_lines = []
    for line in lines:
        if not line.strip():
            continue
        parts = line.strip().split()
        old_index = int(parts[0])
        old_class = old_labels_map.get(old_index)

        if old_class is None or old_class not in new_labels_map:
            continue  # skip unknown class

        new_index = new_labels_map[old_class]

        if target_classes is not None and new_index not in target_classes:
            continue  # skip classes not in target list

        new_lines.append(' '.join([str(new_index)] + parts[1:]))

    with open(file_path, 'w') as f:
        f.write('\n'.join(new_lines) + '\n')

def process_dataset(dataset_path, target_classes=None):
    dataset_path = Path(dataset_path)
    yaml_path = dataset_path / 'data.yaml'

    # Load and parse data.yaml
    data = load_yaml(yaml_path)
    old_names = data.get('names', [])
    old_labels_map = {i: name for i, name in enumerate(old_names)}
    new_labels_map = {name: i for i, name in enumerate(NEW_LABELS)}

    print(f"Original label count: {len(old_names)}")
    print(f"New label count: {len(NEW_LABELS)}")

    # Traverse each subset folder (Train, Test, Val, etc.)
    for subset_dir in dataset_path.iterdir():
        labels_dir = subset_dir / 'labels'
        if not labels_dir.is_dir() or "train" in str(labels_dir):
            continue

        print(f"Processing label files in: {labels_dir}")
        for label_file in glob(str(labels_dir / '*.txt')):
            remap_label_file(label_file, old_labels_map, new_labels_map, target_classes)

    # Update and save new data.yaml
    data['nc'] = len(NEW_LABELS)
    data['names'] = NEW_LABELS
    save_yaml(yaml_path, data)
    print("✅ Dataset successfully remapped.")

# --- CLI Entry Point ---
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Remap YOLO label indices to a new label set.')
    parser.add_argument('dataset_path', type=str, help='Path to the YOLO dataset root directory')
    parser.add_argument('--output_path', '-o', type=str, default=None,
                        help='(Unused) Placeholder for future image cropping output directory')
    parser.add_argument('--target_classes', '-c', type=int, nargs='+', default=None,
                        help='List of new class IDs to retain (e.g., -c 0 1 2). Others will be removed.')

    args = parser.parse_args()

    # Output path placeholder (not used in this script)
    if args.output_path is None:
        output_path = Path(args.dataset_path).parent / "cropped_images"
    else:
        output_path = args.output_path

    print(f"Dataset path: {args.dataset_path}")
    print(f"Output path (unused): {output_path}")
    if args.target_classes:
        print(f"Target classes: {args.target_classes}")
    else:
        print("Processing all classes")

    process_dataset(args.dataset_path, args.target_classes)
