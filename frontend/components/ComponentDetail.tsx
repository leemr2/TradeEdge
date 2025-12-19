'use client';

import { ComponentScore } from '@/lib/api';
import { Info } from 'lucide-react';

interface ComponentDetailProps {
  component: ComponentScore;
}

export default function ComponentDetail({ component }: ComponentDetailProps) {
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

  return (
    <div className="border-l-2 border-gray-200 pl-4 py-2">
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-sm capitalize">
            {component.name.replace(/_/g, ' ')}
          </span>
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
            ? `${component.score.toFixed(1)} / 10`
            : 'N/A'}
        </span>
      </div>
      
      {component.value !== null && component.value !== undefined && (
        <div className="text-xs text-gray-600 mb-1">
          Value: {typeof component.value === 'number' ? component.value.toFixed(2) : component.value}
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

