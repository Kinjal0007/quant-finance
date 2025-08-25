import "../styles/globals.css";
import type { AppProps } from 'next/app'
import Navbar from "../components/Navbar";
import { useEffect } from 'react';

export default function App({ Component, pageProps }: AppProps) {
  // Initialize MSW only in the browser
  useEffect(() => {
    if (process.env.NODE_ENV === 'development' && typeof window !== 'undefined') {
      import('../mocks/browser').then(({ startWorker }) => {
        startWorker().then(() => {
          console.log('🔧 MSW worker started - API requests will be mocked')
        }).catch((error) => {
          console.error('Failed to start MSW worker:', error)
        })
      }).catch(console.error)
    }
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100">
      <Navbar />
      <main className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8 py-8">
        <Component {...pageProps} />
      </main>
      <footer className="border-t mt-12 py-6 text-center text-sm text-slate-500">
        © {new Date().getFullYear()} Quant Finance Platform
      </footer>
    </div>
  );
}
