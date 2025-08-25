import { useState, useEffect } from 'react';

export default function TestMSWPage() {
  const [jobs, setJobs] = useState<any>(null);
  const [symbols, setSymbols] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const testMSW = async () => {
      try {
        setLoading(true);
        
        // Test jobs endpoint
        const jobsResponse = await fetch('/api/v1/jobs/');
        const jobsData = await jobsResponse.json();
        setJobs(jobsData);
        
        // Test symbols endpoint
        const symbolsResponse = await fetch('/api/v1/symbols');
        const symbolsData = await symbolsResponse.json();
        setSymbols(symbolsData);
        
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    testMSW();
  }, []);

  if (loading) {
    return (
      <div className="text-center py-8">
        <div className="text-lg">Testing MSW integration...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8">
        <div className="text-red-600 text-lg">Error: {error}</div>
        <div className="text-sm text-gray-600 mt-2">MSW might not be working properly</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">MSW Test Results</h1>
      
      <div className="bg-green-50 border border-green-200 rounded-lg p-4">
        <h2 className="text-lg font-semibold text-green-800">✅ MSW is working!</h2>
        <p className="text-green-700">API calls are being intercepted by Mock Service Worker</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white p-4 rounded-lg border">
          <h3 className="font-semibold mb-2">Jobs API Response:</h3>
          <pre className="text-sm bg-gray-100 p-2 rounded overflow-auto">
            {JSON.stringify(jobs, null, 2)}
          </pre>
        </div>
        
        <div className="bg-white p-4 rounded-lg border">
          <h3 className="font-semibold mb-2">Symbols API Response:</h3>
          <pre className="text-sm bg-gray-100 p-2 rounded overflow-auto">
            {JSON.stringify(symbols, null, 2)}
          </pre>
        </div>
      </div>
    </div>
  );
}
