import { setupWorker } from 'msw/browser'
import { handlers } from './handlers'

// This configures a Service Worker using MSW
export const worker = setupWorker(...handlers)

// Configure the worker with the correct service worker path
export const startWorker = () => {
  return worker.start({
    onUnhandledRequest: 'bypass', // Don't warn about unhandled requests
    serviceWorker: {
      url: '/mockServiceWorker.js',
    },
  })
}
