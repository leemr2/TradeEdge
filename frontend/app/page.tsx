'use client';

import useSWR from 'swr';
import { fetchCMDS, fetchFRS, fetchVP, CMDSResponse, FRSResponse, VPResponse } from '@/lib/api';
import CMDSDisplay from '@/components/CMDSDisplay';
import FRSDisplay from '@/components/FRSDisplay';
import VPDisplay from '@/components/VPDisplay';

export default function Home() {
  const refreshInterval = 300000; // 5 minutes

  // Fetch all data with SWR for auto-refresh
  const { data: cmdsData, error: cmdsError } = useSWR<CMDSResponse>(
    'cmds',
    () => fetchCMDS(),
    { refreshInterval, revalidateOnFocus: true }
  );

  const { data: frsData, error: frsError } = useSWR<FRSResponse>(
    'frs',
    () => fetchFRS(),
    { refreshInterval, revalidateOnFocus: true }
  );

  const { data: vpData, error: vpError } = useSWR<VPResponse>(
    'vp',
    () => fetchVP(),
    { refreshInterval, revalidateOnFocus: true }
  );

  const isLoading = !cmdsData && !cmdsError && !frsData && !frsError && !vpData && !vpError;

  return (
    <main className="min-h-screen bg-gray-50 p-4 md:p-8">
      <div className="max-w-7xl mx-auto">
        <header className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">TradeEdge</h1>
          <p className="text-gray-600">AI-Powered Investment Command Center</p>
        </header>

        {isLoading && (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
            <p className="mt-4 text-gray-600">Loading market data...</p>
          </div>
        )}

        {cmdsError || frsError || vpError ? (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <h3 className="text-red-800 font-semibold mb-2">Error Loading Data</h3>
            <p className="text-red-600 text-sm">
              {cmdsError?.message || frsError?.message || vpError?.message}
            </p>
            <p className="text-red-600 text-sm mt-2">
              Make sure the backend API is running at http://localhost:8000
            </p>
          </div>
        ) : null}

        {cmdsData && (
          <div className="mb-6">
            <CMDSDisplay data={cmdsData} />
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {frsData && (
            <div>
              <FRSDisplay data={frsData} />
            </div>
          )}

          {vpData && (
            <div>
              <VPDisplay data={vpData} />
            </div>
          )}
        </div>

        {cmdsData && frsData && vpData && (
          <div className="mt-6 text-center text-sm text-gray-500">
            Data auto-refreshes every 5 minutes • Last update: {new Date().toLocaleString()}
          </div>
        )}
      </div>
    </main>
  );
}
