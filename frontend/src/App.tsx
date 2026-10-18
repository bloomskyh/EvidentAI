import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Navbar } from './components/Navbar';
import { DashboardPage } from './pages/DashboardPage';
import { TransactionsPage } from './pages/TransactionsPage';
import { NewDisputeWizard } from './pages/NewDisputeWizard';
import { InvestigationWorkspace } from './pages/InvestigationWorkspace';
import { EvidencePacketPage } from './pages/EvidencePacketPage';
import { ApprovalVerificationPage } from './pages/ApprovalVerificationPage';
import { TestScenariosPage } from './pages/TestScenariosPage';

export function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-[#0A0F1D] text-slate-100 flex flex-col font-sans selection:bg-cyan-500/30 selection:text-cyan-200">
        <Navbar />
        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 pt-8">
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/transactions" element={<TransactionsPage />} />
            <Route path="/new-dispute" element={<NewDisputeWizard />} />
            <Route path="/disputes/:disputeId" element={<InvestigationWorkspace />} />
            <Route path="/disputes/:disputeId/packet" element={<EvidencePacketPage />} />
            <Route path="/disputes/:disputeId/verification" element={<ApprovalVerificationPage />} />
            <Route path="/test-scenarios" element={<TestScenariosPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
        <footer className="border-t border-slate-800/80 py-6 text-center text-xs text-slate-500">
          EvidentAI — Agentic AI Hackathon 2026 by Ziro.Digital • Every Claim. Backed by Evidence.
        </footer>
      </div>
    </BrowserRouter>
  );
}

export default App;
