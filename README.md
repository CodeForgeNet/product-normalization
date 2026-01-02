# Product Normalization & Combination System

A robust, multi-stage product matching system that identifies and groups identical products across different e-commerce platforms, handling variations in naming, formatting, and packaging descriptions.

## 🎯 Overview

This system solves the challenge of product deduplication across multiple e-commerce platforms where the same product appears with different names, descriptions, and formats.

## 🏗️ Architecture

The system uses a **hybrid multi-stage approach** combining detailed text normalization with PostgreSQL for data persistence.

```
┌─────────────────────────────────────────────────────────────┐
│  Stage 1: Fingerprint Matching (Fast Path)                  │
│  • Normalized text-based exact matching                      │
│  • Handles 70-80% of cases in O(1) time                     │
└─────────────────────────────────────────────────────────────┘
                            ↓ (if no match)
┌─────────────────────────────────────────────────────────────┐
│  Stage 2: Fuzzy String Matching                             │
│  • Token-based similarity scoring                            │
│  • Handles spelling variations and extra words              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Database Update (PostgreSQL)                                │
│  • Create/link normalized product entries                    │
│  • Running in Docker container                               │
└─────────────────────────────────────────────────────────────┘
```

## 🛠️ Technology Stack

- **Python 3.13+**: Primary implementation language
- **PostgreSQL**: Database for data persistence (via Docker)
- **Pandas**: CSV processing and data manipulation
- **fuzzywuzzy/Levenshtein**: Fuzzy string matching
- **psycopg**: Database adapter

## 📦 Installation

### Prerequisites
- Python 3.13 or higher
- Docker & Docker Compose

### Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd product-normalization-hackathon
```

2. **Start PostgreSQL Database**
   The project uses a Dockerized PostgreSQL database.
```bash
docker-compose up -d
```
   *Note: Ensure no local PostgreSQL service is running on port 5432.*

3. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

4. **Install dependencies**
```bash
pip install -r requirements.txt
```

5. **Initialize Database**
   The database tables are automatically created on first startup using `init.sql`.

## 🚀 Usage

### 1. Place Input Data
Ensure `products_table.csv` is in the `data/` folder (or configured location).

### 2. Run the Main Script
```bash
python src/main.py
```

## � Project Structure

```
product-normalization-hackathon/
├── README.md               # Project documentation
├── docker-compose.yml      # Docker configuration for PostgreSQL
├── init.sql               # Database initialization script
├── requirements.txt       # Python dependencies
├── .gitignore             # Git ignore rules
│
├── config/
│   ├── __init__.py
│   └── database.py        # Database connection & operations
│
├── data/
│   └── products_table.csv # Input data
│
├── output/
│   ├── normalized_products.csv
│   └── products_updated.csv
│
├── src/
│   ├── main.py            # Entry point
│   ├── app_config.py      # Configuration settings (renamed from config.py)
│   ├── normalizer.py      # Text normalization functions
│   ├── matcher.py         # Matching logic
│   ├── fuzzy_matcher.py   # Fuzzy matching implementation
│   └── data_explorer.py   # Data analysis utilities
│
└── tests/
    └── test_normalizer.py # Unit tests
```

### 3. Check Outputs
Results are saved to the `output/` directory:

*   **`normalized_products.csv` (The Master Catalog)**:
    *   A clean, deduplicated list of unique products.
    *   Each row represents one unique product with a unique `product_id`.
    *   Acts as the "Gold Standard" reference database.

*   **`products_updated.csv` (The Mapped Input)**:
    *   The original raw input data enriched with `product_id`.
    *   Maps every messy input row to the correct normalized entry in the master catalog.

## ⚡ Performance
The system is optimized for high-throughput processing:
- **Persistent Database Connections**: Minimizes connection overhead.
- **Speed**: Processes **~1200+ products/second** (benchmarked on 16k dataset).
- **Batch Processing**: Efficiently handles large datasets.

## 🔧 Configuration

Edit `src/app_config.py` to customize matching thresholds and settings.

## 🐛 Troubleshooting

**Issue**: `FATAL: role "hackathon" does not exist`
- **Cause**: Application is connecting to a local PostgreSQL instance instead of Docker.
- **Solution**: Stop local PostgreSQL services (`brew services stop postgresql`) and restart Docker container (`docker-compose restart`).

**Issue**: `ModuleNotFoundError: No module named 'psycopg'`
- **Solution**: Ensure you are in the virtual environment and requirements are installed (`pip install -r requirements.txt`).

## 📝 License

This project is developed for the Product Normalization Hackathon.