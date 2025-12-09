'use client';

import { useState } from 'react';
import { ManualInput, updateManualInputs } from '@/lib/api';
import { Edit2, Save, X } from 'lucide-react';

interface ManualInputEditorProps {
  name: string;
  label: string;
  input: ManualInput;
  min?: number;
  max?: number;
  onUpdate?: () => void;
}

export default function ManualInputEditor({
  name,
  label,
  input,
  min = 0,
  max = 10,
  onUpdate,
}: ManualInputEditorProps) {
  const [isEditing, setIsEditing] = useState(false);
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
        updatePayload.as_of = asOf;
      }
      
      await updateManualInputs(updatePayload);
      setIsEditing(false);
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
  };

  const formatDate = (dateStr: string | null | undefined) => {
    if (!dateStr) return 'Not set';
    try {
      return new Date(dateStr).toLocaleDateString();
    } catch {
      return dateStr;
    }
  };

  if (isEditing) {
    return (
      <div className="bg-white border border-gray-300 rounded p-3">
        <div className="mb-3">
          <label className="block text-sm font-semibold mb-1">{label}</label>
          <div className="flex gap-2">
            <input
              type="number"
              min={min}
              max={max}
              step="0.1"
              value={value}
              onChange={(e) => setValue(e.target.value)}
              className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm"
              disabled={isSaving}
            />
            <span className="text-sm text-gray-600 self-center">({min}-{max})</span>
          </div>
        </div>
        <div className="mb-3">
          <label className="block text-sm font-semibold mb-1">As of Date</label>
          <input
            type="date"
            value={asOf}
            onChange={(e) => setAsOf(e.target.value)}
            className="px-2 py-1 border border-gray-300 rounded text-sm"
            disabled={isSaving}
          />
        </div>
        {error && (
          <div className="mb-2 text-sm text-red-600">{error}</div>
        )}
        <div className="flex gap-2">
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="flex items-center gap-1 px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 disabled:opacity-50"
          >
            <Save className="h-3 w-3" />
            {isSaving ? 'Saving...' : 'Save'}
          </button>
          <button
            onClick={handleCancel}
            disabled={isSaving}
            className="flex items-center gap-1 px-3 py-1 bg-gray-300 text-gray-700 rounded text-sm hover:bg-gray-400 disabled:opacity-50"
          >
            <X className="h-3 w-3" />
            Cancel
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gray-50 border border-gray-200 rounded p-3">
      <div className="flex items-center justify-between mb-2">
        <div>
          <div className="font-semibold text-sm">{label}</div>
          <div className="text-lg font-bold text-gray-900">{input.value}</div>
        </div>
        <button
          onClick={() => setIsEditing(true)}
          className="p-1 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded"
          title="Edit"
        >
          <Edit2 className="h-4 w-4" />
        </button>
      </div>
      <div className="text-xs text-gray-600 space-y-1">
        <div>Last updated: {formatDate(input.as_of)}</div>
        {input.next_update && (
          <div className="text-blue-600">Next update: {input.next_update}</div>
        )}
      </div>
    </div>
  );
}

