# TradeEdge Backend

Python analytics backend for TradeEdge investment command center.

## Setup

1. Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your FRED_API_KEY
```

3. Train the Volatility Predictor model (first time only):
```bash
python -m analytics.core.volatility_predictor --mode train
```

## Running the API

```bash
cd backend
uvicorn api.main:app --reload
```

The API will be available at `http://localhost:8000`

## API Endpoints

- `GET /` - API info
- `GET /api/health` - Health check
- `GET /api/volatility` - Get VP score
- `GET /api/frs` - Get FRS score
- `GET /api/cmds` - Get CMDS score
- `GET /api/cmds?frs_weight=0.7&vp_weight=0.3` - Get CMDS with custom weights

## Testing Individual Modules

Each module can be run standalone:

```bash
# Volatility Predictor
python -m analytics.core.volatility_predictor --mode json

# FRS Calculator
python -m analytics.core.frs_calculator

# CMDS Calculator
python -m analytics.core.cmds_calculator
```

## Data Caching

All data is cached locally in `data/cache/`:
- FRED data: `data/cache/fred/`
- Yahoo Finance data: `data/cache/yfinance/`
- Trained models: `data/cache/models/`

