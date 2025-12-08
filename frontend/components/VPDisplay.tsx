'use client';

import { VPResponse } from '@/lib/api';

interface VPDisplayProps {
  data: VPResponse;
}

export default function VPDisplay({ data }: VPDisplayProps) {
  const spikeProb = (data.spike_probability * 100).toFixed(1);

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <h2 className="text-2xl font-bold mb-4">Volatility Predictor</h2>
      
      {/* Main Score */}
      <div className="text-center mb-6">
        <div className="text-5xl font-bold text-blue-600 mb-2">
          {data.vp_score}
        </div>
        <div className="text-lg text-gray-600 mb-1">
          2-5 Day Spike Probability: <span className="font-semibold text-red-600">{spikeProb}%</span>
        </div>
        <div className="text-sm text-gray-500">
          Last updated: {new Date(data.last_updated).toLocaleString()}
        </div>
      </div>

      {/* Signal Strength */}
      <div className="mb-6">
        <div className="flex justify-between mb-2">
          <span className="text-sm text-gray-600">Signal Strength</span>
          <span className="text-sm font-semibold">{data.signal_strength}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-3">
          <div
            className="bg-blue-600 h-3 rounded-full transition-all"
            style={{ width: `${data.signal_strength}%` }}
          />
        </div>
      </div>

      {/* Confidence */}
      <div className="mb-6">
        <div className="flex justify-between mb-2">
          <span className="text-sm text-gray-600">Confidence</span>
          <span className="text-sm font-semibold">{data.confidence}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-3">
          <div
            className="bg-green-600 h-3 rounded-full transition-all"
            style={{ width: `${data.confidence}%` }}
          />
        </div>
      </div>

      {/* Component Breakdown */}
      <div className="grid grid-cols-3 gap-3">
        {data.components.fear_composite !== undefined && (
          <div className="bg-red-50 rounded p-3">
            <div className="text-xs text-gray-600">Fear Composite</div>
            <div className="text-lg font-bold">{data.components.fear_composite}</div>
          </div>
        )}
        {data.components.search_volatility !== undefined && (
          <div className="bg-orange-50 rounded p-3">
            <div className="text-xs text-gray-600">Search Volatility</div>
            <div className="text-lg font-bold">{data.components.search_volatility}</div>
          </div>
        )}
        {data.components.cross_asset_stress !== undefined && (
          <div className="bg-yellow-50 rounded p-3">
            <div className="text-xs text-gray-600">Cross-Asset Stress</div>
            <div className="text-lg font-bold">{data.components.cross_asset_stress}</div>
          </div>
        )}
      </div>

      {/* Prediction Window */}
      <div className="mt-4 text-center text-sm text-gray-500">
        Prediction Window: {data.prediction_window_days} days
      </div>
    </div>
  );
}

