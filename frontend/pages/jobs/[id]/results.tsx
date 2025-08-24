import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Head from 'next/head';
import Link from 'next/link';
import { 
  ArrowLeftIcon,
  DocumentChartBarIcon,
  ChartBarIcon,
  TableCellsIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import { getJob } from '../../../lib/api';

interface JobResult {
  id: string;
  type: string;
  status: string;
  params_json: any;
  symbols: string[];
  result_refs: {
    metrics?: any;
    charts?: any;
    data?: any;
  };
  created_at: string;
  finished_at: string;
}

export default function JobResultsPage() {
  const router = useRouter();
  const { id } = router.query;
  const [job, setJob] = useState<JobResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (id) {
      fetchJobResults();
    }
  }, [id]);

  const fetchJobResults = async () => {
    try {
      const jobData = await getJob(id as string);
      setJob(jobData);
    } catch (error) {
      setError('Failed to fetch job results');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand-600 mx-auto"></div>
          <p className="mt-4 text-lg text-gray-600">Loading job results...</p>
        </div>
      </div>
    );
  }

  if (error || !job) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100 flex items-center justify-center">
        <div className="text-center">
          <ExclamationTriangleIcon className="mx-auto h-12 w-12 text-red-500" />
          <h2 className="mt-4 text-lg font-medium text-gray-900">Error</h2>
          <p className="mt-2 text-gray-600">{error || 'Job not found'}</p>
          <Link
            href="/jobs"
            className="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-brand-600 hover:bg-brand-700"
          >
            <ArrowLeftIcon className="h-5 w-5 mr-2" />
            Back to Jobs
          </Link>
        </div>
      </div>
    );
  }

  const getJobTypeLabel = (type: string) => {
    switch (type) {
      case 'monte_carlo':
        return 'Monte Carlo Simulation';
      case 'markowitz':
        return 'Markowitz Portfolio Optimization';
      case 'black_scholes':
        return 'Black-Scholes Option Pricing';
      default:
        return type;
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const renderMonteCarloResults = () => {
    if (!job.result_refs?.metrics) return null;
    
    const metrics = job.result_refs.metrics;
    return (
      <div className="space-y-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Simulation Results</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-brand-600">{metrics.num_simulations || 'N/A'}</div>
              <div className="text-sm text-gray-500">Simulations</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{metrics.mean_return?.toFixed(4) || 'N/A'}</div>
              <div className="text-sm text-gray-500">Mean Return</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{metrics.std_return?.toFixed(4) || 'N/A'}</div>
              <div className="text-sm text-gray-500">Std Deviation</div>
            </div>
          </div>
        </div>

        {metrics.percentiles && (
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Risk Metrics</h3>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div className="text-center">
                <div className="text-lg font-semibold text-red-600">{metrics.percentiles.p5?.toFixed(4) || 'N/A'}</div>
                <div className="text-sm text-gray-500">5th Percentile</div>
              </div>
              <div className="text-center">
                <div className="text-lg font-semibold text-orange-600">{metrics.percentiles.p25?.toFixed(4) || 'N/A'}</div>
                <div className="text-sm text-gray-500">25th Percentile</div>
              </div>
              <div className="text-center">
                <div className="text-lg font-semibold text-blue-600">{metrics.percentiles.p50?.toFixed(4) || 'N/A'}</div>
                <div className="text-sm text-gray-500">Median</div>
              </div>
              <div className="text-center">
                <div className="text-lg font-semibold text-orange-600">{metrics.percentiles.p75?.toFixed(4) || 'N/A'}</div>
                <div className="text-sm text-gray-500">75th Percentile</div>
              </div>
              <div className="text-center">
                <div className="text-lg font-semibold text-red-600">{metrics.percentiles.p95?.toFixed(4) || 'N/A'}</div>
                <div className="text-sm text-gray-500">95th Percentile</div>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderMarkowitzResults = () => {
    if (!job.result_refs?.metrics) return null;
    
    const metrics = job.result_refs.metrics;
    return (
      <div className="space-y-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Portfolio Optimization Results</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{metrics.expected_return?.toFixed(4) || 'N/A'}</div>
              <div className="text-sm text-gray-500">Expected Return</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{metrics.volatility?.toFixed(4) || 'N/A'}</div>
              <div className="text-sm text-gray-500">Volatility</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">{metrics.sharpe_ratio?.toFixed(4) || 'N/A'}</div>
              <div className="text-sm text-gray-500">Sharpe Ratio</div>
            </div>
          </div>
        </div>

        {metrics.weights && (
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Optimal Weights</h3>
            <div className="space-y-3">
              {Object.entries(metrics.weights).map(([symbol, weight]) => (
                <div key={symbol} className="flex justify-between items-center">
                  <span className="font-medium text-gray-900">{symbol}</span>
                  <span className="text-lg font-semibold text-brand-600">{(Number(weight) * 100).toFixed(2)}%</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderBlackScholesResults = () => {
    if (!job.result_refs?.metrics) return null;
    
    const metrics = job.result_refs.metrics;
    return (
      <div className="space-y-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Option Pricing Results</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">${metrics.option_price?.toFixed(4) || 'N/A'}</div>
              <div className="text-sm text-gray-500">Option Price</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{metrics.delta?.toFixed(4) || 'N/A'}</div>
              <div className="text-sm text-gray-500">Delta</div>
            </div>
          </div>
        </div>

        {metrics.greeks && (
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Greeks</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-lg font-semibold text-blue-600">{metrics.greeks.gamma?.toFixed(4) || 'N/A'}</div>
                <div className="text-sm text-gray-500">Gamma</div>
              </div>
              <div className="text-center">
                <div className="text-lg font-semibold text-purple-600">{metrics.greeks.theta?.toFixed(4) || 'N/A'}</div>
                <div className="text-sm text-gray-500">Theta</div>
              </div>
              <div className="text-center">
                <div className="text-lg font-semibold text-orange-600">{metrics.greeks.vega?.toFixed(4) || 'N/A'}</div>
                <div className="text-sm text-gray-500">Vega</div>
              </div>
              <div className="text-center">
                <div className="text-lg font-semibold text-red-600">{metrics.greeks.rho?.toFixed(4) || 'N/A'}</div>
                <div className="text-sm text-gray-500">Rho</div>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderResults = () => {
    switch (job.type) {
      case 'monte_carlo':
        return renderMonteCarloResults();
      case 'markowitz':
        return renderMarkowitzResults();
      case 'black_scholes':
        return renderBlackScholesResults();
      default:
        return (
          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-gray-500">Results not available for this job type.</p>
          </div>
        );
    }
  };

  return (
    <>
      <Head>
        <title>Job Results - Quant Finance</title>
        <meta name="description" content="View job results and metrics" />
      </Head>

      <div className="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100">
        {/* Navigation */}
        <nav className="sticky top-0 z-30 backdrop-blur bg-white/80 border-b">
          <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8 h-14 flex items-center justify-between">
            <Link href="/" className="font-semibold text-brand-700">
              Quant Finance
            </Link>
            <div className="flex items-center gap-2">
              <Link href="/montecarlo" className="px-3 py-2 rounded-md text-sm font-medium transition text-slate-700 hover:bg-slate-100">
                Monte Carlo
              </Link>
              <Link href="/markowitz" className="px-3 py-2 rounded-md text-sm font-medium transition text-slate-700 hover:bg-slate-100">
                Markowitz
              </Link>
              <Link href="/blackscholes" className="px-3 py-2 rounded-md text-sm font-medium transition text-slate-700 hover:bg-slate-100">
                Black–Scholes
              </Link>
              <Link href="/jobs" className="px-3 py-2 rounded-md text-sm font-medium transition text-brand-700 bg-brand-50">
                Jobs
              </Link>
            </div>
          </div>
        </nav>

        <main className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8 py-8">
          {/* Header */}
          <div className="mb-8">
            <Link
              href="/jobs"
              className="inline-flex items-center text-sm text-brand-600 hover:text-brand-700 mb-4"
            >
              <ArrowLeftIcon className="h-4 w-4 mr-2" />
              Back to Jobs
            </Link>
            <h1 className="text-3xl font-bold tracking-tight text-slate-900">Job Results</h1>
            <p className="mt-2 text-slate-600">{getJobTypeLabel(job.type)}</p>
          </div>

          {/* Job Info */}
          <div className="bg-white rounded-lg shadow p-6 mb-8">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Job Information</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <span className="text-sm font-medium text-gray-500">Symbols:</span>
                <span className="ml-2 text-sm text-gray-900">{job.symbols.join(', ')}</span>
              </div>
              <div>
                <span className="text-sm font-medium text-gray-500">Status:</span>
                <span className="ml-2 text-sm text-gray-900 capitalize">{job.status}</span>
              </div>
              <div>
                <span className="text-sm font-medium text-gray-500">Created:</span>
                <span className="ml-2 text-sm text-gray-900">{formatDate(job.created_at)}</span>
              </div>
              <div>
                <span className="text-sm font-medium text-gray-500">Completed:</span>
                <span className="ml-2 text-sm text-gray-900">{formatDate(job.finished_at)}</span>
              </div>
            </div>
          </div>

          {/* Results */}
          {renderResults()}

          {/* Raw Data */}
          {job.result_refs?.data && (
            <div className="bg-white rounded-lg shadow p-6 mt-8">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Raw Data</h3>
              <pre className="bg-gray-50 p-4 rounded-lg overflow-x-auto text-sm">
                {JSON.stringify(job.result_refs.data, null, 2)}
              </pre>
            </div>
          )}
        </main>
      </div>
    </>
  );
}
