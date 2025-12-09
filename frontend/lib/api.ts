/**
 * API client for TradeEdge backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface VPResponse {
  vp_score: number;
  confidence: number;
  spike_probability: number;
  signal_strength: number;
  last_updated: string;
  components: {
    fear_composite?: number;
    search_volatility?: number;
    cross_asset_stress?: number;
  };
  prediction_window_days: string;
}

export interface ComponentScore {
  name: string;
  score: number;
  value?: number | null;
  last_updated?: string | null;
  interpretation?: string;
  data_source?: string;
  is_manual?: boolean;
  next_update?: string;
}

export interface CategoryMetadata {
  name: string;
  description: string;
  update_frequency: string;
  data_sources: string[];
  next_update?: string;
}

export interface CategoryDetail {
  score: number;
  max: number;
  min?: number;
  components: Record<string, ComponentScore>;
  metadata: CategoryMetadata;
}

export interface ManualInput {
  value: number;
  as_of?: string | null;
  next_update?: string;
}

export interface FRSResponse {
  frs_score: number;
  correction_probability: number;
  last_updated: string;
  breakdown: {
    macro: number;
    valuation: number;
    leverage: number;
    earnings: number;
    sentiment: number;
  };
  zone: string;
  data_sources: string[];
  manual_inputs: Record<string, any>; // Backward compatibility
  component_details: Record<string, number>; // Backward compatibility
  // New detailed structure
  categories?: {
    macro_cycle: CategoryDetail;
    valuation: CategoryDetail;
    leverage_stability: CategoryDetail;
    earnings_margins: CategoryDetail;
    sentiment: CategoryDetail;
  };
  manual_inputs_structured?: {
    hedge_fund_leverage?: ManualInput;
    cre_delinquency_rate?: ManualInput;
  };
}

export interface CMDSResponse {
  cmds: number;
  zone: string;
  last_updated: string;
  components: {
    frs: number;
    frs_contribution: number;
    vp: number;
    vp_contribution: number;
  };
  allocation: {
    equity_pct: [number, number];
    hedge_pct: [number, number];
    cash_pct: [number, number];
  };
  divergence: number;
  interpretation: string;
  weights: {
    frs_weight: number;
    vp_weight: number;
  };
}

export async function fetchVP(): Promise<VPResponse> {
  const res = await fetch(`${API_BASE_URL}/api/volatility`);
  if (!res.ok) throw new Error('Failed to fetch VP');
  return res.json();
}

export async function fetchFRS(): Promise<FRSResponse> {
  const res = await fetch(`${API_BASE_URL}/api/frs`);
  if (!res.ok) throw new Error('Failed to fetch FRS');
  return res.json();
}

export async function fetchCMDS(frsWeight = 0.65, vpWeight = 0.35): Promise<CMDSResponse> {
  const res = await fetch(`${API_BASE_URL}/api/cmds?frs_weight=${frsWeight}&vp_weight=${vpWeight}`);
  if (!res.ok) throw new Error('Failed to fetch CMDS');
  return res.json();
}

export interface ManualInputUpdate {
  hedge_fund_leverage?: number;
  cre_delinquency_rate?: number;
  as_of?: string;
}

export async function updateManualInputs(update: ManualInputUpdate): Promise<{ status: string; updated: Record<string, any>; message: string }> {
  const res = await fetch(`${API_BASE_URL}/api/frs/manual-inputs`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(update),
  });
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Failed to update manual inputs');
  }
  return res.json();
}

export async function getManualInputs(): Promise<Record<string, ManualInput>> {
  const res = await fetch(`${API_BASE_URL}/api/frs/manual-inputs`);
  if (!res.ok) throw new Error('Failed to fetch manual inputs');
  return res.json();
}

