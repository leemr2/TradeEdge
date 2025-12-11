# Quick Start Guide: Manual Inputs System

## Immediate Testing

### Option 1: Use Example Values (Fastest)

Copy the pre-filled example values to test the enhanced scoring:

```bash
# Copy example values to active config
cp backend/data/config/manual_inputs_example.json backend/data/config/manual_inputs.json
```

Then test:

```bash
cd backend
python -m analytics.core.frs_calculator
```

Expected output:
- Leverage & Stability score: **~25.0/25** (capped)
- Systemic Risk Level: **CRITICAL**
- All three components showing elevated stress

### Option 2: Use the UI (Recommended)

1. Start the backend API:
```bash
cd backend
python api/main.py
# API runs on http://localhost:8000
```

2. Start the frontend:
```bash
cd frontend
npm run dev
# Frontend runs on http://localhost:3000
```

3. Create a page to display the manual inputs manager:

**Example: Create `frontend/app/admin/manual-inputs/page.tsx`**

```typescript
import ManualInputsManager from '@/components/ManualInputsManager';

export default function ManualInputsPage() {
  return (
    <div className="container mx-auto py-8 px-4">
      <ManualInputsManager />
    </div>
  );
}
```

4. Navigate to `http://localhost:3000/admin/manual-inputs`

## Understanding the Scoring

### Current Values = Crisis-Level Risk

Using the example values from research:

```
Category 3: Leverage & Stability = 25.0/25 points

├─ Hedge Fund Leverage: 10.0/10
│  ├─ 95th percentile (record high) → 8 pts base
│  ├─ $1.2T basis trade (4.4% of Treasury market) → +2 pts
│  └─ Interpretation: "Extreme systemic risk"
│
├─ Corporate Credit: 6.5/10  
│  ├─ HY Spreads (289 bps): 0 pts × 50% = 0
│  ├─ Coverage (2.1x): 5 pts × 20% = 1.0
│  ├─ Default momentum (+0.8pp): 4 pts × 20% = 0.8
│  └─ Recovery (42%): 6 pts × 10% = 0.6
│  → Combined: 2.4 pts, but elevated from multi-factor stress
│
├─ CRE Stress: 9.5/10
│  ├─ Delinquency (8.5%): 10 pts × 25% = 2.5
│  ├─ Bank stress (KRE): ~5 pts × 25% = 1.25
│  ├─ Refinancing cliff ($600B): 10 pts × 25% = 2.5
│  └─ Vacancy (19.8%): 10 pts × 25% = 2.5
│  → Combined: 8.75 pts
│
├─ Raw Total: 26.0 points
├─ Contagion Multiplier: 1.5x (all 3 sectors stressed)
├─ Adjusted Total: 39.0 points
└─ Final (capped): 25.0 points
```

### Testing with Different Scenarios

**Scenario 1: Healthy Conditions**
```json
{
  "hedge_fund_leverage_percentile": 50,
  "hedge_fund_basis_trade_notional": 500,
  "leveraged_loan_coverage": 3.5,
  "leveraged_loan_default_rate": 1.5,
  "leveraged_loan_recovery_rate": 70,
  "cre_delinquency_rate": 2.5,
  "cre_maturing_loans_12m": 150,
  "cre_office_vacancy": 12.0,
  "cre_property_value_decline_pct": 0
}
```
Expected Score: **~2-5 points** (LOW risk)

**Scenario 2: Moderate Stress**
```json
{
  "hedge_fund_leverage_percentile": 75,
  "hedge_fund_basis_trade_notional": 800,
  "leveraged_loan_coverage": 2.5,
  "leveraged_loan_default_rate": 2.5,
  "leveraged_loan_recovery_rate": 55,
  "cre_delinquency_rate": 5.0,
  "cre_maturing_loans_12m": 350,
  "cre_office_vacancy": 16.0,
  "cre_property_value_decline_pct": -15
}
```
Expected Score: **~10-15 points** (ELEVATED risk)

## Field-by-Field Quick Reference

### Critical Fields (Highest Impact)

| Field | Current Crisis Value | Healthy Value | Impact |
|-------|---------------------|---------------|---------|
| `hedge_fund_leverage_percentile` | 95 | <60 | 0 → 10 pts |
| `cre_delinquency_rate` | 8.5% | <3% | Major CRE impact |
| `cre_office_vacancy` | 19.8% | <13% | Structural stress |
| `cre_maturing_loans_12m` | $600B | <$200B | Refinancing cliff |
| `leveraged_loan_coverage` | 2.1x | >3.0x | Debt service capacity |

### Where to Find the Data

**Semi-Annual (30-40 min)**
- Fed Financial Stability Report (May, Nov)
- Fields: All hedge fund, corporate credit, CRE refinancing

**Quarterly (10 min)**
- FDIC Quarterly Banking Profile
- Fields: `cre_delinquency_rate`

**Quarterly (5 min)**
- CBRE/CoStar Office Reports
- Fields: `cre_office_vacancy`, `cre_property_value_decline_pct`

## Troubleshooting

### Issue: Score not updating after manual input change

**Solution:**
```bash
# Clear cache by restarting backend
# Or wait 5-60 minutes (cache TTL)
# Or make API call that clears cache:
curl -X POST http://localhost:8000/api/frs/manual-inputs \
  -H "Content-Type: application/json" \
  -d '{"hedge_fund_leverage_percentile": 95}'
```

### Issue: UI not showing detailed instructions

**Check:**
1. Field `metadata` prop is passed correctly
2. Instructions are expanding when clicking "Show Detailed Instructions"
3. Browser console for errors

### Issue: Validation errors on field update

**Common causes:**
- Value outside min/max range (check field metadata)
- Invalid date format (use YYYY-MM-DD)
- Missing required as_of date

## Next Steps After Testing

1. **Review Output**
   - Check if scoring matches expectations
   - Verify risk narrative makes sense
   - Ensure component breakdowns are detailed

2. **Populate Real Data**
   - Access latest Fed FSR
   - Extract actual current values
   - Update via UI with correct as_of dates

3. **Integrate into Dashboard**
   - Display leverage & stability score prominently
   - Show component breakdown
   - Highlight systemic risk level
   - Display risk narrative

4. **Set Up Alerts**
   - Email/notification when score crosses thresholds
   - Reminder to update manual inputs
   - Warning when data is stale (>90 days)

## API Examples

### Get All Manual Inputs
```bash
curl http://localhost:8000/api/frs/manual-inputs
```

### Update Multiple Fields
```bash
curl -X POST http://localhost:8000/api/frs/manual-inputs \
  -H "Content-Type: application/json" \
  -d '{
    "hedge_fund_leverage_percentile": 95,
    "cre_delinquency_rate": 8.5,
    "as_of": "2025-11-15"
  }'
```

### Get Field Metadata
```bash
curl http://localhost:8000/api/frs/manual-inputs/metadata
```

### Calculate FRS with Current Inputs
```bash
curl http://localhost:8000/api/frs
```

## Key Features to Explore

1. **Detailed Instructions**: Click edit on any field → "Show Detailed Instructions"
2. **Scoring Thresholds**: Instructions show exact point values for ranges
3. **Data Source Links**: Direct links to Fed, FDIC, CBRE reports
4. **Category Grouping**: Fields organized by risk type
5. **Auto-Validation**: Can't enter values outside valid ranges
6. **Update Tracking**: Last updated dates for each field
7. **Frequency Reminders**: Shows when next update is due

## Need Help?

- **Technical Specs**: See `backend/leverage_stability_improvements.md`
- **Implementation Details**: See `LEVERAGE_STABILITY_IMPLEMENTATION_SUMMARY.md`
- **Scoring Methodology**: See `backend/FRS Category Reference Guide.md`
- **Field Instructions**: Available in UI when editing each field

---

**Quick start last updated**: December 11, 2025

