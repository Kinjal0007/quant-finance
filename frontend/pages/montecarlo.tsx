import { useState, ChangeEvent } from "react";
import axios from "axios";

interface FieldProps {
  label: string;
  name: string;
  value: number;
  onChange: (e: ChangeEvent<HTMLInputElement>) => void;
  step?: string;
}

const Field = ({ label, name, value, onChange, step="any" }: FieldProps) => (
  <label className="block">
    <span className="text-sm font-medium text-slate-700">{label}</span>
    <input
      name={name}
      type="number"
      step={step}
      value={value}
      onChange={onChange}
      className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand-500"
    />
  </label>
);

interface MonteCarloParams {
  S0: number;
  mu: number;
  sigma: number;
  T: number;
  steps: number;
  sims: number;
}

interface MonteCarloResult {
  final_mean: number;
  final_std: number;
  p5: number;
  p50: number;
  p95: number;
}

export default function MonteCarlo() {
  const [params, setParams] = useState<MonteCarloParams>({
    S0: 100, mu: 0.08, sigma: 0.2, T: 1.0, steps: 252, sims: 1000
  });
  const [result, setResult] = useState<MonteCarloResult | null>(null);
  const [loading, setLoading] = useState(false);

  const onChange = (e: ChangeEvent<HTMLInputElement>) => setParams({ ...params, [e.target.name]: Number(e.target.value) });

  const run = async () => {
    setLoading(true);
    try {
      const { data } = await axios.get<MonteCarloResult>("http://localhost:8000/api/montecarlo", { params });
      setResult(data);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid gap-6 md:grid-cols-2">
      <div className="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
        <h1 className="text-2xl font-semibold">Monte Carlo Simulator</h1>
        <p className="text-slate-600 mt-1">Geometric Brownian Motion</p>
        <div className="grid grid-cols-2 gap-4 mt-4">
          <Field label="S0" name="S0" value={params.S0} onChange={onChange} />
          <Field label="mu" name="mu" value={params.mu} onChange={onChange} />
          <Field label="sigma" name="sigma" value={params.sigma} onChange={onChange} />
          <Field label="T (years)" name="T" value={params.T} onChange={onChange} />
          <Field label="steps" name="steps" value={params.steps} onChange={onChange} step="1"/>
          <Field label="sims" name="sims" value={params.sims} onChange={onChange} step="1"/>
        </div>
        <button
          onClick={run}
          disabled={loading}
          className="mt-4 px-4 py-2 rounded-lg bg-brand-600 text-white hover:bg-brand-700 disabled:opacity-60"
        >
          {loading ? "Running..." : "Run Simulation"}
        </button>
      </div>

      <div className="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
        <h2 className="text-xl font-semibold">Summary</h2>
        {!result ? (
          <p className="text-slate-500 mt-2">Run a simulation to see results.</p>
        ) : (
          <div className="grid gap-3 mt-3">
            <div className="flex justify-between">
              <span className="text-slate-600">Mean (final):</span>
              <span className="font-semibold">{result.final_mean.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-600">Std (final):</span>
              <span className="font-semibold">{result.final_std.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-600">P5:</span>
              <span className="font-semibold">{result.p5.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-600">Median:</span>
              <span className="font-semibold">{result.p50.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-600">P95:</span>
              <span className="font-semibold">{result.p95.toFixed(2)}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}