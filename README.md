# Product Normalization & Combination System

Hackathon submission for product normalization challenge.

## Setup Instructions

### 1. Install Python 3.8+
Download from: https://www.python.org/downloads/

### 2. Clone/Extract Project
```bash
cd product-normalization-hackathon
```

### 3. Create Virtual Environment
```bash
python -m venv venv

# Activate:
# Windows: venv\Scripts\activate
# Mac/Linux: source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Add Data Files
Place `products_table.csv` in the `data/` folder

### 6. Run Data Verification
```bash
python verify_data.py
```

### 7. Run Main Script
```bash
python src/main.py
```

## Project Structure
```
product-normalization-hackathon/
├── data/              # Input CSV files
├── src/               # Source code
├── output/            # Generated results
├── tests/             # Unit tests
└── docs/              # Documentation
```

