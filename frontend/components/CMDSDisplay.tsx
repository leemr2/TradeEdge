'use client';

import { CMDSResponse } from '@/lib/api';
import { useMemo } from 'react';

interface CMDSDisplayProps {
  data: CMDSResponse;
}

const zoneColors: Record<string, { bg: string; text: string; border: string }> = {
  SAFE: { bg: 'bg-green-50', text: 'text-green-800', border: 'border-green-500' },
  CAUTIOUS: { bg: 'bg-yellow-50', text: 'text-yellow-800', border: 'border-yellow-500' },
  ELEVATED: { bg: 'bg-orange-50', text: 'text-orange-800', border: 'border-orange-500' },
  HIGH: { bg: 'bg-red-50', text: 'text-red-800', border: 'border-red-500' },
  EXTREME: { bg: 'bg-gray-900', text: 'text-white', border: 'border-gray-700' },
};

export default function CMDSDisplay({ data }: CMDSDisplayProps) {
  const zoneStyle = zoneColors[data.zone] || zoneColors.CAUTIOUS;
  const percentage = Math.round(data.cmds);

  const gaugeColor = useMemo(() => {
    if (data.cmds <= 25) return 'text-green-600';
    if (data.cmds <= 45) return 'text-yellow-600';
    if (data.cmds <= 65) return 'text-orange-600';
    if (data.cmds <= 80) return 'text-red-600';
    return 'text-gray-900';
  }, [data.cmds]);

  return (
    <div className={`rounded-lg border-2 ${zoneStyle.border} ${zoneStyle.bg} p-6`}>
      <h2 className="text-2xl font-bold mb-4">Combined Market Danger Score</h2>
      
      {/* Main Score Display */}
      <div className="text-center mb-6">
        <div className={`text-6xl font-bold ${gaugeColor} mb-2`}>
          {data.cmds.toFixed(1)}
        </div>
        <div className={`text-xl font-semibold ${zoneStyle.text} mb-1`}>
          {data.zone} ZONE
        </div>
        <div className="text-sm text-gray-600">
          Last updated: {new Date(data.last_updated).toLocaleString()}
        </div>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-gray-200 rounded-full h-4 mb-6">
        <div
          className={`h-4 rounded-full transition-all ${
            data.cmds <= 25 ? 'bg-green-500' :
            data.cmds <= 45 ? 'bg-yellow-500' :
            data.cmds <= 65 ? 'bg-orange-500' :
            data.cmds <= 80 ? 'bg-red-500' :
            'bg-gray-900'
          }`}
          style={{ width: `${percentage}%` }}
        />
      </div>

      {/* Component Breakdown */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="bg-white rounded p-3">
          <div className="text-sm text-gray-600">FRS Contribution</div>
          <div className="text-xl font-bold">{data.components.frs_contribution.toFixed(1)} pts</div>
          <div className="text-xs text-gray-500">FRS: {data.components.frs.toFixed(1)}</div>
        </div>
        <div className="bg-white rounded p-3">
          <div className="text-sm text-gray-600">VP Contribution</div>
          <div className="text-xl font-bold">{data.components.vp_contribution.toFixed(1)} pts</div>
          <div className="text-xs text-gray-500">VP: {data.components.vp.toFixed(1)}</div>
        </div>
      </div>

      {/* Allocation Recommendations */}
      <div className="bg-white rounded p-4 mb-4">
        <h3 className="font-semibold mb-3">Recommended Allocation</h3>
        <div className="space-y-2">
          <div className="flex justify-between">
            <span>Equity:</span>
            <span className="font-semibold">
              {data.allocation.equity_pct[0]}% - {data.allocation.equity_pct[1]}%
            </span>
          </div>
          <div className="flex justify-between">
            <span>Hedges:</span>
            <span className="font-semibold">
              {data.allocation.hedge_pct[0]}% - {data.allocation.hedge_pct[1]}%
            </span>
          </div>
          <div className="flex justify-between">
            <span>Cash/Bonds:</span>
            <span className="font-semibold">
              {data.allocation.cash_pct[0]}% - {data.allocation.cash_pct[1]}%
            </span>
          </div>
        </div>
      </div>

      {/* Interpretation */}
      <div className="bg-white rounded p-4">
        <h3 className="font-semibold mb-2">Signal Interpretation</h3>
        <p className="text-sm text-gray-700">{data.interpretation}</p>
        {data.divergence > 40 && (
          <div className="mt-2 text-xs text-orange-600">
            ⚠️ High divergence: {data.divergence.toFixed(1)} points between FRS and VP
          </div>
        )}
      </div>
    </div>
  );
}

