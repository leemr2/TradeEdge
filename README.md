# TradeEdge: AI-Powered Investment Command Center

A personal investment tool that provides proactive insights, risk monitoring, and AI-augmented research to support independent investment decisions.

## Overview

TradeEdge combines:
- **Fundamental Risk Score (FRS)**: 12-18 month strategic risk assessment
- **Volatility Predictor (VP)**: 2-5 day tactical warning signals
- **Combined Market Danger Score (CMDS)**: Unified signal driving allocation decisions

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- FRED API key (get from https://fred.stlouisfed.org/docs/api/api_key.html)

### Backend Setup

1. Install Python dependencies:
```bash
cd backend
pip install -r requirements.txt
```

2. Set up environment variables:

**Option 1: PowerShell (Windows) - Current Session Only:**
```powershell
$env:FRED_API_KEY="your_fred_api_key_here"
```

**Option 2: PowerShell (Windows) - Permanent:**
```powershell
[System.Environment]::SetEnvironmentVariable('FRED_API_KEY', 'your_fred_api_key_here', 'User')
```

**Option 3: Create .env file (Recommended):**
Create a `.env` file in the `backend/` directory:
```
FRED_API_KEY=your_fred_api_key_here
```

Then install python-dotenv (already in requirements.txt) and the code will automatically load it.

3. Train the Volatility Predictor model (first time only):
```bash
python -m analytics.core.volatility_predictor --mode train
# Or use the script:
python scripts/train_vp_model.py
```

4. Start the FastAPI backend:

**Windows PowerShell:**
```powershell
cd backend
python -m uvicorn api.main:app --reload
# Or use the helper script:
.\start_server.ps1
```

**Linux/Mac:**
```bash
cd backend
uvicorn api.main:app --reload
```

Backend will be available at `http://localhost:8000`

### Frontend Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Start the development server:
```bash
npm run dev
```

Frontend will be available at `http://localhost:3000`

## Project Structure

```
tradeedge/
├── backend/
│   ├── analytics/
│   │   ├── core/
│   │   │   ├── volatility_predictor.py  # VP calculator
│   │   │   ├── frs_calculator.py        # FRS calculator
│   │   │   └── cmds_calculator.py       # CMDS calculator
│   │   └── data_fetchers/
│   │       ├── fred_client.py          # FRED API wrapper
│   │       └── yfinance_client.py      # Yahoo Finance wrapper
│   ├── api/
│   │   └── main.py                     # FastAPI application
│   ├── tests/                          # Unit tests
│   └── scripts/                        # Utility scripts
├── frontend/
│   ├── app/                            # Next.js app router
│   ├── components/                     # React components
│   └── lib/                           # Utilities
└── data/
    ├── cache/                         # Cached API data
    └── config/                        # Configuration files
```

## Testing Individual Modules

Each Python module can be run standalone:

```bash
# Volatility Predictor
python -m analytics.core.volatility_predictor --mode json

# FRS Calculator
python -m analytics.core.frs_calculator

# CMDS Calculator
python -m analytics.core.cmds_calculator

# Test all modules
python scripts/test_all_modules.py
```

## API Endpoints

- `GET /api/health` - Health check
- `GET /api/volatility` - Get VP score
- `GET /api/frs` - Get FRS score
- `GET /api/cmds` - Get CMDS score
- `GET /api/cmds?frs_weight=0.7&vp_weight=0.3` - Custom weights

## Development

### Running Tests

```bash
cd backend
pytest tests/
```

### Training VP Model

The Volatility Predictor model should be retrained weekly:

```bash
python scripts/train_vp_model.py
```

### Data Caching

All external API data is cached locally:
- FRED data: `data/cache/fred/` (7-day TTL)
- Yahoo Finance: `data/cache/yfinance/` (24-hour TTL)
- Trained models: `data/cache/models/`

## Architecture

- **Modular Python "Brains"**: Each analytics module is independent and outputs JSON
- **FastAPI Backend**: HTTP wrapper around Python modules
- **Next.js Frontend**: React dashboard with real-time data visualization
- **Local-First**: All data cached locally for privacy and speed

## License

This project is for personal/educational use.

## Disclaimer

This is a decision-support tool, not financial advice. Past performance doesn't guarantee future results. Always use proper risk management and never risk more than you can afford to lose.

