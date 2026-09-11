# AI Subsystem — Leaf Disease Detection

**Responsible Teammates**: Diya (AI/ML Crop Health) & Aryan (AI/ML + Frontend)  
**Target Model Architecture**: YOLO11n (Nano Object Detection / Classification)

---

## 1. Objectives

Train a lightweight computer vision model capable of identifying common agricultural crop leaf diseases from field images.

The nano variant (`yolo11n`) is selected specifically because:
* High mAP accuracy while requiring minimal parameter count (~2.6M params).
* Feasible training time on standard GPU/Colab resources.
* Low memory footprint and fast inference on edge hardware (Raspberry Pi CPU).

---

## 2. Recommended Datasets for SIH 26180

1. **PlantVillage Dataset**:
   * Open dataset with 54,000+ images covering 38 disease and healthy crop categories (Tomato, Potato, Pepper, Corn, Apple, etc.).
2. **Indian Crop Leaf Datasets** (Mendeley / Kaggle / AICTE Data):
   * Focus on rice blast, wheat rust, cotton boll rot, and tomato early/late blight.

---

## 3. Dataset Directory Layout (Standard YOLO Format)

When Diya prepares the dataset, organize the files as follows:

```text
ai/disease_detection/dataset/
├── data.yaml                 # Class names and dataset paths
├── train/
│   ├── images/               # Training images (.jpg / .png)
│   └── labels/               # YOLO format bounding box txt files
├── val/
│   ├── images/               # Validation images
│   └── labels/
└── test/
    ├── images/
    └── labels/
```

Example `data.yaml`:
```yaml
path: ./dataset
train: train/images
val: val/images
test: test/images

names:
  0: healthy
  1: early_blight
  2: late_blight
  3: bacterial_spot
  4: leaf_mold
```

---

## 4. Training Workflow (Ultralytics YOLO11n)

```bash
# Install training dependencies
pip install ultralytics torch torchvision

# Train YOLO11n model
yolo detect train \
  data=dataset/data.yaml \
  model=yolo11n.pt \
  epochs=50 \
  imgsz=640 \
  batch=16 \
  project=runs/train \
  name=crop_disease_v1
```

---

## 5. Hand-off to Aryan for Edge Deployment

Once training achieves satisfactory validation metrics ($\text{mAP50} > 0.85$):
1. Locate the best weights file at `runs/train/crop_disease_v1/weights/best.pt`.
2. Hand over `best.pt` to Aryan for ONNX conversion in `ai/inference/`.
