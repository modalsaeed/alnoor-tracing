# Verification Workflow Update

## Overview
The verification workflow has been completely redesigned to match the actual business process where the medical centre/ministry of health confirms coupon data and provides a verification reference. The system now supports batch verification of multiple coupons with a single verification reference.

## Changes Made

### 1. Verification Dialog (`src/ui/dialogs/verify_coupon_dialog.py`)

#### Key Changes:
- **Multi-coupon support**: Dialog now accepts `List[PatientCoupon]` instead of single coupon
- **Manual verification reference**: Replaced auto-generated reference with manual input field
- **Coupon details table**: Added QTableWidget to display all coupons being verified
- **Batch stock validation**: Checks stock availability for all selected coupons grouped by product
- **Batch processing**: Applies same verification reference to all coupons in one operation

#### New UI Components:
```python
# Coupons table showing all coupons to verify
self.coupons_table = QTableWidget()
self.coupons_table.setHorizontalHeaderLabels([
    "Coupon Ref", "Patient Name", "CPR", "Product", "Quantity"
])

# Manual verification reference input
self.verification_ref_input = QLineEdit()
self.verification_ref_input.setPlaceholderText("Enter verification reference (e.g., VER-2024-001)")
```

#### New Methods:
- `load_coupon_details()`: Populates table with coupon information
- `check_stock_availability()`: Validates stock for all coupons, groups by product
- `verify_coupons()`: Processes batch verification with single reference

#### Removed:
- `generate_verification_reference()`: Auto-generation method removed
- Single coupon form fields: Replaced with table view
- Auto-generated verification display: Replaced with manual input

### 2. Coupons Widget (`src/ui/widgets/coupons_widget.py`)

#### Key Changes:
- **Multi-selection enabled**: Table selection mode changed from `SingleSelection` to `ExtendedSelection`
- **Batch verification support**: `verify_coupon()` method now handles multiple selected rows
- **Already-verified handling**: Smart filtering of already-verified coupons with user prompts
- **Tooltip added**: Button tooltip explains Ctrl+Click for multiple selection

#### Selection Behavior:
```python
# Allow multi-selection with Ctrl+Click and Shift+Click
self.table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
```

#### Updated verify_coupon() Logic:
1. Get all selected rows (allows 0 to N selections)
2. Check if any are already verified
3. Prompt user if mix of verified/unverified
4. Filter to only unverified coupons
5. Pass list to verification dialog

## Business Process Flow

### Old Workflow (Incorrect):
1. User creates coupon
2. User clicks "Verify"
3. System generates verification reference automatically
4. System deducts stock

### New Workflow (Correct):
1. User creates one or more coupons
2. User submits coupon data to medical centre/ministry
3. Medical centre/ministry confirms data is correct
4. Medical centre/ministry provides verification reference to user
5. User selects multiple coupons in system (Ctrl+Click)
6. User clicks "Verify Selected"
7. User enters verification reference from medical centre/ministry
8. System validates stock availability for all coupons
9. System deducts stock and marks all coupons as verified with same reference

## User Interface

### Verification Dialog Components:

```
┌─────────────────────────────────────────────────────────────┐
│ ✅ Verify 3 Coupon(s)                                       │
├─────────────────────────────────────────────────────────────┤
│ ℹ️ Info: Enter the verification reference provided by      │
│   the medical centre/ministry after they confirm the data.  │
│                                                              │
│ 📋 Coupons to Verify                                        │
│ ┌───────────────────────────────────────────────────────┐  │
│ │ Coupon Ref │ Patient │ CPR │ Product │ Quantity      │  │
│ ├────────────┼─────────┼─────┼─────────┼──────────────┤  │
│ │ CPN-001    │ John    │ 123 │ Prod A  │ 10 pieces    │  │
│ │ CPN-002    │ Jane    │ 456 │ Prod A  │ 5 pieces     │  │
│ │ CPN-003    │ Bob     │ 789 │ Prod B  │ 20 pieces    │  │
│ └───────────────────────────────────────────────────────┘  │
│                                                              │
│ 📦 Stock Availability                                       │
│ ✅ All required stock is available for 3 coupon(s)         │
│                                                              │
│ 🔑 Verification Reference (Provided by Medical Centre)     │
│ Enter the verification reference provided by the medical    │
│ centre/ministry after they confirm the data.                │
│ ┌───────────────────────────────────────────────────────┐  │
│ │ VER-2024-001                                          │  │
│ └───────────────────────────────────────────────────────┘  │
│                                                              │
│                      [ Cancel ] [ ✅ Verify & Deduct Stock ]│
└─────────────────────────────────────────────────────────────┘
```

### Coupons Widget:
- Table now supports multi-selection (Ctrl+Click, Shift+Click)
- "Verify Selected" button tooltip: "Verify one or more selected coupons (Ctrl+Click for multiple)"

## Stock Validation

The new batch validation groups coupons by product and checks total requirements:

```python
# Example: 3 coupons
# Coupon 1: Product A, 10 pieces
# Coupon 2: Product A, 5 pieces
# Coupon 3: Product B, 20 pieces

# Validation checks:
# Product A: Need 15 pieces total (10 + 5)
# Product B: Need 20 pieces total

# Shows:
# ✅ Product A: 15 pieces available (Current: 50, After: 35)
# ✅ Product B: 20 pieces available (Current: 30, After: 10)
```

## Error Handling

### No Selection:
```
⚠️ No Selection
Please select one or more coupons to verify.

Tip: Hold Ctrl to select multiple coupons, or Shift to select a range.
```

### All Already Verified:
```
ℹ️ Already Verified
All 3 selected coupon(s) have already been verified.

Please select unverified coupons to verify.
```

### Mixed Selection (Some Verified):
```
⚠️ Some Already Verified
2 of 5 selected coupons are already verified.

Do you want to continue and verify only the unverified ones?
[Yes] [No]
```

### Missing Verification Reference:
```
⚠️ Missing Verification Reference
Please enter the verification reference provided by the medical centre/ministry.
```

### Insufficient Stock:
```
❌ Insufficient stock for some products
❌ Product A: Insufficient stock (Need: 50, Available: 30, Short: 20)
✅ Product B: 20 pieces available (Current: 100, After: 80)

[Verify & Deduct Stock] button disabled
```

## Confirmation Dialog

```
❓ Confirm Batch Verification
Are you sure you want to verify 3 coupon(s)?

Verification Reference: VER-2024-001

Coupons:
  • John Doe (123456) - Product A - 10 pieces
  • Jane Smith (789012) - Product A - 5 pieces
  • Bob Johnson (345678) - Product B - 20 pieces

Total Quantity: 35 pieces

Stock will be deducted using FIFO method.
This action cannot be undone except by deleting the coupons.

[Yes] [No]
```

## Success Message

```
✅ Batch Verification Successful
Successfully verified 3 coupon(s)!

Verification Reference: VER-2024-001
Total Stock Deducted: 35 pieces

All coupons have been marked as verified.

[OK]
```

## Database Updates

Each verified coupon gets:
```python
coupon.verified = True
coupon.verification_reference = "VER-2024-001"  # Same for all in batch
coupon.verified_at = datetime.now()  # Individual timestamps
```

Stock deduction via FIFO for each coupon:
```python
self.stock_service.deduct_stock(
    coupon.product_id,
    coupon.quantity_pieces,
    coupon.id
)
```

## Testing Checklist

- [ ] Create multiple coupons for same product
- [ ] Create multiple coupons for different products
- [ ] Select single coupon and verify
- [ ] Select multiple coupons (Ctrl+Click) and verify
- [ ] Select range of coupons (Shift+Click) and verify
- [ ] Try to verify already-verified coupons
- [ ] Try to verify mix of verified and unverified
- [ ] Try to verify without entering verification reference
- [ ] Try to verify with insufficient stock
- [ ] Verify batch with sufficient stock
- [ ] Confirm stock is deducted correctly (FIFO)
- [ ] Confirm all coupons get same verification reference
- [ ] Check activity log entries

## Benefits

1. **Matches Business Process**: System now reflects actual workflow with external verification source
2. **Efficiency**: Verify multiple coupons at once instead of one-by-one
3. **Traceability**: Single verification reference can track a batch of related coupons
4. **User Control**: Users enter references from authoritative source (ministry)
5. **Better UX**: Multi-selection with visual feedback and clear instructions
6. **Stock Safety**: Validates availability for all coupons before any deduction
7. **Error Recovery**: Partial success handling if some coupons fail

## Migration Notes

**No database migration needed** - The `verification_reference` field already exists in the `patient_coupons` table. Existing verified coupons keep their auto-generated references, new verifications will have manually entered references.

## Code Files Changed

1. `src/ui/dialogs/verify_coupon_dialog.py` - Complete rewrite
2. `src/ui/widgets/coupons_widget.py` - Updated selection mode and verify method

## Related Documentation

- See `DEPLOYMENT.md` for build and deployment instructions
- See `ROADMAP.md` for project completion status
- See `README.md` for general application overview
