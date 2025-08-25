import Link from "next/link";
import { useRouter } from "next/router";
import { ReactNode } from "react";

interface NavLinkProps {
  href: string;
  children: ReactNode;
}

const NavLink = ({ href, children }: NavLinkProps) => {
  const { pathname } = useRouter();
  const active = pathname === href;
  return (
    <Link
      href={href}
      className={`px-3 py-2 rounded-md text-sm font-medium transition ${
        active
          ? "bg-brand-600 text-white"
          : "text-slate-700 hover:bg-slate-100"
      }`}
    >
      {children}
    </Link>
  );
};

export default function Navbar() {
  return (
    <nav className="sticky top-0 z-30 backdrop-blur bg-white/80 border-b">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8 h-14 flex items-center justify-between">
        <Link href="/" className="font-semibold text-brand-700">
          Quant Finance
        </Link>
        <div className="flex items-center gap-2">
          <NavLink href="/montecarlo">Monte Carlo</NavLink>
          <NavLink href="/markowitz">Markowitz</NavLink>
          <NavLink href="/blackscholes">Black–Scholes</NavLink>
          <NavLink href="/jobs">Jobs</NavLink>
          <NavLink href="/test-msw">Test MSW</NavLink>
        </div>
      </div>
    </nav>
  );
}