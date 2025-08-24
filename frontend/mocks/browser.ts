import { setupWorker } from 'msw/browser'
import { handlers } from './handlers'

// This configures a Service Worker using MSW
export const worker = setupWorker(...handlers)

// Enable MSW in development only
if (process.env.NODE_ENV === 'development') {
  // Start the worker
  worker.start({
    onUnhandledRequest: 'bypass', // Don't warn about unhandled requests
  })
  
  console.log('🔧 MSW worker started - API requests will be mocked')
}
