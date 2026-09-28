# Thai-Synth-Receipts

**Thai-Synth-Receipts** is a large-scale, highly robust synthetic dataset of Thai commercial documents designed specifically for training and evaluating state-of-the-art Document AI and Optical Character Recognition (OCR) models. The dataset consists of 14,976 high-resolution document images (Receipts, Tax Invoices, Thermal Slips, and Quotations) across three distinct degradation variants, representing challenging environmental and hardware-induced noise found in real-world document processing.

## Dataset Overview

- **Language:** Thai (with standard English headers)
- **Domain:** Commercial documents (Supermarket, Cafe, IT Equipment, Construction)
- **Samples:** 14,976 images (from 4,992 unique documents)
- **Task:** Optical Character Recognition (OCR), Key Information Extraction (KIE), Document Layout Analysis
- **License:** MIT
- **Source:** Procedurally generated via synthetic data engine

## Dataset Structure

The dataset is strictly partitioned to prevent data leakage and ensure true zero-shot evaluation capabilities.

### Splits

- `train/`: 11,964 images (80%)
- `validation/`: 1,482 images (10%)
- `test/`: 1,530 images (10%)

### Data Fields

Each folder contains a `metadata.jsonl` file. Each line in the JSONL represents one document and contains:

- **file_name** (`string`): Relative path to the image file (e.g., `clean/images/TH-INV-0001.jpg`)
- **sample_id** (`string`): Unique identifier for the document
- **doc_type** (`string`): Type of document (e.g., `tax_invoice`, `receipt`, `thermal_slip`)
- **merchant_name** (`string`): Ground truth store/company name
- **items** (`list`): Array of purchased items including name, quantity, and price
- **total** (`float`): Total transaction amount
- **ocr_boxes** (`list`): Precise polygon coordinates `[[x1,y1], [x2,y1], [x2,y2], [x1,y2]]` and text transcriptions for every word on the page

### Data Statistics

- **Total Unique Documents:** 4,992
- **Variants per Document:** 3 (`clean`, `error`, `photo`)
- **Total Images:** 14,976
- **Layout Templates:** 6 distinct templates (ranging from structured formal grids to unstructured handwritten lists)

## Dataset Characteristics

### Robustness Evaluation Design

Thai-Synth-Receipts is specifically designed to measure and improve Document AI performance in **"in-the-wild" conditions** that challenge both optical recognition and layout understanding. Every document is generated in three parallel variants:

1. **Clean:** Perfect digital baseline with no artifacts.
2. **Error (Printer Degradation):** Simulates hardware defects including faded ink, vertical streaks, folded paper, ghosting, and ink blobs.
3. **Photo (Camera Degradation):** Simulates smartphone captures with motion blur, uneven lighting, non-linear gamma curves, and perspective warping.

### Zero-Shot Generalization Strategy

Unlike standard random-split datasets, the validation and test sets were curated using an **Unseen Dictionary Strategy**:
- **100% Disjoint Entities:** All merchant names, customer names, addresses, and product items in the `validation` and `test` splits are entirely absent from the `train` split.
- **True OCR Evaluation:** This forces the model to actually *read* the Thai text rather than memorizing common vocabulary or exploiting language model hallucinations.

### Key Evaluation Aspects

This dataset evaluates Document AI models on:
1. **Visual Robustness:** Performance on noisy, degraded, and warped document images.
2. **Layout Diversity:** Ability to parse information across 6 radically different structures (formal grids vs. minimalist POS vs. handwritten formats).
3. **Zero-shot Entity Extraction:** Accurate transcription of unseen proper nouns and technical terms (e.g., construction materials, IT jargon).

## Usage (Kaggle Notebooks)

### Loading the Dataset with Pandas

```python
import pandas as pd
import json
from PIL import Image
import matplotlib.pyplot as plt

# Define path (adjust based on your Kaggle input directory)
base_path = '/kaggle/input/thai-synth-receipts'

# Load training metadata
df_train = pd.read_json(f'{base_path}/train/metadata.jsonl', lines=True)

# Peek at the first document
sample = df_train.iloc[0]
print(f"Merchant: {sample['merchant_name']} | Total: {sample['total']}")

# Load and display the corresponding image
img_path = f"{base_path}/train/{sample['file_name']}"
img = Image.open(img_path)
plt.imshow(img)
plt.axis('off')
plt.show()
```

## Dataset Creation

### Source and Generation

The dataset was generated using a custom procedural synthesis engine in Python. All text entities (names, addresses, tax IDs, phone numbers) were procedurally combined from a large, custom-built Thai vocabulary catalog. 

### Privacy and Safety

This dataset contains **zero Personally Identifiable Information (PII)**. All companies, individuals, and contact details are 100% fictional. It is completely safe for commercial and academic use without privacy compliance risks.

## Limitations

- **Synthetic Nature:** While visually robust, the dataset is synthetic and may lack certain microscopic textures or artifacts found exclusively in authentic scanned paper.
- **Font Diversity:** The generation relies on a curated subset of Thai fonts; it may not cover extremely rare or heavily stylized legacy fonts.
- **Table Complexity:** The dataset focuses on standard commercial transactions and does not include highly complex nested tables or multi-page documents.
