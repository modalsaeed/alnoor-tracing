# Quick Testing Guide - Verification Workflow

## Prerequisites
1. Application is running
2. At least one product exists in database
3. At least one purchase order with available stock exists
4. At least one medical centre exists
5. At least one distribution location exists

## Test Scenario 1: Single Coupon Verification

### Steps:
1. Navigate to **Coupons** tab
2. Click **Add Coupon**
3. Fill in all fields:
   - Coupon Reference: `CPN-TEST-001`
   - Patient Name: `John Doe`
   - CPR: `123456789`
   - Product: Select any product with available stock
   - Quantity: `5`
   - Medical Centre: Select any centre
   - Distribution Location: Select any location
   - Date: Today's date
4. Click **Save**
5. Select the newly created coupon in the table
6. Click **Verify Selected**
7. In the verification dialog:
   - Check that the table shows 1 coupon with correct details
   - Check that stock availability shows "✅ All required stock is available"
   - Enter verification reference: `VER-MINISTRY-2024-001`
8. Click **✅ Verify & Deduct Stock**
9. Confirm in the dialog
10. Verify success message appears

### Expected Results:
- ✅ Coupon status changes to "Verified"
- ✅ Verification reference appears in table: `VER-MINISTRY-2024-001`
- ✅ Stock is deducted from purchase orders (FIFO)
- ✅ Activity log entry created

## Test Scenario 2: Batch Verification (Same Product)

### Steps:
1. Navigate to **Coupons** tab
2. Create 3 coupons for the **same product**:
   - Coupon 1: `CPN-BATCH-001`, Patient: `Alice Brown`, Quantity: `10`
   - Coupon 2: `CPN-BATCH-002`, Patient: `Bob Smith`, Quantity: `15`
   - Coupon 3: `CPN-BATCH-003`, Patient: `Carol White`, Quantity: `20`
3. Hold **Ctrl** and click each coupon to select all 3
4. Click **Verify Selected**
5. In the verification dialog:
   - Check that table shows all 3 coupons
   - Check stock availability shows total needed: `45 pieces`
   - Enter verification reference: `VER-BATCH-001`
6. Click **✅ Verify & Deduct Stock**
7. Confirm in dialog
8. Verify success message: "Successfully verified 3 coupon(s)!"

### Expected Results:
- ✅ All 3 coupons marked as verified
- ✅ All 3 have same verification reference: `VER-BATCH-001`
- ✅ Total 45 pieces deducted from stock
- ✅ Stock deducted using FIFO method

## Test Scenario 3: Batch Verification (Multiple Products)

### Steps:
1. Create 3 coupons for **different products**:
   - Coupon 1: Product A, Quantity: `10`
   - Coupon 2: Product B, Quantity: `5`
   - Coupon 3: Product A, Quantity: `8`
2. Select all 3 using Ctrl+Click
3. Click **Verify Selected**
4. Check verification dialog:
   - Should show all 3 coupons
   - Stock availability should show:
     - Product A: 18 pieces needed (10 + 8)
     - Product B: 5 pieces needed
5. Enter verification reference: `VER-MULTI-PROD-001`
6. Verify

### Expected Results:
- ✅ All 3 coupons verified
- ✅ Product A stock deducted 18 pieces total
- ✅ Product B stock deducted 5 pieces
- ✅ Same verification reference on all

## Test Scenario 4: Range Selection

### Steps:
1. Create 5 coupons
2. Click first coupon
3. Hold **Shift** and click fifth coupon
4. All 5 should be selected
5. Click **Verify Selected**
6. Enter verification reference
7. Verify all

### Expected Results:
- ✅ All 5 coupons selected correctly
- ✅ Batch verification works for range selection

## Test Scenario 5: Already Verified Handling

### Steps:
1. Select a coupon that is already verified
2. Click **Verify Selected**
3. Check message

### Expected Results:
- ℹ️ "All selected coupons have already been verified" message
- Dialog does not open

## Test Scenario 6: Mixed Verified/Unverified

### Steps:
1. Select 3 coupons:
   - 2 already verified
   - 1 not verified
2. Click **Verify Selected**
3. Check prompt

### Expected Results:
- ⚠️ Message: "2 of 3 selected coupons are already verified"
- Prompt: "Continue and verify only unverified ones?"
- If Yes: Dialog opens with only 1 coupon
- If No: Operation cancelled

## Test Scenario 7: Missing Verification Reference

### Steps:
1. Select unverified coupon(s)
2. Click **Verify Selected**
3. In dialog, leave verification reference field **empty**
4. Click **✅ Verify & Deduct Stock**

### Expected Results:
- ⚠️ Warning: "Please enter the verification reference provided by the medical centre/ministry"
- Focus moves to verification reference input
- No verification occurs

## Test Scenario 8: Insufficient Stock

### Steps:
1. Find a product with low stock (e.g., 10 pieces available)
2. Create a coupon requiring more than available (e.g., 50 pieces)
3. Try to verify

### Expected Results:
- ❌ Stock availability shows red: "Insufficient stock"
- Shows: "Need: 50, Available: 10, Short: 40"
- **Verify & Deduct Stock** button is **disabled**
- Cannot proceed with verification

## Test Scenario 9: Partial Batch Failure

### Steps:
This is hard to test without breaking the database. Skip for now.

## Test Scenario 10: FIFO Stock Deduction Verification

### Steps:
1. Go to **Purchase Orders** tab
2. Note the IDs and quantities of orders for Product A:
   - PO-001: 50 pieces, Date: 2024-01-01
   - PO-002: 30 pieces, Date: 2024-01-15
   - PO-003: 20 pieces, Date: 2024-02-01
3. Create and verify a coupon for Product A, Quantity: 60
4. Check **Reports** > **FIFO Stock Usage**

### Expected Results:
- ✅ PO-001 fully depleted (50 pieces used)
- ✅ PO-002 partially used (10 pieces used, 20 remaining)
- ✅ PO-003 untouched (20 pieces remaining)

## Test Scenario 11: Activity Log

### Steps:
1. Verify any coupon(s)
2. Go to **Reports** tab
3. View activity log

### Expected Results:
- ✅ Entry: "Coupon CPN-XXX verified with reference VER-XXX"
- ✅ Correct timestamp
- ✅ One entry per verified coupon

## Test Scenario 12: Verification Reference Format

### Steps:
Try various reference formats:
- `VER-2024-001` ✅
- `vr-test-123` ✅ (converted to uppercase)
- `MINISTRY-HEALTH-20241108` ✅
- `12345` ✅
- Empty string ❌ (validation error)
- Spaces only ❌ (trimmed, then validation error)

### Expected Results:
- All non-empty values accepted
- All values converted to uppercase automatically
- Empty values rejected with warning

## Test Scenario 13: Tooltip Verification

### Steps:
1. Hover over **Verify Selected** button
2. Check tooltip

### Expected Results:
- ✅ Tooltip shows: "Verify one or more selected coupons (Ctrl+Click for multiple)"

## Test Scenario 14: Delete Verified Coupon (Stock Restoration)

### Steps:
1. Verify a coupon (stock gets deducted)
2. Note the stock levels
3. Select the verified coupon
4. Click **Delete**
5. Confirm deletion

### Expected Results:
- ⚠️ Warning about deleting verified coupon
- "Deleting will RESTORE the stock back to purchase orders"
- After deletion: stock is restored to the purchase orders
- FIFO deduction records are rolled back

## Performance Test

### Steps:
1. Create 50 coupons
2. Select all 50 (Ctrl+A or Ctrl+Click all)
3. Click **Verify Selected**
4. Enter verification reference
5. Verify all

### Expected Results:
- Dialog loads in < 2 seconds
- Table shows all 50 coupons
- Stock validation completes in < 3 seconds
- Verification completes in < 5 seconds
- No errors or crashes
- All 50 coupons marked verified

## Regression Tests

Run these to ensure old functionality still works:

### Test: Add Coupon
- ✅ Can create new coupon
- ✅ All fields validated
- ✅ Coupon reference required and manual

### Test: Edit Coupon
- ✅ Can edit unverified coupon
- ✅ Cannot edit verified coupon
- ✅ Changes saved correctly

### Test: Search and Filter
- ✅ Search by patient name works
- ✅ Search by CPR works
- ✅ Search by verification reference works
- ✅ Filter by status works
- ✅ Filter by product works
- ✅ Filter by medical centre works
- ✅ Date range filter works

### Test: Reports
- ✅ Stock report accurate
- ✅ FIFO report shows correct deductions
- ✅ Activity log shows verification entries

## Bug Checklist

Ensure these are fixed:
- ✅ Icon constants (singular, not plural)
- ✅ Import paths (absolute, not relative)
- ✅ Lazy loading errors (eager loading with joinedload)
- ✅ Stock report dictionary keys (total_remaining, total_used)
- ✅ Stock alerts parameter (threshold_percentage)
- ✅ Coupon reference (manual entry, not auto-generated)

## Success Criteria

All tests pass if:
1. Single and batch verification work correctly
2. Multi-selection works (Ctrl+Click, Shift+Click)
3. Manual verification reference entry required and validated
4. Stock validation accurate for batches
5. FIFO deduction correct
6. Already-verified coupons handled gracefully
7. Error messages clear and helpful
8. No crashes or exceptions
9. All data saved correctly to database
10. Activity logs created

## Report Template

```
Test Date: _______________
Tester: _______________

| Scenario | Status | Notes |
|----------|--------|-------|
| 1. Single Coupon | ☐ Pass ☐ Fail | |
| 2. Batch Same Product | ☐ Pass ☐ Fail | |
| 3. Batch Multi Product | ☐ Pass ☐ Fail | |
| 4. Range Selection | ☐ Pass ☐ Fail | |
| 5. Already Verified | ☐ Pass ☐ Fail | |
| 6. Mixed Verified | ☐ Pass ☐ Fail | |
| 7. Missing Ref | ☐ Pass ☐ Fail | |
| 8. Insufficient Stock | ☐ Pass ☐ Fail | |
| 10. FIFO Deduction | ☐ Pass ☐ Fail | |
| 11. Activity Log | ☐ Pass ☐ Fail | |
| 12. Ref Format | ☐ Pass ☐ Fail | |
| 13. Tooltip | ☐ Pass ☐ Fail | |
| 14. Delete Verified | ☐ Pass ☐ Fail | |
| Performance Test | ☐ Pass ☐ Fail | |

Overall Status: ☐ Pass ☐ Fail

Issues Found:
1. _______________
2. _______________
3. _______________
```
