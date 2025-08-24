import "../styles/globals.css";
import type { AppProps } from 'next/app'
import Navbar from "../components/Navbar";

// Initialize MSW in development
if (process.env.NODE_ENV === 'development') {
  import('../mocks/browser').then(({ worker }) => {
    worker.start({
      onUnhandledRequest: 'bypass',
    })
    console.log('🔧 MSW worker started - API requests will be mocked')
  }).catch(console.error)
}

export default function App({ Component, pageProps }: AppProps) {
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
