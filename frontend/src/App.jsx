import { Navigate, Route, Routes } from 'react-router-dom';
import AppLayout from './layouts/AppLayout';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import MarketplacePage from './pages/MarketplacePage';
import AiSignalsPage from './pages/AiSignalsPage';
import InvestorDashboardPage from './pages/InvestorDashboardPage';
import PropertyOwnerPage from './pages/PropertyOwnerPage';
import AdminDashboardPage from './pages/AdminDashboardPage';
import LiquidityPage from './pages/LiquidityPage';
import PropertyDetailsPage from './pages/PropertyDetailsPage';
import PortfolioPage from './pages/PortfolioPage';
import ProtectedRoute from './routes/ProtectedRoute';

function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      <Route element={<AppLayout />}>
        <Route index element={<Navigate to="/login" replace />} />
        <Route path="/marketplace" element={<MarketplacePage />} />
        <Route path="/ai-signals" element={<AiSignalsPage />} />
        <Route path="/properties/:id" element={<PropertyDetailsPage />} />

        <Route element={<ProtectedRoute allowedRoles={["investor"]} />}>
          <Route path="/investor" element={<InvestorDashboardPage />} />
          <Route path="/portfolio" element={<PortfolioPage />} />
          <Route path="/liquidity" element={<LiquidityPage />} />
        </Route>

        <Route element={<ProtectedRoute allowedRoles={["property_owner"]} />}>
          <Route path="/owner" element={<PropertyOwnerPage />} />
        </Route>

        <Route element={<ProtectedRoute allowedRoles={["admin"]} />}>
          <Route path="/admin" element={<AdminDashboardPage />} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/marketplace" replace />} />
    </Routes>
  );
}

export default App;
