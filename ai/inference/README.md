# Edge AI Inference — ONNX Runtime Deployment

**Responsible Teammate**: Aryan (AI/ML + Frontend)  
**Deployment Target**: Raspberry Pi 4/5 (Field Edge Gateway) & Local Dev PC

---

## 1. Why ONNX for SIH 26180 Field Deployment?

Deploying deep learning models directly on agricultural edge gateways (like a Raspberry Pi in a farm) presents key constraints:
* PyTorch and CUDA dependencies are heavy, resource-intensive, and slow to initialize on edge ARM CPUs.
* The Open Neural Network Exchange (**ONNX**) format decouples model training from deployment.
* **ONNX Runtime** (`onnxruntime`) is lightweight, highly optimized for ARM/x86 CPU inference, and operates completely offline.

---

## 2. Model Export Procedure (PyTorch to ONNX)

Once Diya provides the trained `best.pt` file from `ai/disease_detection/`:

```bash
# Export trained YOLO11n weights to ONNX with 640x640 input resolution
yolo export model=runs/train/crop_disease_v1/weights/best.pt format=onnx imgsz=640 dynamic=False
```

This generates `best.onnx`, ready for deployment.

---

## 3. Edge Inference Workflow (Python + ONNX Runtime)

The edge inference pipeline consists of:
1. **Image Preprocessing**: Resize camera leaf image to $640 \times 640$, normalize pixel values to $[0.0, 1.0]$, convert from HWC to CHW format.
2. **Inference Execution**:
   ```python
   import onnxruntime as ort
   import numpy as np

   # Initialize lightweight ONNX session on CPU
   session = ort.InferenceSession("best.onnx", providers=["CPUExecutionProvider"])
   input_name = session.get_inputs()[0].name
   outputs = session.run(None, {input_name: preprocessed_image})
   ```
3. **Post-Processing (NMS)**: Filter detections with confidence score threshold ($> 0.50$) and extract predicted disease class and bounding box coordinates.
4. **Integration**: Wire into FastAPI backend endpoint `POST /api/v1/ai/predict` so the Next.js dashboard can upload a photo and receive instant disease diagnosis.
