# Windows Setup Guide for TradeEdge

## Setting Environment Variables in PowerShell

### Method 1: Current PowerShell Session Only (Temporary)

```powershell
$env:FRED_API_KEY="your_fred_api_key_here"
```

This sets the variable only for the current PowerShell window. Close the window and you'll need to set it again.

### Method 2: User-Level (Permanent)

```powershell
[System.Environment]::SetEnvironmentVariable('FRED_API_KEY', 'your_fred_api_key_here', 'User')
```

After running this, **restart your PowerShell terminal** for the change to take effect.

### Method 3: .env File (Recommended - Easiest)

1. Create a file named `.env` in the `backend/` directory
2. Add this line:
   ```
   FRED_API_KEY=your_fred_api_key_here
   ```
3. The application will automatically load it (python-dotenv is already installed)

**Example:**
```powershell
cd backend
New-Item -ItemType File -Name ".env" -Value "FRED_API_KEY=your_fred_api_key_here"
```

Or manually create the file with your text editor.

## Verifying Environment Variable

To check if your environment variable is set:

```powershell
# Check current session variable
$env:FRED_API_KEY

# Check system variable (after restart)
[System.Environment]::GetEnvironmentVariable('FRED_API_KEY', 'User')
```

## Quick Start Commands (PowerShell)

```powershell
# 1. Set FRED API key (choose one method above)

# 2. Install dependencies
cd backend
pip install -r requirements.txt

# 3. Train VP model (first time only)
python -m analytics.core.volatility_predictor --mode train

# 4. Start backend
uvicorn api.main:app --reload

# 5. In another terminal, start frontend
cd frontend
npm install
npm run dev
```

## Troubleshooting

**If you get "FRED_API_KEY not set" errors:**
- Make sure you've set the variable using one of the methods above
- If using Method 2, restart your PowerShell terminal
- If using .env file, make sure it's in the `backend/` directory
- Verify the variable is set: `$env:FRED_API_KEY`

