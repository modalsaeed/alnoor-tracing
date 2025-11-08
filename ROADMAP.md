# 📍 Development Roadmap - Alnoor Medical Services

## ✅ Phase 0: Foundation (COMPLETED)

### What We Built
- [x] Complete directory structure
- [x] Database models with SQLAlchemy ORM
- [x] Database manager with CRUD operations
- [x] Main application window skeleton
- [x] Basic menu system
- [x] Status bar with live statistics
- [x] Backup/Restore functionality
- [x] Activity logging system
- [x] Configuration files (requirements.txt, .gitignore)
- [x] Documentation (README.md, QUICKSTART.md)

### Key Files Created
```
✅ src/database/models.py          - All database tables
✅ src/database/db_manager.py      - Database operations
✅ src/ui/main_window.py           - Main application window
✅ src/main.py                     - Entry point
✅ src/utils/constants.py          - App constants
✅ requirements.txt                - Dependencies
✅ README.md                       - Project documentation
✅ .gitignore                      - Git configuration
```

---

## 🔨 Phase 1: Basic CRUD Widgets (3-4 days)

### Priority 1: Products Widget
**File**: `src/ui/widgets/products_widget.py`

**Features**:
- Table view of all products
- Add/Edit/Delete products
- Search by name or reference
- Validation for unique references

**Why First?**: Products are referenced by Purchase Orders and Coupons

---

### Priority 2: Distribution Locations Widget
**File**: `src/ui/widgets/distribution_locations_widget.py`

**Features**:
- Table view of locations
- Add/Edit/Delete locations
- Contact information management
- Search and filter

**Why Second?**: Required before Coupons

---

### Priority 3: Medical Centres Widget
**File**: `src/ui/widgets/medical_centres_widget.py`

**Features**:
- Table view of medical centres
- Add/Edit/Delete centres
- Contact information management
- Search and filter

**Why Third?**: Required before Coupons

---

### Priority 4: Purchase Orders Widget
**File**: `src/ui/widgets/purchase_orders_widget.py`

**Features**:
- Table view with stock levels
- Add/Edit/Delete POs
- Product linking (dropdown)
- Automatic remaining stock calculation
- Filter by product or PO reference
- Stock level warnings (low stock)

**Why Fourth?**: Foundation for stock tracking

---

### Priority 5: Coupons Widget
**File**: `src/ui/widgets/coupons_widget.py`

**Features**:
- Table view with verification status
- Add new coupons
- Verify coupons (with verification reference)
- Filter by:
  - Verification status
  - Date range
  - Medical centre
  - Distribution location
- Patient CPR validation
- Auto-update stock on verification

**Why Fifth?**: Core business functionality

---

## 🎯 Phase 2: Business Logic Services (2-3 days)

### Stock Service
**File**: `src/services/stock_service.py`

**Responsibilities**:
- Calculate total stock across all POs
- Calculate remaining stock per product
- Update stock when coupon verified
- Stock level alerts
- Stock history tracking

---

### Coupon Service
**File**: `src/services/coupon_service.py`

**Responsibilities**:
- Coupon validation
- Verification logic
- Generate verification references
- Link to stock updates
- Duplicate detection

---

### Report Service
**File**: `src/services/report_service.py`

**Responsibilities**:
- Stock report generation
- Coupon report generation
- Delivery note creation
- Filter and query logic
- Date range handling

---

### CSV Handler
**File**: `src/utils/csv_handler.py`

**Responsibilities**:
- Import CSV files (with validation)
- Export to CSV
- Field mapping
- Error reporting
- Data transformation

---

## 📊 Phase 3: Dashboard & Reports (2 days)

### Dashboard Widget
**File**: `src/ui/widgets/dashboard_widget.py`

**Features**:
- Total stock overview
- Recent activity log
- Verification statistics
- Quick stats cards:
  - Total products
  - Total POs
  - Pending verifications
  - Low stock alerts
- Charts (optional):
  - Stock levels by product
  - Verifications over time

---

### Reports Widget
**File**: `src/ui/widgets/reports_widget.py`

**Features**:
- Report type selector
- Date range picker
- Filter options
- Preview table
- Export buttons (CSV, PDF optional)
- Print functionality

**Report Types**:
1. Stock Summary Report
2. Coupon Verification Report
3. Delivery Note
4. Activity Log Report

---

## 🎨 Phase 4: UI Polish & Validation (2 days)

### Common Dialog
**File**: `src/ui/dialogs/add_edit_dialog.py`

**Features**:
- Generic CRUD dialog
- Form validation
- Required field indicators
- Date pickers
- Combo boxes for foreign keys
- Error messages

---

### Validators
**File**: `src/utils/validators.py`

**Functions**:
- CPR validation
- Reference format validation
- Quantity validation
- Date range validation
- Duplicate checking

---

### Styling
**File**: `src/resources/styles/stylesheet.qss`

**Features**:
- Modern color scheme
- Button styling
- Table styling
- Status indicators
- Dark mode (optional)

---

## 🧪 Phase 5: Testing (2 days)

### Database Tests
**File**: `tests/test_models.py`

- Model validation
- Relationship integrity
- Constraint testing

---

### Service Tests
**File**: `tests/test_services.py`

- Stock calculation logic
- Coupon verification
- Report generation

---

### Integration Tests
**File**: `tests/test_integration.py`

- Full workflow tests
- Import/Export
- Backup/Restore

---

## 📦 Phase 6: Packaging (1-2 days)

### Installer Creation
**File**: `build_installer.py`

**Tools**:
- PyInstaller for executable
- Inno Setup for Windows installer

**Deliverables**:
- Standalone .exe
- Windows installer
- User manual (PDF)

---

## 🚀 Future Enhancements (Post v1.0)

### Phase 7: Advanced Features
- [ ] Barcode/QR code scanning for coupons
- [ ] Multi-user support with login
- [ ] Role-based permissions
- [ ] Data encryption for CPR
- [ ] Automated daily backups
- [ ] Email notifications
- [ ] Advanced analytics dashboard

### Phase 8: Web Migration
- [ ] FastAPI backend
- [ ] React/Vue frontend
- [ ] PostgreSQL database
- [ ] REST API
- [ ] Authentication system
- [ ] Cloud deployment

---

## Current Status Summary

```
Foundation:          ████████████████████ 100%
CRUD Widgets:        ░░░░░░░░░░░░░░░░░░░░   0%
Business Logic:      ░░░░░░░░░░░░░░░░░░░░   0%
Dashboard/Reports:   ░░░░░░░░░░░░░░░░░░░░   0%
UI Polish:           ░░░░░░░░░░░░░░░░░░░░   0%
Testing:             ░░░░░░░░░░░░░░░░░░░░   0%
Packaging:           ░░░░░░░░░░░░░░░░░░░░   0%

Overall Progress:    ███░░░░░░░░░░░░░░░░░  15%
```

---

## Estimated Timeline

| Phase | Duration | Status |
|-------|----------|--------|
| Foundation | 2 days | ✅ DONE |
| CRUD Widgets | 3-4 days | 📍 NEXT |
| Business Logic | 2-3 days | ⏳ Pending |
| Dashboard/Reports | 2 days | ⏳ Pending |
| UI Polish | 2 days | ⏳ Pending |
| Testing | 2 days | ⏳ Pending |
| Packaging | 1-2 days | ⏳ Pending |
| **Total** | **14-17 days** | **~15% Complete** |

---

## Next Action Items

1. ✅ Set up Python virtual environment
2. ✅ Install dependencies (`pip install -r requirements.txt`)
3. ✅ Test run application (`python src/main.py`)
4. 🔨 Build Products Widget (Priority 1)
5. 🔨 Build Distribution Locations Widget
6. 🔨 Build Medical Centres Widget
7. 🔨 Build Purchase Orders Widget
8. 🔨 Build Coupons Widget

**Ready to start building?** Let's tackle the Products Widget first! 🚀
