"""
Manual Inputs Manager
Loads and saves manual input values from JSON config file
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime


def get_manual_inputs_path() -> Path:
    """Get path to manual inputs config file"""
    backend_path = Path(__file__).parent.parent.parent
    config_dir = backend_path / 'data' / 'config'
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / 'manual_inputs.json'


def get_default_manual_inputs() -> Dict[str, Any]:
    """
    Get default manual input values with comprehensive documentation
    
    Returns:
        Dictionary with all manual input fields, default values, and metadata
    """
    return {
        # ============================================================
        # HEDGE FUND LEVERAGE (Category 3.1)
        # Data Source: Federal Reserve Financial Stability Report
        # Update Frequency: Semi-annual (May, November)
        # ============================================================
        'hedge_fund_leverage_percentile': 50,
        'hedge_fund_leverage_as_of': '2025-11-01',
        'hedge_fund_basis_trade_concern': False,
        'hedge_fund_basis_trade_notional': 0,  # Billions USD
        'primary_dealer_slr_ratio': 7.0,  # % - Supplementary Leverage Ratio
        
        # ============================================================
        # CORPORATE CREDIT (Category 3.2)
        # Data Sources: Fed FSR + FDIC Risk Review
        # Update Frequency: Semi-annual (May, November)
        # ============================================================
        'leveraged_loan_coverage': 2.5,  # Interest coverage ratio (EBITDA/Interest)
        'leveraged_loan_coverage_as_of': '2025-11-01',
        'leveraged_loan_default_rate': 2.0,  # Current default rate %
        'leveraged_loan_default_rate_6m_ago': 2.0,  # For momentum calculation
        'leveraged_loan_default_as_of': '2025-11-01',
        'leveraged_loan_recovery_rate': 65,  # % recovery on defaulted loans
        'leveraged_loan_recovery_as_of': '2025-11-01',
        
        # ============================================================
        # CRE STRESS - Delinquency (Category 3.3.1)
        # Data Source: FDIC Quarterly Banking Profile
        # Update Frequency: Quarterly (~6 weeks after quarter end)
        # ============================================================
        'cre_delinquency_rate': 5.0,  # % of CRE loans 90+ days past due
        'cre_delinquency_as_of': '2025-11-15',
        
        # ============================================================
        # CRE STRESS - Refinancing Cliff (Category 3.3.3)
        # Data Sources: Fed FSR + FSOC Annual Report + Trepp
        # Update Frequency: Semi-annual
        # ============================================================
        'cre_maturing_loans_12m': 0,  # Billions USD maturing next 12 months
        'cre_maturing_loans_24m': 0,  # Billions USD total 2-year maturity wall
        'cre_refi_spread_shock': 0,  # bps higher than original rates
        'cre_refinancing_as_of': '2025-11-01',
        
        # ============================================================
        # CRE STRESS - Vacancy/Structural (Category 3.3.4)
        # Data Sources: CBRE, CoStar, Moody's Analytics
        # Update Frequency: Quarterly
        # ============================================================
        'cre_office_vacancy': 12.0,  # % office vacancy rate
        'cre_office_vacancy_as_of': '2025-11-01',
        'cre_property_value_decline_pct': 0,  # % decline from peak (negative number)
        
        # ============================================================
        # METADATA
        # ============================================================
        'last_full_update': datetime.now().isoformat(),
        'version': '2.0',  # Enhanced scoring with multi-factor analysis
    }


def load_manual_inputs() -> Dict[str, Any]:
    """
    Load manual inputs from JSON file
    
    Returns:
        Dictionary with manual input values and metadata
    """
    config_path = get_manual_inputs_path()
    defaults = get_default_manual_inputs()
    
    if not config_path.exists():
        # Create file with defaults
        save_manual_inputs(defaults)
        return defaults
    
    try:
        with open(config_path, 'r') as f:
            data = json.load(f)
        
        # Merge with defaults to ensure all fields exist
        # (in case new fields were added in an update)
        merged = defaults.copy()
        merged.update(data)
        
        # Update version if needed
        if merged.get('version') != defaults['version']:
            merged['version'] = defaults['version']
            save_manual_inputs(merged)
        
        return merged
    except Exception as e:
        print(f"Warning: Error loading manual inputs: {e}, using defaults")
        return defaults


def save_manual_inputs(inputs: Dict[str, Any]) -> None:
    """
    Save manual inputs to JSON file
    
    Args:
        inputs: Dictionary with manual input values
    """
    config_path = get_manual_inputs_path()
    
    try:
        with open(config_path, 'w') as f:
            json.dump(inputs, f, indent=2)
    except Exception as e:
        print(f"Error saving manual inputs: {e}")
        raise


def update_manual_input(key: str, value: Any, as_of: Optional[str] = None) -> Dict[str, Any]:
    """
    Update a single manual input value
    
    Args:
        key: Input key (e.g., 'hedge_fund_leverage_percentile')
        value: New value
        as_of: Optional date string for when this value was recorded
    
    Returns:
        Updated manual inputs dictionary
    """
    inputs = load_manual_inputs()
    inputs[key] = value
    
    if as_of:
        inputs[f'{key}_as_of'] = as_of
    else:
        inputs[f'{key}_as_of'] = datetime.now().isoformat()
    
    inputs['last_full_update'] = datetime.now().isoformat()
    
    save_manual_inputs(inputs)
    return inputs


def get_field_metadata() -> Dict[str, Dict[str, Any]]:
    """
    Get comprehensive metadata for all manual input fields
    Used by frontend to display field labels, descriptions, ranges, and instructions
    
    Returns:
        Dictionary mapping field names to their metadata
    """
    return {
        # HEDGE FUND LEVERAGE
        'hedge_fund_leverage_percentile': {
            'label': 'Hedge Fund Leverage Percentile',
            'description': 'Historical percentile ranking of hedge fund gross leverage',
            'category': 'Hedge Fund Leverage',
            'min': 0,
            'max': 100,
            'unit': 'percentile',
            'data_source': 'Federal Reserve Financial Stability Report',
            'frequency': 'Semi-annual (May, November)',
            'instructions': (
                "1. Access the latest Fed Financial Stability Report\n"
                "2. Navigate to Section 3: 'Leverage in the Financial System'\n"
                "3. Find Chart 3-1: 'Hedge Fund Gross Leverage'\n"
                "4. Look for the current percentile ranking vs historical distribution\n"
                "5. Enter the percentile value (e.g., 95 = 95th percentile)\n\n"
                "Interpretation:\n"
                "- <60th: Low systemic risk (0 points)\n"
                "- 60-75th: Moderately elevated (1-4 points)\n"
                "- 75-90th: Elevated but stable (5 points)\n"
                ">90th: Record leverage - maximum risk (8-10 points)"
            ),
            'url': 'https://www.federalreserve.gov/publications/financial-stability-report.htm'
        },
        'hedge_fund_basis_trade_concern': {
            'label': 'Basis Trade Regulator Concern',
            'description': 'Has the Fed flagged basis trade concentration risk?',
            'category': 'Hedge Fund Leverage',
            'type': 'boolean',
            'data_source': 'Federal Reserve Financial Stability Report',
            'frequency': 'Semi-annual',
            'instructions': (
                "Read the hedge fund leverage section narrative. Flag as TRUE if:\n"
                "- Report uses terms: 'elevated', 'concentrated', 'fragility'\n"
                "- Specific warnings about Treasury basis trade risks\n"
                "- Concerns about unwind scenarios or market functioning\n\n"
                "When flagged, ensures minimum score of 8/10 for systemic risk"
            )
        },
        'hedge_fund_basis_trade_notional': {
            'label': 'Basis Trade Notional Value',
            'description': 'Estimated notional value of hedge fund Treasury basis trades',
            'category': 'Hedge Fund Leverage',
            'min': 0,
            'max': 5000,
            'unit': 'billions USD',
            'data_source': 'Fed FSR + Market Estimates',
            'frequency': 'Semi-annual',
            'instructions': (
                "Find estimates of total Treasury basis trade exposure:\n"
                "1. Check Fed FSR narrative (may cite market estimates)\n"
                "2. Look for: 'notional value', 'gross exposure'\n"
                "3. Enter value in billions USD\n\n"
                "Context: Treasury market size ~$27T\n"
                "- >$1.08T (4% of market): Extreme concentration risk\n"
                "- $810B-$1.08T (3-4%): High concentration\n"
                "- <$810B: Elevated but manageable"
            )
        },
        'primary_dealer_slr_ratio': {
            'label': 'Primary Dealer SLR Ratio',
            'description': 'Supplementary Leverage Ratio for primary dealers',
            'category': 'Hedge Fund Leverage',
            'min': 4.0,
            'max': 10.0,
            'unit': '%',
            'data_source': 'Fed FSR Banking Section',
            'frequency': 'Semi-annual',
            'instructions': (
                "Find dealer capacity metrics in Fed FSR:\n"
                "1. Section on 'Banking System' or 'Market Liquidity'\n"
                "2. Look for 'dealer leverage', 'SLR', 'balance sheet capacity'\n"
                "3. Enter current SLR ratio as percentage\n\n"
                "Regulatory minimum: 5.0%\n"
                "- <5.5%: Constrained capacity - amplification risk (+1 point)\n"
                "- 5.5-6.0%: Tight capacity\n"
                "- >6.0%: Adequate capacity"
            )
        },
        
        # CORPORATE CREDIT
        'leveraged_loan_coverage': {
            'label': 'Leveraged Loan Interest Coverage',
            'description': 'Median interest coverage ratio (EBITDA / Interest Expense)',
            'category': 'Corporate Credit',
            'min': 0.5,
            'max': 5.0,
            'unit': 'ratio',
            'data_source': 'Fed FSR Corporate Debt Section',
            'frequency': 'Semi-annual',
            'instructions': (
                "Extract corporate interest coverage metrics:\n"
                "1. Fed FSR Section 2: 'Borrowing by Businesses and Households'\n"
                "2. Find table or chart: 'Interest Coverage Ratios'\n"
                "3. Look for median coverage for leveraged loan borrowers\n"
                "4. Enter ratio (e.g., 2.5 means 2.5x coverage)\n\n"
                "Interpretation:\n"
                "- >3.0: Healthy capacity (0 points)\n"
                "- 2.5-3.0: Moderate - watchlist (2 points)\n"
                "- 2.0-2.5: Weak coverage (5 points)\n"
                "- <2.0: Critical - minimal buffer (7-10 points)"
            )
        },
        'leveraged_loan_default_rate': {
            'label': 'Current Leveraged Loan Default Rate',
            'description': 'Current annual default rate on leveraged loans',
            'category': 'Corporate Credit',
            'min': 0,
            'max': 15,
            'unit': '% annual',
            'data_source': 'Fed FSR + FDIC Risk Review',
            'frequency': 'Semi-annual',
            'instructions': (
                "Find current leveraged loan default rate:\n"
                "1. Fed FSR corporate debt section\n"
                "2. Look for: 'default rates', 'loan performance'\n"
                "3. May also check FDIC Risk Review or S&P/LCD reports\n"
                "4. Enter current annual default rate as %\n\n"
                "Used to calculate default momentum (trend)"
            )
        },
        'leveraged_loan_default_rate_6m_ago': {
            'label': 'Leveraged Loan Default Rate (6M Ago)',
            'description': 'Default rate from 6 months prior for momentum calculation',
            'category': 'Corporate Credit',
            'min': 0,
            'max': 15,
            'unit': '% annual',
            'data_source': 'Fed FSR Historical + FDIC',
            'frequency': 'Semi-annual',
            'instructions': (
                "Enter default rate from 6 months ago:\n"
                "1. Check previous Fed FSR (from 6 months prior)\n"
                "2. Or historical data tables in current FSR\n"
                "3. Enter rate from ~6 months ago\n\n"
                "Momentum Scoring:\n"
                "- Change >+1.5pp: Rapid acceleration (10 points)\n"
                "- Change +1.0-1.5pp: Sharp increase (7 points)\n"
                "- Change +0.5-1.0pp: Rising steadily (4 points)\n"
                "- Change 0-0.5pp: Trending up (2 points)\n"
                "- Negative change: Improving (0 points)"
            )
        },
        'leveraged_loan_recovery_rate': {
            'label': 'Leveraged Loan Recovery Rate',
            'description': 'Percentage recovered on defaulted leveraged loans',
            'category': 'Corporate Credit',
            'min': 0,
            'max': 100,
            'unit': '% recovery',
            'data_source': 'Fed FSR + Moody\'s/S&P Reports',
            'frequency': 'Semi-annual',
            'instructions': (
                "Find average recovery rates on defaulted loans:\n"
                "1. Fed FSR corporate section may cite recovery rates\n"
                "2. Moody's/S&P publish annual recovery rate studies\n"
                "3. Enter % recovered (e.g., 42 = 42% recovery)\n\n"
                "Interpretation:\n"
                "- ≥60%: Normal recovery rates (0 points)\n"
                "- 50-60%: Below average (3 points)\n"
                "- 40-50%: Weak recoveries (6 points)\n"
                "- <40%: Crisis-level recoveries (10 points)\n\n"
                "Lower recoveries = higher loss severity when defaults occur"
            )
        },
        
        # CRE - DELINQUENCY
        'cre_delinquency_rate': {
            'label': 'CRE Delinquency Rate',
            'description': 'Percentage of CRE loans 90+ days past due or nonaccrual',
            'category': 'CRE Stress',
            'min': 0,
            'max': 20,
            'unit': '% of CRE loans',
            'data_source': 'FDIC Quarterly Banking Profile',
            'frequency': 'Quarterly',
            'instructions': (
                "Extract CRE delinquency from FDIC QBP:\n"
                "1. Access FDIC Quarterly Banking Profile\n"
                "2. Navigate to Table II-B: 'Loan Performance'\n"
                "3. Find row: 'Nonfarm Nonresidential' or 'Commercial Real Estate'\n"
                "4. Look for column: 'Noncurrent Rate' or '90+ Days Past Due'\n"
                "5. Enter percentage\n\n"
                "Scoring:\n"
                "- <3%: Low delinquency (0 points)\n"
                "- 3-5%: Early deterioration (3 points)\n"
                "- 5-6%: Concerning (5 points)\n"
                "- 6-8%: Significant stress (7 points)\n"
                "- ≥8%: Crisis levels (10 points)"
            ),
            'url': 'https://www.fdic.gov/analysis/quarterly-banking-profile/'
        },
        
        # CRE - REFINANCING CLIFF
        'cre_maturing_loans_12m': {
            'label': 'CRE Loans Maturing (12 Months)',
            'description': 'Commercial real estate loans maturing in next 12 months',
            'category': 'CRE Refinancing Cliff',
            'min': 0,
            'max': 2000,
            'unit': 'billions USD',
            'data_source': 'Fed FSR + Trepp + CBRE',
            'frequency': 'Semi-annual',
            'instructions': (
                "Find CRE maturity wall data:\n"
                "1. Fed FSR section on CRE markets\n"
                "2. Look for charts: 'CRE Debt Maturities', 'Refinancing Timeline'\n"
                "3. May cite Trepp or CBRE research\n"
                "4. Extract amount maturing in next 12 months (billions)\n\n"
                "Scoring:\n"
                "- <$200B: Manageable (0 points)\n"
                "- $200-400B: Elevated (3 points)\n"
                "- $400-600B: High pressure (6 points)\n"
                "- ≥$600B: Refinancing cliff (10 points)\n\n"
                "Context: Total CRE debt ~$5.6T, ~$1.2T maturing 2025-2026"
            )
        },
        'cre_maturing_loans_24m': {
            'label': 'CRE Loans Maturing (24 Months)',
            'description': 'Total CRE loans maturing over next 2 years',
            'category': 'CRE Refinancing Cliff',
            'min': 0,
            'max': 3000,
            'unit': 'billions USD',
            'data_source': 'Fed FSR + Trepp',
            'frequency': 'Semi-annual',
            'instructions': (
                "Total 2-year maturity wall:\n"
                "1. Same sources as 12-month metric\n"
                "2. Extract cumulative maturities over 24 months\n"
                "3. Provides context for refinancing pressure duration\n\n"
                "Informational - not directly scored"
            )
        },
        'cre_refi_spread_shock': {
            'label': 'CRE Refinancing Rate Shock',
            'description': 'Basis points higher than original rates at refinancing',
            'category': 'CRE Refinancing Cliff',
            'min': 0,
            'max': 500,
            'unit': 'basis points',
            'data_source': 'Fed FSR + Market Data',
            'frequency': 'Semi-annual',
            'instructions': (
                "Calculate rate shock for maturing CRE loans:\n"
                "1. Find typical origination rate for loans from 5-7 years ago\n"
                "2. Compare to current CRE lending rates\n"
                "3. Enter difference in basis points\n\n"
                "Example:\n"
                "- Original rate (2019): 4.0%\n"
                "- Current rate (2025): 6.5%\n"
                "- Shock: 250 bps\n\n"
                "Impact on scoring:\n"
                "- >300 bps: +2 points (extreme shock)\n"
                "- 200-300 bps: +1 point (significant shock)\n"
                "- <200 bps: No adjustment"
            )
        },
        
        # CRE - VACANCY/STRUCTURAL
        'cre_office_vacancy': {
            'label': 'Office Vacancy Rate',
            'description': 'National office vacancy rate',
            'category': 'CRE Structural Stress',
            'min': 5,
            'max': 30,
            'unit': '% vacant',
            'data_source': 'CBRE, CoStar, Moody\'s Analytics',
            'frequency': 'Quarterly',
            'instructions': (
                "Find current office vacancy rate:\n"
                "1. CBRE Quarterly Office Report\n"
                "2. CoStar market data\n"
                "3. Cited in Fed FSR or financial media\n"
                "4. Enter national average vacancy rate\n\n"
                "Scoring:\n"
                "- <13%: Healthy occupancy (0 points)\n"
                "- 13-16%: Elevated vacancy (3 points)\n"
                "- 16-18%: High vacancy (6 points)\n"
                "- ≥18%: Crisis vacancy (10 points)\n\n"
                "Pre-COVID normal: 10-12%\n"
                "Current (~2025): ~19.8% - structural decline"
            ),
            'url': 'https://www.cbre.com/insights/reports/us-office-figures-q4-2024'
        },
        'cre_property_value_decline_pct': {
            'label': 'Office Property Value Decline',
            'description': 'Percentage decline in office property valuations from peak',
            'category': 'CRE Structural Stress',
            'min': -50,
            'max': 20,
            'unit': '% change',
            'data_source': 'Moody\'s/RCA CPPI + Fed FSR',
            'frequency': 'Quarterly',
            'instructions': (
                "Track office property value changes:\n"
                "1. Moody's/RCA Commercial Property Price Index (CPPI)\n"
                "2. Green Street Commercial Property Price Index\n"
                "3. May be cited in Fed FSR\n"
                "4. Enter % change from peak (use negative for declines)\n\n"
                "Example: -28 means 28% decline from peak\n\n"
                "Impact on scoring:\n"
                "- Decline >25%: +2 points (severe value erosion)\n"
                "- Decline 15-25%: +1 point (significant decline)\n"
                "- Decline <15%: No adjustment\n\n"
                "Lower property values = harder refinancing = more defaults"
            )
        },
    }


def get_category_groups() -> Dict[str, list[str]]:
    """
    Group manual input fields by category for UI organization
    
    Returns:
        Dictionary mapping category names to lists of field names
    """
    return {
        'Hedge Fund Leverage': [
            'hedge_fund_leverage_percentile',
            'hedge_fund_basis_trade_concern',
            'hedge_fund_basis_trade_notional',
            'primary_dealer_slr_ratio',
        ],
        'Corporate Credit': [
            'leveraged_loan_coverage',
            'leveraged_loan_default_rate',
            'leveraged_loan_default_rate_6m_ago',
            'leveraged_loan_recovery_rate',
        ],
        'CRE Delinquency': [
            'cre_delinquency_rate',
        ],
        'CRE Refinancing Cliff': [
            'cre_maturing_loans_12m',
            'cre_maturing_loans_24m',
            'cre_refi_spread_shock',
        ],
        'CRE Structural Stress': [
            'cre_office_vacancy',
            'cre_property_value_decline_pct',
        ],
    }

