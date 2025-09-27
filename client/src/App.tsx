import React from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { GlobalContextProvider } from "./Context/GlobalContext";
import Loading from "./components/Loading";
import { useGlobalContext } from "./Context/useGlobalContext";
import { ProtectedRoute } from "./components/ProtectedLayout";
import { AIAgent } from "./candidate/AIAgent";
import MainLayout from "./components/Layout/MainLayout";
import { JobSearch } from "./candidate/JobSearch";
import { Profile } from "./candidate/Profile";
import { ApplicationStatus } from "./candidate/ApplicationStatus";
import { CandidateOverview } from "./candidate/CandidateOverview";
import { AISearch } from "./company/AISearch";
import { ApplicationTracking } from "./company/ApplicationTracking";
import CompanyInfo from "./company/CompanyInfo";
import { CompanyOverview } from "./company/CompanyOverview";
import { JobManagement } from "./company/JobManagement";
// Replace this with any of the networks listed at https://github.com/wevm/viem/blob/main/src/chains/index.ts
import { flowTestnet } from "viem/chains";
import { PrivyProvider, usePrivy } from "@privy-io/react-auth";
import { LoginForm } from "./LoginForm";

const AppContent: React.FC = () => {
  const { loading } = useGlobalContext();
  const { ready } = usePrivy();

  if (loading || !ready) {
    return <Loading message="Loading..." />;
  }

  return (
    <Routes>
      {/* Candidate routes */}
      <Route
        path="/candidate"
        element={
          <ProtectedRoute allowedType="candidate">
            <MainLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<CandidateOverview />} />
        <Route path="jobs" element={<JobSearch />} />
        <Route path="ai-agent" element={<AIAgent />} />
        <Route path="profile" element={<Profile />} />
        <Route path="applications" element={<ApplicationStatus />} />
      </Route>

      {/* Company routes */}
      <Route path="/company" element={<MainLayout />}>
        <Route path="ai-search" element={<AISearch />} />
        <Route path="applications" element={<ApplicationTracking />} />
        <Route path="profile" element={<CompanyInfo />} />
        <Route index element={<CompanyOverview />} />
        <Route path="jobs" element={<JobManagement />} />
         <Route path="/" element={<LoginForm />} />
      </Route>

      <Route path="*" element={<div>Page not found</div>} />

    </Routes>
  );
};

function App() {
  return (
    <PrivyProvider
      appId={import.meta.env.VITE_PRIVY_APP_ID!}
      clientId={import.meta.env.VITE_PRIVY_CLIENT_ID!}
      config={{
        // Create embedded wallets for users who don't have a wallet
        appearance: {
          walletChainType: "ethereum-only",
        },

        supportedChains: [flowTestnet],
        embeddedWallets: {
          ethereum: {
            createOnLogin: "users-without-wallets",
          },
          showWalletUIs: true,
        },
      }}
    >
      <BrowserRouter>
        <GlobalContextProvider>
          <AppContent />
        </GlobalContextProvider>
      </BrowserRouter>
    </PrivyProvider>
  );
}

export default App;
