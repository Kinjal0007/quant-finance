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

interface BlackScholesParams {
  S: number;
  K: number;
  T: number;
  r: number;
  sigma: number;
  option_type: string;
}

interface BlackScholesResult {
  price: number;
}

export default function BlackScholes() {
  const [params, setParams] = useState<BlackScholesParams>({
    S: 100, K: 100, T: 1, r: 0.02, sigma: 0.2, option_type: "call"
  });
  const [result, setResult] = useState<BlackScholesResult | null>(null);
  const [loading, setLoading] = useState(false);

  const onChange = (e: ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setParams({
      ...params,
      [e.target.name]:
        e.target.name === "option_type" ? e.target.value : Number(e.target.value),
    });

  const price = async () => {
    setLoading(true);
    try {
      const { data } = await axios.get<BlackScholesResult>("http://localhost:8000/api/blackscholes", { params });
      setResult(data);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid gap-6 md:grid-cols-2">
      <div className="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
        <h1 className="text-2xl font-semibold">Black–Scholes Pricer</h1>
        <div className="grid grid-cols-2 gap-4 mt-4">
          <Field label="Spot (S)" name="S" value={params.S} onChange={onChange}/>
          <Field label="Strike (K)" name="K" value={params.K} onChange={onChange}/>
          <Field label="Maturity (T, yrs)" name="T" value={params.T} onChange={onChange}/>
          <Field label="Rate (r)" name="r" value={params.r} onChange={onChange}/>
          <Field label="Vol (sigma)" name="sigma" value={params.sigma} onChange={onChange}/>
          <label className="block">
            <span className="text-sm font-medium text-slate-700">Type</span>
            <select
              name="option_type"
              value={params.option_type}
              onChange={onChange}
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand-500"
            >
              <option value="call">call</option>
              <option value="put">put</option>
            </select>
          </label>
        </div>
        <button
          onClick={price}
          disabled={loading}
          className="mt-4 px-4 py-2 rounded-lg bg-brand-600 text-white hover:bg-brand-700 disabled:opacity-60"
        >
          {loading ? "Pricing..." : "Get Price"}
        </button>
      </div>

      <div className="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
        <h2 className="text-xl font-semibold">Result</h2>
        {!result ? (
          <p className="text-slate-500 mt-2">Enter inputs and price the option.</p>
        ) : (
          <div className="mt-3">
            <div className="flex justify-between">
              <span className="text-slate-600">Option Price:</span>
              <span className="font-semibold">{result.price.toFixed(4)}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}