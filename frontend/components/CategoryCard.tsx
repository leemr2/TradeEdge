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

  return (
    <div className={`rounded-lg border-2 p-4 ${bgColor}`}>
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between mb-2"
      >
        <div className="flex-1 text-left">
          <div className="flex items-center gap-3 mb-1">
            <h3 className="text-lg font-semibold">{title}</h3>
            <span className={`text-xl font-bold ${getScoreColor(category.score, category.max)}`}>
              {category.score.toFixed(1)} / {category.max}
            </span>
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

