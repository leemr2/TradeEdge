'use client';

import { useState } from 'react';
import { ManualInput, updateManualInputs } from '@/lib/api';
import { Edit2, Save, X, Info, ExternalLink, ChevronDown, ChevronUp, HelpCircle } from 'lucide-react';

interface FieldMetadata {
  label: string;
  description: string;
  category: string;
  min?: number;
  max?: number;
  unit?: string;
  type?: string;
  data_source: string;
  frequency: string;
  instructions: string;
  url?: string;
}

interface ManualInputEditorProps {
  name: string;
  label: string;
  input: ManualInput;
  min?: number;
  max?: number;
  metadata?: FieldMetadata;
  onUpdate?: () => void;
}

export default function ManualInputEditor({
  name,
  label,
  input,
  min = 0,
  max = 10,
  metadata,
  onUpdate,
}: ManualInputEditorProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [showInstructions, setShowInstructions] = useState(false);
  const [value, setValue] = useState(input.value.toString());
  const [asOf, setAsOf] = useState(input.as_of || new Date().toISOString().split('T')[0]);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSave = async () => {
    setError(null);
    const numValue = parseFloat(value);
    
    if (isNaN(numValue) || numValue < min || numValue > max) {
      setError(`Value must be between ${min} and ${max}`);
      return;
    }

    setIsSaving(true);
    try {
      const updatePayload: Record<string, any> = {};
      updatePayload[name] = numValue;
      if (asOf) {
        updatePayload[`${name}_as_of`] = asOf;
      }
      
      await updateManualInputs(updatePayload);
      setIsEditing(false);
      setShowInstructions(false);
      if (onUpdate) {
        onUpdate();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update');
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancel = () => {
    setValue(input.value.toString());
    setAsOf(input.as_of || new Date().toISOString().split('T')[0]);
    setError(null);
    setIsEditing(false);
    setShowInstructions(false);
  };

  const formatDate = (dateStr: string | null | undefined) => {
    if (!dateStr) return 'Not set';
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric' 
      });
    } catch {
      return dateStr;
    }
  };

  if (isEditing) {
    return (
      <div className="bg-white border-2 border-blue-500 rounded-lg p-4 shadow-lg">
        {/* Header */}
        <div className="mb-4">
          <h4 className="font-bold text-base text-gray-900">{label}</h4>
          {metadata?.description && (
            <p className="text-sm text-gray-600 mt-1">{metadata.description}</p>
          )}
        </div>

        {/* Instructions Toggle */}
        {metadata?.instructions && (
          <div className="mb-4">
            <button
              onClick={() => setShowInstructions(!showInstructions)}
              className="flex items-center gap-2 text-sm text-blue-600 hover:text-blue-800 font-medium"
            >
              <HelpCircle className="h-4 w-4" />
              {showInstructions ? 'Hide' : 'Show'} Detailed Instructions
              {showInstructions ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </button>
            
            {showInstructions && (
              <div className="mt-3 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <div className="text-sm text-gray-800 whitespace-pre-line leading-relaxed">
                  {metadata.instructions}
                </div>
                
                {metadata.url && (
                  <a
                    href={metadata.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="mt-3 inline-flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800 font-medium"
                  >
                    <ExternalLink className="h-3 w-3" />
                    Open Data Source
                  </a>
                )}
              </div>
            )}
          </div>
        )}

        {/* Data Source Info */}
        {metadata && (
          <div className="mb-4 p-3 bg-gray-50 rounded border border-gray-200">
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div>
                <span className="font-semibold text-gray-700">Data Source:</span>
                <div className="text-gray-600 mt-0.5">{metadata.data_source}</div>
              </div>
              <div>
                <span className="font-semibold text-gray-700">Update Frequency:</span>
                <div className="text-gray-600 mt-0.5">{metadata.frequency}</div>
              </div>
            </div>
          </div>
        )}

        {/* Value Input */}
        <div className="mb-4">
          <label className="block text-sm font-semibold text-gray-700 mb-2">
            Value {metadata?.unit && <span className="text-gray-500 font-normal">({metadata.unit})</span>}
          </label>
          <div className="flex gap-3 items-center">
            <input
              type="number"
              min={min}
              max={max}
              step={metadata?.type === 'boolean' ? '1' : '0.1'}
              value={value}
              onChange={(e) => setValue(e.target.value)}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-base focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              disabled={isSaving}
              autoFocus
            />
            <span className="text-sm text-gray-500 whitespace-nowrap">
              Range: {min} - {max}
            </span>
          </div>
        </div>

        {/* Date Input */}
        <div className="mb-4">
          <label className="block text-sm font-semibold text-gray-700 mb-2">
            As of Date
          </label>
          <input
            type="date"
            value={asOf}
            onChange={(e) => setAsOf(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-base focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            disabled={isSaving}
          />
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-700 font-medium">{error}</p>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-2">
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Save className="h-4 w-4" />
            {isSaving ? 'Saving...' : 'Save Changes'}
          </button>
          <button
            onClick={handleCancel}
            disabled={isSaving}
            className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg font-medium hover:bg-gray-300 disabled:opacity-50 transition-colors"
          >
            <X className="h-4 w-4 inline mr-1" />
            Cancel
          </button>
        </div>
      </div>
    );
  }

  // Display Mode
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 hover:border-gray-300 transition-colors">
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <div className="font-semibold text-sm text-gray-700 mb-1">{label}</div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold text-gray-900">{input.value}</span>
            {metadata?.unit && (
              <span className="text-sm text-gray-500">{metadata.unit}</span>
            )}
          </div>
        </div>
        <button
          onClick={() => setIsEditing(true)}
          className="p-2 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
          title="Edit value"
        >
          <Edit2 className="h-5 w-5" />
        </button>
      </div>

      {/* Metadata */}
      <div className="space-y-2">
        {metadata?.description && (
          <p className="text-xs text-gray-600 leading-relaxed">
            {metadata.description}
          </p>
        )}
        
        <div className="flex items-center gap-4 text-xs text-gray-500">
          <div className="flex items-center gap-1">
            <Info className="h-3 w-3" />
            <span>Updated: {formatDate(input.as_of)}</span>
          </div>
          {metadata?.frequency && (
            <div>
              <span className="font-medium">Freq:</span> {metadata.frequency}
            </div>
          )}
        </div>

        {input.next_update && (
          <div className="text-xs text-blue-600 font-medium">
            📅 Next update: {input.next_update}
          </div>
        )}
      </div>
    </div>
  );
}

