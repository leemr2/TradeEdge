'use client';

import { useState, useEffect } from 'react';
import { getManualInputs, FieldMetadata, ManualInputsResponse } from '@/lib/api';
import ManualInputEditor from './ManualInputEditor';
import { RefreshCw, AlertCircle, CheckCircle, Info } from 'lucide-react';

export default function ManualInputsManager() {
  const [data, setData] = useState<ManualInputsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await getManualInputs();
      setData(result);
      setLastRefresh(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load manual inputs');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleUpdate = () => {
    // Reload data after any update
    loadData();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <RefreshCw className="h-6 w-6 animate-spin text-blue-600" />
        <span className="ml-2 text-gray-600">Loading manual inputs...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 bg-red-50 border border-red-200 rounded-lg">
        <div className="flex items-start gap-3">
          <AlertCircle className="h-5 w-5 text-red-600 mt-0.5" />
          <div>
            <h3 className="font-semibold text-red-900">Error Loading Manual Inputs</h3>
            <p className="text-sm text-red-700 mt-1">{error}</p>
            <button
              onClick={loadData}
              className="mt-3 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!data) {
    return null;
  }

  const { values, metadata, categories, last_updated, version } = data;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white p-6 rounded-lg shadow-lg">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-2xl font-bold mb-2">Manual Input Configuration</h2>
            <p className="text-blue-100">
              Enhanced multi-factor risk scoring for Leverage & Stability category
            </p>
            {version && (
              <p className="text-xs text-blue-200 mt-2">
                Configuration Version: {version}
              </p>
            )}
          </div>
          <button
            onClick={loadData}
            className="p-2 hover:bg-blue-500 rounded-lg transition-colors"
            title="Refresh data"
          >
            <RefreshCw className="h-5 w-5" />
          </button>
        </div>
      </div>

      {/* Last Updated Info */}
      {last_updated && (
        <div className="flex items-center gap-2 text-sm text-gray-600 bg-gray-50 p-3 rounded-lg">
          <CheckCircle className="h-4 w-4 text-green-600" />
          <span>
            Last updated: {new Date(last_updated).toLocaleString()}
          </span>
          <span className="text-gray-400">•</span>
          <span>
            Last refresh: {lastRefresh.toLocaleTimeString()}
          </span>
        </div>
      )}

      {/* Important Notice */}
      <div className="bg-amber-50 border-l-4 border-amber-500 p-4 rounded-r-lg">
        <div className="flex items-start gap-3">
          <Info className="h-5 w-5 text-amber-600 mt-0.5 flex-shrink-0" />
          <div className="text-sm">
            <p className="font-semibold text-amber-900 mb-1">Data Collection Guidelines</p>
            <p className="text-amber-800">
              These inputs require manual extraction from regulatory reports. Click "Edit" on any field 
              to view detailed instructions for locating the correct data in source documents. 
              Each field includes scoring thresholds and links to official data sources.
            </p>
          </div>
        </div>
      </div>

      {/* Category Groups */}
      {Object.entries(categories).map(([categoryName, fieldNames]) => (
        <div key={categoryName} className="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
          {/* Category Header */}
          <div className="bg-gray-50 border-b border-gray-200 px-6 py-4">
            <h3 className="text-lg font-bold text-gray-900">{categoryName}</h3>
            {/* Show data source and frequency from first field's metadata */}
            {fieldNames.length > 0 && metadata[fieldNames[0]] && (
              <div className="mt-2 flex items-center gap-4 text-xs text-gray-600">
                <div>
                  <span className="font-semibold">Source:</span> {metadata[fieldNames[0]].data_source}
                </div>
                <div>
                  <span className="font-semibold">Frequency:</span> {metadata[fieldNames[0]].frequency}
                </div>
              </div>
            )}
          </div>

          {/* Fields in this category */}
          <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-4">
            {fieldNames.map((fieldName) => {
              const fieldMeta = metadata[fieldName];
              if (!fieldMeta) return null;

              // Get value and as_of date
              const value = values[fieldName] ?? fieldMeta.min ?? 0;
              const asOf = values[`${fieldName}_as_of`] ?? null;

              // Determine next_update from metadata or field-specific data
              let nextUpdate = undefined;
              if (categoryName === 'Hedge Fund Leverage' || categoryName === 'Corporate Credit') {
                nextUpdate = '2026-05-01 (Next Fed FSR)';
              } else if (categoryName === 'CRE Delinquency') {
                nextUpdate = '2026-02-15 (Next FDIC QBP)';
              } else if (categoryName.includes('CRE')) {
                nextUpdate = '2026-05-01 (Next Fed FSR)';
              }

              return (
                <ManualInputEditor
                  key={fieldName}
                  name={fieldName}
                  label={fieldMeta.label}
                  input={{
                    value: value,
                    as_of: asOf,
                    next_update: nextUpdate,
                  }}
                  min={fieldMeta.min ?? 0}
                  max={fieldMeta.max ?? 100}
                  metadata={fieldMeta}
                  onUpdate={handleUpdate}
                />
              );
            })}
          </div>
        </div>
      ))}

      {/* Footer Help */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="font-semibold text-blue-900 mb-2">Need Help?</h4>
        <ul className="text-sm text-blue-800 space-y-1 list-disc list-inside">
          <li>Click "Edit" on any field to view detailed extraction instructions</li>
          <li>All fields include scoring thresholds and interpretation guides</li>
          <li>Update frequencies are shown for each category</li>
          <li>Links to official data sources provided where available</li>
          <li>Changes take effect immediately and clear cached calculations</li>
        </ul>
      </div>
    </div>
  );
}

