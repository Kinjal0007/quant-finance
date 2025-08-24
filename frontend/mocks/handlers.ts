import { http, HttpResponse, delay } from 'msw'

// Mock data for jobs
const mockJobs = [
  {
    id: 'demo-job-1',
    type: 'montecarlo',
    status: 'completed',
    symbols: ['AAPL', 'MSFT'],
    start_ts: '2024-01-01T00:00:00Z',
    end_ts: '2024-12-31T00:00:00Z',
    interval: '1d',
    vendor: 'eodhd',
    adjusted: true,
    created_at: '2024-01-15T10:00:00Z',
    finished_at: '2024-01-15T10:02:00Z',
    result_refs: {
      metrics: {
        num_simulations: 1000,
        time_steps: 252,
        mean_return: 0.0856,
        std_return: 0.2341,
        percentiles: {
          p5: -0.3124,
          p25: -0.0891,
          p50: 0.0456,
          p75: 0.1987,
          p95: 0.4567
        }
      }
    }
  },
  {
    id: 'demo-job-2',
    type: 'markowitz',
    status: 'completed',
    symbols: ['AAPL', 'MSFT', 'GOOGL'],
    start_ts: '2024-01-01T00:00:00Z',
    end_ts: '2024-12-31T00:00:00Z',
    interval: '1d',
    vendor: 'eodhd',
    adjusted: true,
    created_at: '2024-01-15T09:00:00Z',
    finished_at: '2024-01-15T09:01:00Z',
    result_refs: {
      metrics: {
        expected_return: 0.1245,
        volatility: 0.1876,
        sharpe_ratio: 0.6634,
        weights: {
          AAPL: 0.35,
          MSFT: 0.45,
          GOOGL: 0.20
        }
      }
    }
  }
]

// Mock data for symbols
const mockSymbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX']

export const handlers = [
  // GET /api/v1/jobs/ - List jobs
  http.get('/api/v1/jobs/', async () => {
    await delay(500) // Simulate network delay
    
    return HttpResponse.json({
      jobs: mockJobs,
      total: mockJobs.length,
      page: 1,
      size: 50,
      has_next: false
    })
  }),

  // POST /api/v1/jobs/ - Create job
  http.post('/api/v1/jobs/', async ({ request }) => {
    await delay(1000) // Simulate processing time
    
    const body = await request.json() as any
    const { type, symbols, start, end, interval, vendor, adjusted, params } = body
    
    // Create a new mock job
    const newJob: any = {
      id: `demo-job-${Date.now()}`,
      type,
      status: 'queued',
      symbols,
      start_ts: start,
      end_ts: end,
      interval,
      vendor,
      adjusted,
      created_at: new Date().toISOString(),
      params_json: params,
      result_refs: {},
      finished_at: undefined
    }
    
    // Add to mock jobs list
    mockJobs.unshift(newJob)
    
    // Simulate job progression: queued -> running -> completed
    setTimeout(async () => {
      newJob.status = 'running'
      await delay(500)
      newJob.status = 'completed'
      newJob.finished_at = new Date().toISOString()
      
      // Generate mock results based on job type
      if (type === 'montecarlo') {
        newJob.result_refs = {
          metrics: {
            num_simulations: params.simulations || 1000,
            time_steps: params.time_steps || 252,
            mean_return: 0.0856 + Math.random() * 0.1,
            std_return: 0.2341 + Math.random() * 0.05,
            percentiles: {
              p5: -0.3124 + Math.random() * 0.1,
              p25: -0.0891 + Math.random() * 0.1,
              p50: 0.0456 + Math.random() * 0.1,
              p75: 0.1987 + Math.random() * 0.1,
              p95: 0.4567 + Math.random() * 0.1
            }
          }
        }
      } else if (type === 'markowitz') {
        newJob.result_refs = {
          metrics: {
            expected_return: 0.1245 + Math.random() * 0.1,
            volatility: 0.1876 + Math.random() * 0.05,
            sharpe_ratio: 0.6634 + Math.random() * 0.1,
            weights: symbols.reduce((acc: any, symbol: any, index: any) => {
              acc[symbol] = (1 / symbols.length) + (Math.random() - 0.5) * 0.2
              return acc
            }, {})
          }
        }
      } else if (type === 'blackscholes') {
        newJob.result_refs = {
          metrics: {
            option_price: 15.67 + Math.random() * 5,
            delta: 0.6 + Math.random() * 0.2,
            greeks: {
              gamma: 0.02 + Math.random() * 0.01,
              theta: -2.34 + Math.random() * 1,
              vega: 45.67 + Math.random() * 10,
              rho: 12.34 + Math.random() * 5
            }
          }
        }
      }
    }, 1500)
    
    return HttpResponse.json({
      job_id: newJob.id,
      status: 'queued',
      message: 'Job queued successfully',
      estimated_duration: 30
    })
  }),

  // GET /api/v1/jobs/:id - Get job details
  http.get('/api/v1/jobs/:id', async ({ params }) => {
    await delay(300)
    
    const { id } = params
    const job = mockJobs.find(j => j.id === id)
    
    if (!job) {
      return new HttpResponse(null, { status: 404 })
    }
    
    return HttpResponse.json(job)
  }),

  // DELETE /api/v1/jobs/:id - Cancel job
  http.delete('/api/v1/jobs/:id', async ({ params }) => {
    await delay(200)
    
    const { id } = params
    const jobIndex = mockJobs.findIndex(j => j.id === id)
    
    if (jobIndex === -1) {
      return new HttpResponse(null, { status: 404 })
    }
    
    mockJobs[jobIndex].status = 'cancelled'
    
    return HttpResponse.json({ message: 'Job cancelled successfully' })
  }),

  // GET /api/v1/symbols - Get available symbols
  http.get('/api/v1/symbols', async () => {
    await delay(200)
    
    return HttpResponse.json({
      symbols: mockSymbols,
      total: mockSymbols.length
    })
  }),

  // Health check
  http.get('/health', async () => {
    return HttpResponse.json({
      status: 'ok',
      timestamp: new Date().toISOString(),
      version: '1.0.0',
      database: 'connected',
      pubsub: 'connected'
    })
  })
]
