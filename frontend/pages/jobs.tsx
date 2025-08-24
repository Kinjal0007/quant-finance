import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Head from 'next/head';
import { 
  PlusIcon, 
  ClockIcon, 
  CheckCircleIcon, 
  ExclamationTriangleIcon,
  PlayIcon,
  StopIcon,
  TrashIcon,
  EyeIcon,
  DocumentChartBarIcon
} from '@heroicons/react/24/outline';
import { getJobs, createJob as apiCreateJob, cancelJob as apiCancelJob } from '../lib/api';

interface Job {
  id: string;
  type: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  params_json: any;
  symbols: string[];
  start_ts: string;
  end_ts: string;
  interval: string;
  vendor: string;
  adjusted: boolean;
  created_at: string;
  started_at?: string;
  finished_at?: string;
  result_refs?: any;
  error?: string;
}

interface CreateJobForm {
  type: 'montecarlo' | 'markowitz' | 'blackscholes';
  symbols: string[];
  start_date: string;
  end_date: string;
  interval: '1d' | '1h' | '1min';
  vendor: 'eodhd' | 'twelvedata';
  adjusted: boolean;
  // Monte Carlo specific
  simulations?: number;
  time_steps?: number;
  // Markowitz specific
  risk_aversion?: number;
  // Black-Scholes specific
  option_type?: 'call' | 'put';
  strike_price?: number;
  time_to_expiry?: number;
}

export default function JobsPage() {
  const router = useRouter();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [createForm, setCreateForm] = useState<CreateJobForm>({
    type: 'montecarlo',
    symbols: ['AAPL'],
    start_date: new Date(Date.now() - 365 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    end_date: new Date().toISOString().split('T')[0],
    interval: '1d',
    vendor: 'eodhd',
    adjusted: true,
    simulations: 1000,
    time_steps: 252
  });
  const [submitting, setSubmitting] = useState(false);

  // Fetch jobs on component mount
  useEffect(() => {
    fetchJobs();
    // Poll for updates every 5 seconds
    const interval = setInterval(fetchJobs, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchJobs = async () => {
    try {
      const data = await getJobs();
      setJobs(data.jobs || []);
    } catch (error) {
      console.error('Failed to fetch jobs:', error);
    } finally {
      setLoading(false);
    }
  };

  const createJob = async () => {
    setSubmitting(true);
    try {
      const jobData = {
        type: createForm.type,
        symbols: createForm.symbols,
        start: createForm.start_date,
        end: createForm.end_date,
        interval: createForm.interval,
        vendor: createForm.vendor,
        adjusted: createForm.adjusted,
        params: {
          ...(createForm.type === 'montecarlo' && {
            simulations: createForm.simulations,
            time_steps: createForm.time_steps
          }),
          ...(createForm.type === 'markowitz' && {
            risk_aversion: createForm.risk_aversion || 1.0
          }),
          ...(createForm.type === 'blackscholes' && {
            option_type: createForm.option_type,
            strike_price: createForm.strike_price,
            time_to_expiry: createForm.time_to_expiry
          })
        }
      };

      const result = await apiCreateJob(jobData);
      
      // Create a placeholder job object for the UI
      const placeholderJob: Job = {
        id: result.job_id,
        type: createForm.type,
        status: 'pending',
        params_json: jobData.params,
        symbols: createForm.symbols,
        start_ts: createForm.start_date,
        end_ts: createForm.end_date,
        interval: createForm.interval,
        vendor: createForm.vendor,
        adjusted: createForm.adjusted,
        created_at: new Date().toISOString()
      };
      
      setJobs(prev => [placeholderJob, ...prev]);
      setShowCreateForm(false);
      setCreateForm({
        type: 'montecarlo',
        symbols: ['AAPL'],
        start_date: new Date(Date.now() - 365 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        end_date: new Date().toISOString().split('T')[0],
        interval: '1d',
        vendor: 'eodhd',
        adjusted: true,
        simulations: 1000,
        time_steps: 252
      });
    } catch (error) {
      console.error('Failed to create job:', error);
      alert('Failed to create job. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const cancelJob = async (jobId: string) => {
    try {
      await apiCancelJob(jobId);
      setJobs(prev => prev.map(job => 
        job.id === jobId ? { ...job, status: 'cancelled' } : job
      ));
    } catch (error) {
      console.error('Failed to cancel job:', error);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending':
        return <ClockIcon className="h-5 w-5 text-yellow-500" />;
      case 'running':
        return <PlayIcon className="h-5 w-5 text-blue-500" />;
      case 'completed':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case 'failed':
        return <ExclamationTriangleIcon className="h-5 w-5 text-red-500" />;
      case 'cancelled':
        return <StopIcon className="h-5 w-5 text-gray-500" />;
      default:
        return <ClockIcon className="h-5 w-5 text-gray-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'running':
        return 'bg-blue-100 text-blue-800';
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'cancelled':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const getJobTypeLabel = (type: string) => {
    switch (type) {
      case 'montecarlo':
        return 'Monte Carlo';
      case 'markowitz':
        return 'Markowitz';
      case 'blackscholes':
        return 'Black-Scholes';
      default:
        return type;
    }
  };

  return (
    <>
      <Head>
        <title>Job Console - Quant Finance</title>
        <meta name="description" content="Manage and monitor your quantitative finance jobs" />
      </Head>

      <div className="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100">
        {/* Navigation */}
        <nav className="sticky top-0 z-30 backdrop-blur bg-white/80 border-b">
          <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8 h-14 flex items-center justify-between">
            <a className="font-semibold text-brand-700" href="/">Quant Finance</a>
            <div className="flex items-center gap-2">
              <a className="px-3 py-2 rounded-md text-sm font-medium transition text-slate-700 hover:bg-slate-100" href="/montecarlo">Monte Carlo</a>
              <a className="px-3 py-2 rounded-md text-sm font-medium transition text-slate-700 hover:bg-slate-100" href="/markowitz">Markowitz</a>
              <a className="px-3 py-2 rounded-md text-sm font-medium transition text-slate-700 hover:bg-slate-100" href="/blackscholes">Black–Scholes</a>
              <a className="px-3 py-2 rounded-md text-sm font-medium transition text-brand-700 bg-brand-50" href="/jobs">Jobs</a>
            </div>
          </div>
        </nav>

        <main className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8 py-8">
          {/* Header */}
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-3xl font-bold tracking-tight text-slate-900">Job Console</h1>
              <p className="mt-2 text-slate-600">Monitor and manage your quantitative finance jobs</p>
            </div>
            <button
              onClick={() => setShowCreateForm(true)}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-brand-600 hover:bg-brand-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-brand-500"
            >
              <PlusIcon className="h-5 w-5 mr-2" />
              New Job
            </button>
          </div>

          {/* Create Job Modal */}
          {showCreateForm && (
            <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
              <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
                <div className="mt-3">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Create New Job</h3>
                  
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Job Type</label>
                      <select
                        value={createForm.type}
                        onChange={(e) => setCreateForm(prev => ({ ...prev, type: e.target.value as any }))}
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-brand-500 focus:ring-brand-500"
                      >
                        <option value="monte_carlo">Monte Carlo Simulation</option>
                        <option value="markowitz">Markowitz Portfolio Optimization</option>
                        <option value="black_scholes">Black-Scholes Option Pricing</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700">Symbols (comma-separated)</label>
                      <input
                        type="text"
                        value={createForm.symbols.join(', ')}
                        onChange={(e) => setCreateForm(prev => ({ ...prev, symbols: e.target.value.split(',').map(s => s.trim()).filter(Boolean) }))}
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-brand-500 focus:ring-brand-500"
                        placeholder="AAPL, MSFT, GOOGL"
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700">Start Date</label>
                        <input
                          type="date"
                          value={createForm.start_date}
                          onChange={(e) => setCreateForm(prev => ({ ...prev, start_date: e.target.value }))}
                          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-brand-500 focus:ring-brand-500"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700">End Date</label>
                        <input
                          type="date"
                          value={createForm.end_date}
                          onChange={(e) => setCreateForm(prev => ({ ...prev, end_date: e.target.value }))}
                          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-brand-500 focus:ring-brand-500"
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700">Interval</label>
                        <select
                          value={createForm.interval}
                          onChange={(e) => setCreateForm(prev => ({ ...prev, interval: e.target.value as any }))}
                          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-brand-500 focus:ring-brand-500"
                        >
                          <option value="1d">Daily</option>
                          <option value="1h">Hourly</option>
                          <option value="1m">Minute</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700">Vendor</label>
                        <select
                          value={createForm.vendor}
                          onChange={(e) => setCreateForm(prev => ({ ...prev, vendor: e.target.value as any }))}
                          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-brand-500 focus:ring-brand-500"
                        >
                          <option value="eodhd">EOD Historical Data</option>
                          <option value="twelve_data">Twelve Data</option>
                        </select>
                      </div>
                    </div>

                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        checked={createForm.adjusted}
                        onChange={(e) => setCreateForm(prev => ({ ...prev, adjusted: e.target.checked }))}
                        className="h-4 w-4 text-brand-600 focus:ring-brand-500 border-gray-300 rounded"
                      />
                      <label className="ml-2 block text-sm text-gray-900">Use adjusted prices</label>
                    </div>

                    {/* Monte Carlo specific fields */}
                    {createForm.type === 'montecarlo' && (
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700">Simulations</label>
                          <input
                            type="number"
                            value={createForm.simulations}
                            onChange={(e) => setCreateForm(prev => ({ ...prev, simulations: parseInt(e.target.value) }))}
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-brand-500 focus:ring-brand-500"
                            min="100"
                            max="10000"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700">Time Steps</label>
                          <input
                            type="number"
                            value={createForm.time_steps}
                            onChange={(e) => setCreateForm(prev => ({ ...prev, time_steps: parseInt(e.target.value) }))}
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-brand-500 focus:ring-brand-500"
                            min="50"
                            max="1000"
                          />
                        </div>
                      </div>
                    )}

                    {/* Black-Scholes specific fields */}
                    {createForm.type === 'blackscholes' && (
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700">Option Type</label>
                          <select
                            value={createForm.option_type || 'call'}
                            onChange={(e) => setCreateForm(prev => ({ ...prev, option_type: e.target.value as 'call' | 'put' }))}
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-brand-500 focus:ring-brand-500"
                          >
                            <option value="call">Call</option>
                            <option value="put">Put</option>
                          </select>
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700">Strike Price</label>
                          <input
                            type="number"
                            value={createForm.strike_price || ''}
                            onChange={(e) => setCreateForm(prev => ({ ...prev, strike_price: parseFloat(e.target.value) }))}
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-brand-500 focus:ring-brand-500"
                            step="0.01"
                            min="0"
                          />
                        </div>
                      </div>
                    )}
                  </div>

                  <div className="flex justify-end space-x-3 mt-6">
                    <button
                      onClick={() => setShowCreateForm(false)}
                      className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={createJob}
                      disabled={submitting}
                      className="px-4 py-2 text-sm font-medium text-white bg-brand-600 border border-transparent rounded-md hover:bg-brand-700 disabled:opacity-50"
                    >
                      {submitting ? 'Creating...' : 'Create Job'}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Jobs List */}
          <div className="bg-white shadow rounded-lg">
            {loading ? (
              <div className="p-8 text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-600 mx-auto"></div>
                <p className="mt-2 text-sm text-gray-500">Loading jobs...</p>
              </div>
            ) : jobs.length === 0 ? (
              <div className="p-8 text-center">
                <DocumentChartBarIcon className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">No jobs yet</h3>
                <p className="mt-1 text-sm text-gray-500">Get started by creating your first job.</p>
                <div className="mt-6">
                  <button
                    onClick={() => setShowCreateForm(true)}
                    className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-brand-600 hover:bg-brand-700"
                  >
                    <PlusIcon className="h-5 w-5 mr-2" />
                    New Job
                  </button>
                </div>
              </div>
            ) : (
              <div className="overflow-hidden">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Job</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Symbols</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {jobs.map((job) => (
                      <tr key={job.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div>
                            <div className="text-sm font-medium text-gray-900">
                              {getJobTypeLabel(job.type)}
                            </div>
                            <div className="text-sm text-gray-500">
                              {job.interval} • {job.vendor} • {job.adjusted ? 'Adjusted' : 'Raw'}
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            {getStatusIcon(job.status)}
                            <span className={`ml-2 inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(job.status)}`}>
                              {job.status}
                            </span>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900">
                            {job.symbols.join(', ')}
                          </div>
                          <div className="text-sm text-gray-500">
                            {formatDate(job.start_ts)} → {formatDate(job.end_ts)}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatDate(job.created_at)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                          <div className="flex space-x-2">
                            {job.status === 'running' && (
                              <button
                                onClick={() => cancelJob(job.id)}
                                className="text-red-600 hover:text-red-900"
                                title="Cancel job"
                              >
                                <StopIcon className="h-4 w-4" />
                              </button>
                            )}
                            {job.status === 'completed' && job.result_refs && (
                              <button
                                onClick={() => router.push(`/jobs/${job.id}/results`)}
                                className="text-brand-600 hover:text-brand-900"
                                title="View results"
                              >
                                <EyeIcon className="h-4 w-4" />
                              </button>
                            )}
                            {job.error && (
                              <button
                                onClick={() => alert(`Error: ${job.error}`)}
                                className="text-red-600 hover:text-red-900"
                                title="View error"
                              >
                                <ExclamationTriangleIcon className="h-4 w-4" />
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </main>
      </div>
    </>
  );
}
