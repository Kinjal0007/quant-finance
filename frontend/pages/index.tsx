import Link from "next/link";

interface CardProps {
  title: string;
  desc: string;
  href: string;
}

const Card = ({ title, desc, href }: CardProps) => (
  <Link
    href={href}
    className="group rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200 hover:shadow-md transition block"
  >
    <h3 className="text-lg font-semibold text-slate-900 group-hover:text-brand-700">
      {title}
    </h3>
    <p className="text-slate-600 mt-2">{desc}</p>
    <span className="inline-block mt-4 text-brand-700 group-hover:translate-x-1 transition">
      Open →
    </span>
  </Link>
);

export default function Home() {
  return (
    <>
      <section className="text-center py-10">
        <h1 className="text-4xl font-bold tracking-tight text-slate-900">
          Build, Simulate, Optimize.
        </h1>
        <p className="mt-3 text-slate-600 max-w-2xl mx-auto">
          A minimal quant toolkit: Monte Carlo simulations, portfolio optimization,
          and option pricing—served through a clean web UI.
        </p>
        <div className="mt-6 flex gap-3 justify-center">
          <Link
            className="px-5 py-2.5 rounded-lg bg-brand-600 text-white hover:bg-brand-700"
            href="/montecarlo"
          >
            Try Monte Carlo
          </Link>
          <Link
            className="px-5 py-2.5 rounded-lg border border-slate-300 hover:bg-white"
            href="/markowitz"
          >
            Optimize Portfolio
          </Link>
        </div>
      </section>

      <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        <Card
          title="Monte Carlo"
          desc="Simulate GBM price paths and view risk metrics (percentiles, mean, std)."
          href="/montecarlo"
        />
        <Card
          title="Markowitz"
          desc="Compute global minimum-variance weights from your returns matrix."
          href="/markowitz"
        />
        <Card
          title="Black–Scholes"
          desc="Price European calls/puts. Explore sensitivities via parameters."
          href="/blackscholes"
        />
      </section>
    </>
  );
}