'use client';

import { useEffect, useState } from 'react';
import { getManualInputs } from '@/lib/api';

export default function TestManualInputsPage() {
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getManualInputs()
      .then((result) => {
        console.log('Received data:', result);
        setData(result);
      })
      .catch((err) => {
        console.error('Error:', err);
        setError(err.message);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="p-8">
        <div>Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8">
        <div className="bg-red-50 border border-red-200 p-4 rounded">
          <h2 className="text-red-900 font-bold mb-2">Error Loading Data</h2>
          <p className="text-red-700">{error}</p>
          <div className="mt-4 text-sm text-red-600">
            <p>Make sure the backend is running:</p>
            <pre className="bg-red-100 p-2 mt-2">cd backend{'\n'}python api/main.py</pre>
          </div>
        </div>
      </div>
    );
  }

  if (!data) {
    return <div className="p-8">No data received</div>;
  }

  const categories = data.categories || {};
  const metadata = data.metadata || {};
  const values = data.values || {};

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">Manual Inputs Diagnostic Test</h1>

      {/* Summary */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        <div className="bg-blue-50 border border-blue-200 p-4 rounded">
          <div className="text-2xl font-bold text-blue-900">
            {Object.keys(categories).length}
          </div>
          <div className="text-sm text-blue-700">Categories</div>
        </div>
        <div className="bg-green-50 border border-green-200 p-4 rounded">
          <div className="text-2xl font-bold text-green-900">
            {Object.keys(metadata).length}
          </div>
          <div className="text-sm text-green-700">Metadata Fields</div>
        </div>
        <div className="bg-purple-50 border border-purple-200 p-4 rounded">
          <div className="text-2xl font-bold text-purple-900">
            {Object.keys(values).length}
          </div>
          <div className="text-sm text-purple-700">Value Fields</div>
        </div>
      </div>

      {/* Expected vs Actual */}
      <div className="mb-8 p-4 bg-gray-50 border border-gray-200 rounded">
        <h2 className="font-bold mb-2">Status Check</h2>
        <div className="space-y-1 text-sm">
          <div>
            Categories: {Object.keys(categories).length === 5 ? '✅' : '❌'} 
            {' '}Expected 5, Got {Object.keys(categories).length}
          </div>
          <div>
            Metadata: {Object.keys(metadata).length === 14 ? '✅' : '❌'} 
            {' '}Expected 14, Got {Object.keys(metadata).length}
          </div>
          <div>
            Values: {Object.keys(values).length >= 14 ? '✅' : '❌'} 
            {' '}Expected ≥14, Got {Object.keys(values).length}
          </div>
        </div>
      </div>

      {/* Category Breakdown */}
      <div className="mb-8">
        <h2 className="text-xl font-bold mb-4">Categories Detail</h2>
        {Object.entries(categories).map(([catName, fieldNames]: [string, any]) => (
          <div key={catName} className="mb-4 border border-gray-200 rounded">
            <div className="bg-gray-100 px-4 py-2 font-semibold">
              {catName} ({fieldNames.length} fields)
            </div>
            <div className="p-4">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-2">Field Name</th>
                    <th className="text-center py-2">Has Metadata</th>
                    <th className="text-center py-2">Has Value</th>
                    <th className="text-right py-2">Current Value</th>
                  </tr>
                </thead>
                <tbody>
                  {fieldNames.map((fieldName: string) => (
                    <tr key={fieldName} className="border-b">
                      <td className="py-2 font-mono text-xs">{fieldName}</td>
                      <td className="text-center">
                        {metadata[fieldName] ? '✅' : '❌'}
                      </td>
                      <td className="text-center">
                        {values[fieldName] !== undefined ? '✅' : '❌'}
                      </td>
                      <td className="text-right font-mono text-xs">
                        {values[fieldName] !== undefined 
                          ? JSON.stringify(values[fieldName])
                          : '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ))}
      </div>

      {/* Missing Fields */}
      <div className="mb-8">
        <h2 className="text-xl font-bold mb-4">Validation</h2>
        {(() => {
          const allFieldsInCategories: string[] = [];
          Object.values(categories).forEach((fields: any) => {
            allFieldsInCategories.push(...fields);
          });
          
          const missingMetadata = allFieldsInCategories.filter(
            f => !metadata[f]
          );
          const missingValues = allFieldsInCategories.filter(
            f => values[f] === undefined
          );

          return (
            <div className="space-y-4">
              {missingMetadata.length > 0 ? (
                <div className="bg-yellow-50 border border-yellow-200 p-4 rounded">
                  <div className="font-semibold text-yellow-900">
                    ⚠️ {missingMetadata.length} fields missing metadata:
                  </div>
                  <ul className="mt-2 text-sm text-yellow-800 list-disc list-inside">
                    {missingMetadata.map(f => <li key={f}>{f}</li>)}
                  </ul>
                </div>
              ) : (
                <div className="bg-green-50 border border-green-200 p-4 rounded text-green-900">
                  ✅ All fields have metadata
                </div>
              )}

              {missingValues.length > 0 ? (
                <div className="bg-yellow-50 border border-yellow-200 p-4 rounded">
                  <div className="font-semibold text-yellow-900">
                    ⚠️ {missingValues.length} fields missing values:
                  </div>
                  <ul className="mt-2 text-sm text-yellow-800 list-disc list-inside">
                    {missingValues.map(f => <li key={f}>{f}</li>)}
                  </ul>
                </div>
              ) : (
                <div className="bg-green-50 border border-green-200 p-4 rounded text-green-900">
                  ✅ All fields have values
                </div>
              )}
            </div>
          );
        })()}
      </div>

      {/* Raw JSON */}
      <details className="mb-8">
        <summary className="cursor-pointer font-bold mb-2">
          View Raw JSON Response
        </summary>
        <pre className="bg-gray-100 p-4 rounded text-xs overflow-auto max-h-96">
          {JSON.stringify(data, null, 2)}
        </pre>
      </details>
    </div>
  );
}

