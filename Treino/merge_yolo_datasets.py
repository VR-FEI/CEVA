import os
import shutil
import yaml
import uuid
from glob import glob
from pathlib import Path


def load_yaml(yaml_path):
    with open(yaml_path, 'r') as f:
        return yaml.safe_load(f)


def save_yaml(yaml_path, data):
    with open(yaml_path, 'w') as f:
        yaml.dump(data, f, sort_keys=False)


def remap_label_file(file_path, old_labels_map, new_labels_map):
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
            continue

        new_index = new_labels_map[old_class]
        new_lines.append(' '.join([str(new_index)] + parts[1:]))

    with open(file_path, 'w') as f:
        f.write('\n'.join(new_lines) + '\n')


def remap_dataset_labels(dataset_path, target_labels):
    yaml_path = dataset_path / 'data.yaml'
    data = load_yaml(yaml_path)
    old_names = data.get('names', [])
    old_labels_map = {i: name for i, name in enumerate(old_names)}
    new_labels_map = {name: i for i, name in enumerate(target_labels)}

    for subset in dataset_path.iterdir():
        labels_dir = subset / 'labels'
        if not labels_dir.is_dir():
            continue
        for label_file in glob(str(labels_dir / '*.txt')):
            remap_label_file(label_file, old_labels_map, new_labels_map)

    data['nc'] = len(target_labels)
    data['names'] = target_labels
    save_yaml(yaml_path, data)


def copy_dataset_contents(src_dataset, dst_dataset):
    for subset_name in ['Train', 'Test', 'Val']:
        src_subset = src_dataset / subset_name
        dst_subset = dst_dataset / subset_name

        for subfolder in ['images', 'labels']:
            src_dir = src_subset / subfolder
            dst_dir = dst_subset / subfolder

            if not src_dir.exists():
                continue
            dst_dir.mkdir(parents=True, exist_ok=True)

            for file_path in src_dir.glob('*'):
                dst_file = dst_dir / file_path.name

                if dst_file.exists():
                    # Generate a unique name to avoid conflict
                    unique_id = uuid.uuid4().hex[:8]
                    new_name = f"{file_path.stem}_{unique_id}{file_path.suffix}"
                    dst_file = dst_dir / new_name

                    # If this is a label file, rename corresponding image too
                    if subfolder == "labels":
                        corresponding_image = file_path.with_suffix('.jpg')
                        if not corresponding_image.exists():
                            corresponding_image = file_path.with_suffix('.png')

                        if corresponding_image.exists():
                            new_image_name = f"{corresponding_image.stem}_{unique_id}{corresponding_image.suffix}"
                            image_src = corresponding_image
                            image_dst_dir = dst_subset / 'images'
                            image_dst_dir.mkdir(parents=True, exist_ok=True)
                            image_dst = image_dst_dir / new_image_name
                            shutil.copy(image_src, image_dst)

                shutil.copy(file_path, dst_file)


def merge_datasets(principal_path, secondary_path):
    principal_path = Path(principal_path)
    secondary_path = Path(secondary_path)

    # Load label list from the principal dataset
    principal_yaml = load_yaml(principal_path / 'data.yaml')
    main_labels = principal_yaml['names']
    print(f"📘 Principal dataset has {len(main_labels)} classes.")

    # Check and remap second dataset if needed
    secondary_yaml = load_yaml(secondary_path / 'data.yaml')
    secondary_labels = secondary_yaml['names']

    if secondary_labels != main_labels:
        print("⚠️  Label sets differ. Remapping second dataset to match principal dataset...")
        remap_dataset_labels(secondary_path, main_labels)
    else:
        print("✅ Label sets match. No remapping needed.")

    # Merge data
    print("📦 Copying images and labels from secondary to principal...")
    copy_dataset_contents(secondary_path, principal_path)

    # Ensure principal dataset yaml is consistent
    principal_yaml['nc'] = len(main_labels)
    principal_yaml['names'] = main_labels
    save_yaml(principal_path / 'data.yaml', principal_yaml)

    print("✅ Merge completed successfully.")


# --- CLI Entry Point ---
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Merge two YOLO detection datasets into one unified structure.')
    parser.add_argument('principal_dataset', type=str, help='Path to the main YOLO dataset (destination)')
    parser.add_argument('secondary_dataset', type=str, help='Path to the second YOLO dataset to merge (source)')

    args = parser.parse_args()

    print(f"➡️  Merging into principal dataset: {args.principal_dataset}")
    print(f"➕ From secondary dataset: {args.secondary_dataset}\n")

    merge_datasets(args.principal_dataset, args.secondary_dataset)
