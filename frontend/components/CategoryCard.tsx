'use client';

import { useState } from 'react';
import { CategoryDetail } from '@/lib/api';
import { ChevronDown, ChevronUp } from 'lucide-react';
import ComponentDetail from './ComponentDetail';

interface CategoryCardProps {
  categoryKey: string;
  category: CategoryDetail;
  color: string;
}

const categoryColors: Record<string, string> = {
  macro_cycle: 'bg-blue-50 border-blue-200',
  valuation: 'bg-purple-50 border-purple-200',
  leverage_stability: 'bg-red-50 border-red-200',
  earnings_margins: 'bg-yellow-50 border-yellow-200',
  sentiment: 'bg-orange-50 border-orange-200',
};

const categoryTitles: Record<string, string> = {
  macro_cycle: 'Macro/Cycle',
  valuation: 'Valuation',
  leverage_stability: 'Leverage & Stability',
  earnings_margins: 'Earnings & Margins',
  sentiment: 'Sentiment',
};

export default function CategoryCard({ categoryKey, category, color }: CategoryCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const bgColor = categoryColors[categoryKey] || 'bg-gray-50 border-gray-200';
  const title = categoryTitles[categoryKey] || categoryKey;
  const percentage = (category.score / category.max) * 100;

  const getScoreColor = (score: number, max: number) => {
    const pct = (score / max) * 100;
    if (pct >= 80) return 'text-red-600';
    if (pct >= 60) return 'text-orange-600';
    if (pct >= 40) return 'text-yellow-600';
    return 'text-green-600';
  };

  const getRiskLevelBadge = (riskLevel: string) => {
    const configs = {
      'LOW': { bg: 'bg-green-100', text: 'text-green-800', border: 'border-green-300' },
      'MODERATE': { bg: 'bg-yellow-100', text: 'text-yellow-800', border: 'border-yellow-300' },
      'ELEVATED': { bg: 'bg-orange-100', text: 'text-orange-800', border: 'border-orange-300' },
      'SEVERE': { bg: 'bg-red-100', text: 'text-red-800', border: 'border-red-300' },
    };
    const config = configs[riskLevel as keyof typeof configs] || configs['LOW'];
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${config.bg} ${config.text} ${config.border}`}>
        {riskLevel}
      </span>
    );
  };

  return (
    <div className={`rounded-lg border-2 p-4 ${bgColor}`}>
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between mb-2"
      >
        <div className="flex-1 text-left">
          <div className="flex items-center gap-3 mb-1 flex-wrap">
            <h3 className="text-lg font-semibold">{title}</h3>
            <span className={`text-xl font-bold ${getScoreColor(category.score, category.max)}`}>
              {category.score.toFixed(1)} / {category.max}
            </span>
            {category.risk_level && categoryKey === 'macro_cycle' && (
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-500">Risk:</span>
                {getRiskLevelBadge(category.risk_level)}
              </div>
            )}
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2 mb-1">
            <div
              className={`h-2 rounded-full ${color}`}
              style={{ width: `${Math.min(percentage, 100)}%` }}
            />
          </div>
          <p className="text-xs text-gray-600 mt-1">{category.metadata.description}</p>
          {category.metadata.next_update && (
            <p className="text-xs text-blue-600 mt-1">
              Next update: {category.metadata.next_update}
            </p>
          )}
        </div>
        {isExpanded ? (
          <ChevronUp className="h-5 w-5 text-gray-500" />
        ) : (
          <ChevronDown className="h-5 w-5 text-gray-500" />
        )}
      </button>
      
      {isExpanded && (
        <div className="mt-4 space-y-2">
          {categoryKey === 'macro_cycle' && (
            <div className="mb-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="text-xs font-semibold text-blue-900 mb-1">Enhanced Macro/Cycle Assessment</div>
              <div className="text-xs text-blue-800">
                <strong>Traditional Indicators (20 pts):</strong> Unemployment/Sahm Rule (5), Yield Curve (10), GDP (5)
              </div>
              <div className="text-xs text-blue-800 mt-1">
                <strong>Leading Labor Quality Indicators (10 pts):</strong> U-6 Underemployment (4), Labor Market Softness (3), High-Income Sector Stress (3)
              </div>
              <div className="text-xs text-blue-700 mt-2 italic">
                New indicators provide 3-9 months advance warning vs. traditional lagging indicators
              </div>
            </div>
          )}
          <div className="text-sm font-semibold mb-2">Component Breakdown:</div>
          {Object.entries(category.components).map(([key, component]) => (
            <ComponentDetail key={key} component={component} />
          ))}
          <div className="mt-3 pt-3 border-t border-gray-300">
            <div className="text-xs text-gray-600">
              <div><strong>Update Frequency:</strong> {category.metadata.update_frequency}</div>
              <div className="mt-1"><strong>Data Sources:</strong> {category.metadata.data_sources.join(', ')}</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

