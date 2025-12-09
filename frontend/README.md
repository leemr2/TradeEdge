# TradeEdge Frontend

Next.js frontend for TradeEdge investment command center.

## Getting Started

### Prerequisites

- Node.js 18+ and npm/yarn/pnpm
- Backend API running at `http://localhost:8000` (see `../backend/README.md`)

### Installation

```bash
npm install
# or
yarn install
# or
pnpm install
```

### Development

Start the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

### Environment Variables

Create a `.env.local` file (optional):

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

If not set, defaults to `http://localhost:8000`.

## Project Structure

```
frontend/
├── app/                    # Next.js app router pages
│   ├── page.tsx           # Main dashboard
│   └── layout.tsx         # Root layout
├── components/             # React components
│   ├── FRSDisplay.tsx     # Main FRS score display
│   ├── CategoryCard.tsx   # Expandable category cards
│   ├── ComponentDetail.tsx # Component breakdown display
│   └── ManualInputEditor.tsx # Manual input editor
├── lib/                   # Utilities
│   └── api.ts            # API client & type definitions
└── public/               # Static assets
```

## Components

### FRSDisplay

Main component displaying the Fundamental Risk Score with:
- Overall FRS score and correction probability
- Category breakdown chart
- Expandable category cards with detailed component breakdowns
- Manual input editing section
- Data freshness indicators

### CategoryCard

Expandable card for each FRS category showing:
- Category score and progress bar
- Component-level breakdowns
- Data source information
- Update frequency and next update dates

### ComponentDetail

Displays individual component scores with:
- Score value and interpretation
- Actual data values
- Last update timestamp (color-coded by freshness)
- Data source information

### ManualInputEditor

Inline editor for manual input values:
- Edit hedge fund leverage (0-10)
- Edit CRE delinquency rate (0-20%)
- Set "as of" date
- Validation and error handling

## Features

### Detailed FRS Breakdown

The frontend displays comprehensive FRS information:
- **Category Scores**: Each of 5 categories with max points
- **Component Details**: Individual indicators within each category
- **Data Freshness**: Color-coded timestamps (green=fresh, yellow=stale, red=very stale)
- **Interpretations**: Tooltips explaining what each score means
- **Update Schedules**: When each data source will next update

### Manual Input Management

Users can update manual inputs directly from the UI:
- Click "Edit" on any manual input card
- Enter new value and "as of" date
- Save updates via API
- Changes reflected immediately

### Responsive Design

- Mobile-friendly layout
- Expandable sections for detailed views
- Color-coded zones (GREEN, YELLOW, ORANGE, RED, BLACK)

## API Integration

The frontend communicates with the backend API:

```typescript
// Fetch FRS data
const frsData = await fetchFRS();

// Update manual inputs
await updateManualInputs({
  hedge_fund_leverage: 10,
  cre_delinquency_rate: 5.0,
  as_of: '2025-12-09'
});

// Get manual inputs
const inputs = await getManualInputs();
```

See `lib/api.ts` for complete API client implementation.

## Testing

### Component Testing

```bash
# Run tests (if configured)
npm test
```

### Manual Testing Checklist

1. **FRS Display**
   - [ ] FRS score displays correctly
   - [ ] Category breakdown chart renders
   - [ ] Category cards expand/collapse
   - [ ] Component details show correctly
   - [ ] Data freshness colors are accurate

2. **Manual Inputs**
   - [ ] Manual input values display
   - [ ] Edit button opens editor
   - [ ] Validation works (min/max ranges)
   - [ ] Save updates API successfully
   - [ ] Cancel resets form
   - [ ] Error messages display on failure

3. **Data Freshness**
   - [ ] Timestamps display correctly
   - [ ] Color coding works (green/yellow/red)
   - [ ] "Days ago" calculation is accurate

4. **Responsive Design**
   - [ ] Layout works on mobile
   - [ ] Cards stack properly on small screens
   - [ ] Charts resize appropriately

## Building for Production

```bash
npm run build
npm start
```

## Learn More

- [Next.js Documentation](https://nextjs.org/docs)
- [React Documentation](https://react.dev)
- [Recharts Documentation](https://recharts.org) - Used for data visualization
