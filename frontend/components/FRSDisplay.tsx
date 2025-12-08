'use client';

import { FRSResponse } from '@/lib/api';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';

interface FRSDisplayProps {
  data: FRSResponse;
}

const categoryColors = ['#3b82f6', '#8b5cf6', '#ef4444', '#f59e0b', '#10b981'];

export default function FRSDisplay({ data }: FRSDisplayProps) {
  const chartData = [
    { name: 'Macro', value: data.breakdown.macro, max: 30 },
    { name: 'Valuation', value: data.breakdown.valuation, max: 25 },
    { name: 'Leverage', value: data.breakdown.leverage, max: 25 },
    { name: 'Earnings', value: data.breakdown.earnings, max: 10 },
    { name: 'Sentiment', value: data.breakdown.sentiment, max: 10 },
  ];

  const correctionProb = (data.correction_probability * 100).toFixed(1);

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <h2 className="text-2xl font-bold mb-4">Fundamental Risk Score</h2>
      
      {/* Main Score */}
      <div className="text-center mb-6">
        <div className="text-5xl font-bold text-gray-900 mb-2">
          {data.frs_score.toFixed(1)}
        </div>
        <div className="text-lg text-gray-600 mb-1">
          Correction Probability: <span className="font-semibold text-red-600">{correctionProb}%</span>
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

      {/* Category Details */}
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
    </div>
  );
}

