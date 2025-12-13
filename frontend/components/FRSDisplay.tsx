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

      {/* Manual Inputs Section - Link to Full Editor */}
      <div className="mb-6">
        <div className="bg-gradient-to-r from-blue-50 to-blue-100 border border-blue-200 rounded-lg p-6">
          <div className="flex items-start justify-between">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Manual Risk Inputs</h3>
              <p className="text-sm text-gray-700 mb-3">
                Leverage & Stability category requires 14 manual input fields from Fed FSR, FDIC QBP, and CRE market data.
              </p>
              <div className="flex items-center gap-4 text-xs text-gray-600">
                <div>
                  <span className="font-semibold">Categories:</span> 5
                </div>
                <div>
                  <span className="font-semibold">Fields:</span> 14
                </div>
                <div>
                  <span className="font-semibold">Status:</span> 
                  <span className="text-green-700 font-medium"> Operational</span>
                </div>
              </div>
            </div>
            <div>
              <a
                href="/admin/manual-inputs"
                className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium text-sm"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
                Manage All Inputs
              </a>
            </div>
          </div>

          {/* Quick Summary - Show sample of current values */}
          {data.manual_inputs_structured && (
            <div className="mt-4 pt-4 border-t border-blue-200">
              <div className="text-xs text-gray-600 mb-2 font-semibold">Sample Current Values:</div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                {data.manual_inputs_structured.cre_delinquency_rate && (
                  <div className="bg-white rounded p-2">
                    <div className="text-gray-600">CRE Delinquency</div>
                    <div className="text-lg font-bold text-gray-900">
                      {data.manual_inputs_structured.cre_delinquency_rate.value}%
                    </div>
                  </div>
                )}
                <div className="bg-white rounded p-2 opacity-60">
                  <div className="text-gray-600">HF Leverage</div>
                  <div className="text-sm font-semibold text-gray-700">
                    + 13 more fields
                  </div>
                </div>
                <div className="col-span-2 flex items-center justify-center text-gray-500 text-sm">
                  Click "Manage All Inputs" to view and edit all 14 fields →
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

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

