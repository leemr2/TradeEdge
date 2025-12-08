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
  manual_inputs: Record<string, any>;
  component_details: Record<string, number>;
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

