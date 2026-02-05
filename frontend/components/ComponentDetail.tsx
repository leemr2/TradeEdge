'use client';

import { ComponentScore } from '@/lib/api';
import { Info } from 'lucide-react';

interface ComponentDetailProps {
  component: ComponentScore;
}

export default function ComponentDetail({ component }: ComponentDetailProps) {
  // Component max point mapping for enhanced macro/cycle indicators
  const getComponentMaxPoints = (componentName: string): number => {
    const maxPoints: Record<string, number> = {
      // Macro/Cycle - Enhanced (30 total)
      'unemployment': 5,           // Reduced from 10
      'yield_curve': 10,            // Unchanged
      'gdp': 5,                     // Reduced from 10
      'u6_underemployment': 4,      // NEW
      'labor_market_softness': 3,   // NEW
      'high_income_stress': 3,      // NEW
      // Other categories default to 10
    };
    return maxPoints[componentName] || 10;
  };

  const formatDate = (dateStr: string | null | undefined) => {
    if (!dateStr) return 'Unknown';
    try {
      const date = new Date(dateStr);
      const now = new Date();
      const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));

      if (diffDays === 0) return 'Today';
      if (diffDays === 1) return 'Yesterday';
      if (diffDays < 7) return `${diffDays} days ago`;
      if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
      return date.toLocaleDateString();
    } catch {
      return dateStr;
    }
  };

  const getFreshnessColor = (dateStr: string | null | undefined) => {
    if (!dateStr) return 'text-gray-500';
    try {
      const date = new Date(dateStr);
      const now = new Date();
      const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));
      
      if (diffDays <= 1) return 'text-green-600';
      if (diffDays <= 7) return 'text-yellow-600';
      return 'text-red-600';
    } catch {
      return 'text-gray-500';
    }
  };

  const maxPoints = getComponentMaxPoints(component.name);

  // Helper to get user-friendly labels for new indicators
  const getComponentLabel = (name: string): string => {
    const labels: Record<string, string> = {
      'u6_underemployment': 'U-6 Underemployment',
      'labor_market_softness': 'Labor Market Softness',
      'high_income_stress': 'High-Income Sector Stress',
    };
    return labels[name] || name.replace(/_/g, ' ');
  };

  // Check if this is a new leading indicator
  const isLeadingIndicator = (name: string): boolean => {
    return ['u6_underemployment', 'labor_market_softness', 'high_income_stress'].includes(name);
  };

  return (
    <div className="border-l-2 border-gray-200 pl-4 py-2">
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-semibold text-sm capitalize">
            {getComponentLabel(component.name)}
          </span>
          {isLeadingIndicator(component.name) && (
            <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800 border border-blue-200">
              NEW
            </span>
          )}
          {component.interpretation && (
            <div className="group relative">
              <Info className="h-3 w-3 text-gray-400 cursor-help" />
              <div className="absolute left-0 bottom-full mb-2 hidden group-hover:block z-10 w-64 p-2 bg-gray-900 text-white text-xs rounded shadow-lg">
                {component.interpretation}
              </div>
            </div>
          )}
        </div>
        <span className="text-sm font-bold">
          {component.score !== null && component.score !== undefined
            ? `${component.score.toFixed(1)} / ${maxPoints}`
            : 'N/A'}
        </span>
      </div>
      
      {component.value !== null && component.value !== undefined && (
        <div className="text-xs text-gray-600 mb-1">
          Value: {typeof component.value === 'number' 
            ? component.value.toFixed(2) 
            : typeof component.value === 'object' 
              ? Object.entries(component.value).map(([key, val]) => 
                  `${key.replace(/_/g, ' ')}: ${typeof val === 'number' ? val.toFixed(2) : val}`
                ).join(', ')
              : String(component.value)}
          {component.data_source && ` (${component.data_source})`}
        </div>
      )}
      
      <div className="flex items-center justify-between text-xs">
        <span className={getFreshnessColor(component.last_updated)}>
          Updated: {formatDate(component.last_updated)}
        </span>
        {component.is_manual && component.next_update && (
          <span className="text-blue-600">
            Next update: {component.next_update}
          </span>
        )}
      </div>
    </div>
  );
}

