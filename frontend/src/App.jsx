import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import useAuthStore from './store/authStore';

// Auth Pages
import LoginPage from './pages/Auth/LoginPage';
import SignupPage from './pages/Auth/SignupPage';

// Customer Pages
import CustomerHome from './pages/Customer/CustomerHome';
import MenuView from './pages/Customer/MenuView';
import OrderTracking from './pages/Customer/OrderTracking';

// Restaurant Admin Pages
import AdminDashboard from './pages/Admin/AdminDashboard';
import RestaurantManagement from './pages/Admin/RestaurantManagement';
import MenuManagement from './pages/Admin/MenuManagement';
import TableManagement from './pages/Admin/TableManagement';
import FeedbackView from './pages/Admin/FeedbackView';

// Chef Pages
import KitchenDashboard from './pages/Kitchen/KitchenDashboard';

// Master Admin Pages
import MasterAdminDashboard from './pages/MasterAdmin/MasterAdminDashboard';

// Protected Route Component
const ProtectedRoute = ({ children, allowedRoles = [] }) => {
  const { isAuthenticated, user } = useAuthStore();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles.length > 0 && !allowedRoles.includes(user?.role)) {
    return <Navigate to="/" replace />;
  }

  return children;
};

function App() {
  const { isAuthenticated, user } = useAuthStore();

  // Redirect authenticated users to appropriate dashboard
  const getDefaultRoute = () => {
    if (!isAuthenticated) return '/customer';

    switch (user?.role) {
      case 'master_admin':
        return '/master-admin';
      case 'restaurant_admin':
        return '/admin';
      case 'chef':
        return '/kitchen';
      case 'customer':
      default:
        return '/customer';
    }
  };

  return (
    <Router>
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 3000,
          style: {
            background: '#363636',
            color: '#fff',
          },
          success: {
            duration: 3000,
            iconTheme: {
              primary: '#10b981',
              secondary: '#fff',
            },
          },
          error: {
            duration: 4000,
            iconTheme: {
              primary: '#ef4444',
              secondary: '#fff',
            },
          },
        }}
      />

      <Routes>
        {/* Public Routes */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />

        {/* Customer Routes */}
        <Route path="/customer" element={<CustomerHome />} />
        <Route path="/menu/:restaurantId" element={<MenuView />} />
        <Route path="/order/:orderId" element={<OrderTracking />} />

        {/* Restaurant Admin Routes */}
        <Route
          path="/admin"
          element={
            <ProtectedRoute allowedRoles={['restaurant_admin']}>
              <AdminDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/restaurant"
          element={
            <ProtectedRoute allowedRoles={['restaurant_admin']}>
              <RestaurantManagement />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/menu"
          element={
            <ProtectedRoute allowedRoles={['restaurant_admin']}>
              <MenuManagement />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/tables"
          element={
            <ProtectedRoute allowedRoles={['restaurant_admin']}>
              <TableManagement />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/feedback"
          element={
            <ProtectedRoute allowedRoles={['restaurant_admin']}>
              <FeedbackView />
            </ProtectedRoute>
          }
        />

        {/* Kitchen Routes */}
        <Route
          path="/kitchen"
          element={
            <ProtectedRoute allowedRoles={['chef']}>
              <KitchenDashboard />
            </ProtectedRoute>
          }
        />

        {/* Master Admin Routes */}
        <Route
          path="/master-admin"
          element={
            <ProtectedRoute allowedRoles={['master_admin']}>
              <MasterAdminDashboard />
            </ProtectedRoute>
          }
        />

        {/* Default Route */}
        <Route path="/" element={<Navigate to={getDefaultRoute()} replace />} />

        {/* 404 Route */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}

export default App;
