'use client';

import { useState } from 'react';
import { FRSResponse, fetchFRS } from '@/lib/api';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import CategoryCard from './CategoryCard';
import ManualInputEditor from './ManualInputEditor';

interface FRSDisplayProps {
  data: FRSResponse;
}

const categoryColors = ['#3b82f6', '#8b5cf6', '#ef4444', '#f59e0b', '#10b981'];
const categoryColorMap: Record<string, string> = {
  macro_cycle: '#3b82f6',
  valuation: '#8b5cf6',
  leverage_stability: '#ef4444',
  earnings_margins: '#f59e0b',
  sentiment: '#10b981',
};

export default function FRSDisplay({ data }: FRSDisplayProps) {
  const [refreshKey, setRefreshKey] = useState(0);
  
  const chartData = [
    { name: 'Macro', value: data.breakdown.macro, max: 30 },
    { name: 'Valuation', value: data.breakdown.valuation, max: 25 },
    { name: 'Leverage', value: data.breakdown.leverage, max: 25 },
    { name: 'Earnings', value: data.breakdown.earnings, max: 10 },
    { name: 'Sentiment', value: data.breakdown.sentiment, max: 10 },
  ];

  const correctionProb = (data.correction_probability * 100).toFixed(1);
  
  const getZoneColor = (zone: string) => {
    switch (zone) {
      case 'GREEN': return 'text-green-600';
      case 'YELLOW': return 'text-yellow-600';
      case 'ORANGE': return 'text-orange-600';
      case 'RED': return 'text-red-600';
      case 'BLACK': return 'text-black font-extrabold';
      default: return 'text-gray-600';
    }
  };

  const handleManualInputUpdate = () => {
    // Trigger a refresh by updating key
    setRefreshKey(prev => prev + 1);
    // Optionally refetch data
    window.location.reload();
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <h2 className="text-2xl font-bold mb-4">Fundamental Risk Score</h2>
      
      {/* Main Score */}
      <div className="text-center mb-6">
        <div className={`text-5xl font-bold mb-2 ${getZoneColor(data.zone)}`}>
          {data.frs_score.toFixed(1)}
        </div>
        <div className="text-lg text-gray-600 mb-1">
          Correction Probability: <span className="font-semibold text-red-600">{correctionProb}%</span>
        </div>
        <div className="text-sm text-gray-500 mb-2">
          Zone: <span className={`font-semibold ${getZoneColor(data.zone)}`}>{data.zone}</span>
        </div>
        <div className="text-sm text-gray-500">
          Last updated: {new Date(data.last_updated).toLocaleString()}
        </div>
      </div>

      {/* Category Breakdown Chart */}
      <div className="mb-6">
        <h3 className="text-lg font-semibold mb-3">Category Breakdown</h3>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={chartData}>
            <XAxis dataKey="name" />
            <YAxis domain={[0, 30]} />
            <Tooltip />
            <Bar dataKey="value" fill="#3b82f6">
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={categoryColors[index]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Detailed Category Cards */}
      {data.categories && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold mb-3">Category Details</h3>
          <div className="space-y-4">
            {Object.entries(data.categories).map(([key, category]) => (
              <CategoryCard
                key={key}
                categoryKey={key}
                category={category}
                color={categoryColorMap[key] || '#3b82f6'}
              />
            ))}
          </div>
        </div>
      )}

      {/* Manual Inputs Section */}
      {data.manual_inputs_structured && Object.keys(data.manual_inputs_structured).length > 0 && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold mb-3">Manual Inputs</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {data.manual_inputs_structured.hedge_fund_leverage && (
              <ManualInputEditor
                name="hedge_fund_leverage"
                label="Hedge Fund Leverage"
                input={data.manual_inputs_structured.hedge_fund_leverage}
                min={0}
                max={10}
                onUpdate={handleManualInputUpdate}
              />
            )}
            {data.manual_inputs_structured.cre_delinquency_rate && (
              <ManualInputEditor
                name="cre_delinquency_rate"
                label="CRE Delinquency Rate (%)"
                input={data.manual_inputs_structured.cre_delinquency_rate}
                min={0}
                max={20}
                onUpdate={handleManualInputUpdate}
              />
            )}
          </div>
        </div>
      )}

      {/* Fallback: Simple Category Grid (if detailed structure not available) */}
      {!data.categories && (
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-blue-50 rounded p-3">
            <div className="text-sm text-gray-600">Macro/Cycle</div>
            <div className="text-xl font-bold">{data.breakdown.macro.toFixed(1)} / 30</div>
          </div>
          <div className="bg-purple-50 rounded p-3">
            <div className="text-sm text-gray-600">Valuation</div>
            <div className="text-xl font-bold">{data.breakdown.valuation.toFixed(1)} / 25</div>
          </div>
          <div className="bg-red-50 rounded p-3">
            <div className="text-sm text-gray-600">Leverage & Stability</div>
            <div className="text-xl font-bold">{data.breakdown.leverage.toFixed(1)} / 25</div>
          </div>
          <div className="bg-yellow-50 rounded p-3">
            <div className="text-sm text-gray-600">Earnings</div>
            <div className="text-xl font-bold">{data.breakdown.earnings.toFixed(1)} / 10</div>
          </div>
          <div className={`rounded p-3 ${data.breakdown.sentiment >= 0 ? 'bg-orange-50' : 'bg-green-50'}`}>
            <div className="text-sm text-gray-600">Sentiment</div>
            <div className="text-xl font-bold">
              {data.breakdown.sentiment >= 0 ? '+' : ''}{data.breakdown.sentiment.toFixed(1)} / ±10
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

