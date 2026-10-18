import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  CreditCard, 
  FilePlus, 
  SearchCheck, 
  FileText, 
  FlaskConical,
  ShieldCheck,
  Building2,
  ExternalLink
} from 'lucide-react';

export const Navbar: React.FC = () => {
  const navItems = [
    { to: '/', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/transactions', label: 'Transactions', icon: CreditCard },
    { to: '/new-dispute', label: 'New Dispute Wizard', icon: FilePlus },
    { to: '/test-scenarios', label: 'Test Scenarios (TC1-TC4)', icon: FlaskConical },
  ];

  return (
    <header className="bg-slate-900 border-b border-slate-800 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-gradient-to-tr from-cyan-600 to-blue-600 rounded-lg shadow-md shadow-cyan-500/20">
              <ShieldCheck className="w-6 h-6 text-white" />
            </div>
            <div>
              <span className="text-xl font-bold tracking-tight text-white flex items-center gap-1.5">
                Evident<span className="text-cyan-400">AI</span>
              </span>
              <span className="hidden sm:inline-block text-[11px] text-slate-400 font-medium tracking-wide ml-2 border-l border-slate-700 pl-2">
                Every Claim. Backed by Evidence.
              </span>
            </div>
          </div>

          <nav className="flex space-x-1 sm:space-x-2">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    `flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-all ${
                      isActive
                        ? 'bg-slate-800 text-cyan-400 border border-cyan-500/30 shadow-sm'
                        : 'text-slate-300 hover:bg-slate-800/60 hover:text-white'
                    }`
                  }
                >
                  <Icon className="w-4 h-4" />
                  <span className="hidden md:inline">{item.label}</span>
                </NavLink>
              );
            })}
          </nav>

          <div className="flex items-center space-x-2">
            <span className="hidden lg:flex items-center text-xs font-semibold px-2.5 py-1 rounded-full bg-emerald-950/80 text-emerald-400 border border-emerald-800/80">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse mr-1.5"></span>
              Mock Bank & Store Active
            </span>
          </div>
        </div>
      </div>
    </header>
  );
};
