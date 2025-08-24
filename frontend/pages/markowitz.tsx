import { useState, ChangeEvent } from "react";
import axios from "axios";

interface MarkowitzResult {
  expected_return: number;
  volatility: number;
  weights: number[];
}

export default function Markowitz() {
  const [csv, setCsv] = useState(
    "0.01,0.00,0.02\n0.01,-0.01,0.01\n-0.02,0.03,0.00\n0.01,0.02,-0.01"
  );
  const [result, setResult] = useState<MarkowitzResult | null>(null);
  const [loading, setLoading] = useState(false);

  const run = async () => {
    setLoading(true);
    try {
      const rows = csv.trim().split("\n").map(r => r.split(",").map(Number));
      const { data } = await axios.post<MarkowitzResult>("http://localhost:8000/api/markowitz", { returns: rows });
      setResult(data);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid gap-6 md:grid-cols-2">
      <div className="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
        <h1 className="text-2xl font-semibold">Markowitz Optimizer</h1>
        <p className="text-slate-600 mt-1">Global minimum-variance (long-only)</p>
        <label className="block mt-4">
          <span className="text-sm font-medium text-slate-700">Returns CSV</span>
          <textarea
            value={csv}
            onChange={(e: ChangeEvent<HTMLTextAreaElement>) => setCsv(e.target.value)}
            className="mt-1 w-full h-48 rounded-md border border-slate-300 p-3 focus:outline-none focus:ring-2 focus:ring-brand-500"
          />
        </label>
        <button
          onClick={run}
          disabled={loading}
          className="mt-4 px-4 py-2 rounded-lg bg-brand-600 text-white hover:bg-brand-700 disabled:opacity-60"
        >
          {loading ? "Optimizing..." : "Optimize"}
        </button>
      </div>

      <div className="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
        <h2 className="text-xl font-semibold">Result</h2>
        {!result ? (
          <p className="text-slate-500 mt-2">Paste returns and run optimization.</p>
        ) : (
          <div className="mt-3 grid gap-3">
            <div className="flex justify-between">
              <span className="text-slate-600">Expected Return:</span>
              <span className="font-semibold">{result.expected_return.toFixed(4)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-600">Volatility:</span>
              <span className="font-semibold">{result.volatility.toFixed(4)}</span>
            </div>
            <div>
              <span className="text-slate-600 block mb-1">Weights:</span>
              <div className="grid grid-cols-3 gap-2">
                {result.weights.map((w, i) => (
                  <div key={i} className="rounded bg-slate-100 px-3 py-2 text-center">
                    {w.toFixed(3)}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}