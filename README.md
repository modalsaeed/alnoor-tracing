# 🩺 Alnoor Medical Services - Database Tracking App

A desktop application for managing purchase orders, inventory, distribution, and patient coupons for Alnoor Medical Services.

## 📋 Features

- **Purchase Order Management**: Track orders from Ministry of Health
- **Stock Management**: Real-time inventory tracking and automated stock calculations
- **Product Database**: Comprehensive product catalog with references
- **Distribution Tracking**: Manage distribution locations and medical centres
- **Patient Coupon System**: Register, verify, and track patient coupons
- **Reporting**: Generate stock reports, coupon reports, and delivery notes
- **Import/Export**: CSV import/export functionality
- **Future-Ready**: Architecture designed for easy migration to web-based system

## 🛠️ Technology Stack

- **Python 3.11+**
- **PyQt6** - Modern GUI framework
- **SQLAlchemy 2.0** - Database ORM (web-ready)
- **SQLite** - Lightweight local database
- **pandas** - Data processing and CSV handling

## 📦 Installation

### Prerequisites

- Python 3.11 or higher
- pip (Python package manager)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/modalsaeed/alnoor-tracing.git
cd alnoor-tracing
```

2. Create a virtual environment:
```bash
python -m venv venv
```

3. Activate the virtual environment:
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Run the application:
```bash
python src/main.py
```

## 📁 Project Structure

```
alnoor-tracing/
├── src/
│   ├── main.py                 # Application entry point
│   ├── database/               # Database models and manager
│   ├── ui/                     # User interface components
│   │   ├── widgets/           # Feature-specific widgets
│   │   └── dialogs/           # Dialog windows
│   ├── services/              # Business logic layer
│   └── utils/                 # Utility functions
├── data/                       # SQLite database storage
├── exports/                    # CSV export location
├── backups/                    # Automatic database backups
├── tests/                      # Unit and integration tests
└── requirements.txt           # Python dependencies
```

## 🚀 Usage

### Main Sections

1. **Dashboard**: Overview of stock levels and recent activity
2. **Purchase Orders**: Add and manage POs from Ministry
3. **Products**: Maintain product catalog
4. **Distribution Locations**: Manage distribution points
5. **Medical Centres**: Track medical centre information
6. **Coupons**: Register and verify patient coupons
7. **Reports**: Generate and export reports

### Key Workflows

#### Adding a Purchase Order
1. Navigate to Purchase Orders
2. Click "Add New PO"
3. Enter PO reference, select product, and enter quantity
4. Save - stock levels update automatically

#### Verifying a Coupon
1. Navigate to Coupons
2. Select unverified coupon
3. Click "Verify"
4. Enter verification reference
5. Stock automatically decreases

#### Generating Reports
1. Navigate to Reports
2. Select report type (Stock/Coupon/Delivery Note)
3. Apply filters (date range, location, etc.)
4. Click "Generate" or "Export to CSV"

## 🔄 Future Web Migration

The application is architected for seamless migration to a web-based system:

- **SQLAlchemy ORM**: Database-agnostic (easy switch to PostgreSQL/MySQL)
- **Service Layer**: Business logic separated from UI (ready for API wrapping)
- **Modular Design**: Components can be reused in web framework (FastAPI/Django)

## 🧪 Testing

Run tests with pytest:

```bash
pytest tests/
```

With coverage:

```bash
pytest --cov=src tests/
```

## 📄 License

Copyright © 2025 Alnoor Medical Services. All rights reserved.

## 👥 Contact

For support or questions, contact Alnoor Medical Services IT Department.

---

**Version**: 1.0.0  
**Last Updated**: November 7, 2025
