import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { FiUsers, FiDollarSign, FiStar, FiTrendingUp } from 'react-icons/fi';
import DashboardLayout from '../../components/layout/DashboardLayout';
import { restaurantAPI, feedbackAPI } from '../../services/api';
import useAuthStore from '../../store/authStore';
import toast from 'react-hot-toast';

export default function AdminDashboard() {
  const { user } = useAuthStore();
  const [analytics, setAnalytics] = useState(null);
  const [feedback, setFeedback] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (user?.restaurant_id) {
      fetchDashboardData();
    } else {
      setLoading(false);
    }
  }, [user]);

  const fetchDashboardData = async () => {
    try {
      const [analyticsRes, feedbackRes] = await Promise.all([
        restaurantAPI.getAnalytics(user.restaurant_id),
        feedbackAPI.getSummary(user.restaurant_id, 30),
      ]);
      setAnalytics(analyticsRes.data);
      setFeedback(feedbackRes.data);
    } catch (error) {
      toast.error('Failed to load dashboard data');
      console.error('Dashboard fetch error:', error);
    } finally {
      setLoading(false);
    }
  };

  const stats = [
    {
      label: 'Total Tables',
      value: analytics?.total_tables || 0,
      icon: FiUsers,
      color: 'bg-blue-500',
    },
    {
      label: 'Total Revenue',
      value: `$${analytics?.total_revenue || 0}`,
      icon: FiDollarSign,
      color: 'bg-green-500',
    },
    {
      label: 'Average Rating',
      value: feedback?.average_rating || 0,
      icon: FiStar,
      color: 'bg-yellow-500',
    },
    {
      label: 'Total Feedback',
      value: feedback?.total_feedback || 0,
      icon: FiTrendingUp,
      color: 'bg-purple-500',
    },
  ];

  // Show message if no restaurant
  if (!loading && !user?.restaurant_id) {
    return (
      <DashboardLayout>
        <div className="p-8">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
            <p className="text-gray-600 mt-1">Welcome back, {user?.full_name || user?.username}!</p>
          </div>

          <div className="max-w-2xl mx-auto text-center py-20">
            <div className="bg-yellow-50 border-2 border-yellow-200 rounded-xl p-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">Setup Required</h2>
              <p className="text-gray-600 mb-8">
                You need to create your restaurant first before you can access the dashboard.
              </p>
              <Link to="/admin/restaurant" className="btn-primary inline-block">
                Create Your Restaurant
              </Link>
            </div>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="p-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600 mt-1">Welcome back, {user?.full_name || user?.username}!</p>
        </div>

        {loading ? (
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin h-12 w-12 border-4 border-blue-500 border-t-transparent rounded-full"></div>
          </div>
        ) : (
          <>
            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              {stats.map((stat, index) => {
                const Icon = stat.icon;
                return (
                  <div key={index} className="bg-white rounded-xl shadow-md p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-gray-600 text-sm mb-1">{stat.label}</p>
                        <p className="text-3xl font-bold text-gray-900">{stat.value}</p>
                      </div>
                      <div className={`${stat.color} w-14 h-14 rounded-full flex items-center justify-center`}>
                        <Icon className="text-white text-2xl" />
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Feedback Summary */}
            {feedback && (
              <div className="bg-white rounded-xl shadow-md p-6 mb-8">
                <h2 className="text-xl font-bold mb-6">Customer Feedback (Last 30 Days)</h2>
                <div className="grid grid-cols-5 gap-4">
                  {[5, 4, 3, 2, 1].map((rating) => (
                    <div key={rating} className="text-center">
                      <div className="text-2xl mb-2">{'⭐'.repeat(rating)}</div>
                      <p className="text-3xl font-bold text-gray-900">
                        {feedback.rating_distribution?.[rating] || 0}
                      </p>
                      <p className="text-sm text-gray-600">{rating} Star</p>
                    </div>
                  ))}
                </div>
                <div className="mt-6 pt-6 border-t">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-gray-600">5-Star Percentage</p>
                      <p className="text-2xl font-bold text-green-600">{feedback.five_star_percentage}%</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">4+ Star Percentage</p>
                      <p className="text-2xl font-bold text-blue-600">{feedback.four_plus_percentage}%</p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Quick Actions */}
            <div className="bg-white rounded-xl shadow-md p-6">
              <h2 className="text-xl font-bold mb-4">Quick Actions</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Link
                  to="/admin/menu"
                  className="block p-4 border-2 border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all"
                >
                  <p className="font-semibold text-gray-900">📋 Manage Menu</p>
                  <p className="text-sm text-gray-600 mt-1">Add, edit, or remove menu items</p>
                </Link>
                <Link
                  to="/admin/tables"
                  className="block p-4 border-2 border-gray-200 rounded-lg hover:border-green-500 hover:bg-green-50 transition-all"
                >
                  <p className="font-semibold text-gray-900">🪑 Manage Tables</p>
                  <p className="text-sm text-gray-600 mt-1">View and manage table QR codes</p>
                </Link>
                <Link
                  to="/admin/feedback"
                  className="block p-4 border-2 border-gray-200 rounded-lg hover:border-purple-500 hover:bg-purple-50 transition-all"
                >
                  <p className="font-semibold text-gray-900">💬 View Feedback</p>
                  <p className="text-sm text-gray-600 mt-1">Read customer reviews</p>
                </Link>
              </div>
            </div>

            {/* Analytics & Reports */}
            <div className="bg-white rounded-xl shadow-md p-6 mt-6">
              <h2 className="text-xl font-bold mb-4">Analytics & Reports</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Link
                  to="/admin/analytics"
                  className="block p-4 border-2 border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all"
                >
                  <p className="font-semibold text-gray-900">📊 Analytics Dashboard</p>
                  <p className="text-sm text-gray-600 mt-1">View sales trends and performance</p>
                </Link>
                <Link
                  to="/admin/predictions"
                  className="block p-4 border-2 border-gray-200 rounded-lg hover:border-indigo-500 hover:bg-indigo-50 transition-all"
                >
                  <p className="font-semibold text-gray-900">🔮 Demand Predictions</p>
                  <p className="text-sm text-gray-600 mt-1">AI-powered demand forecasting</p>
                </Link>
                <Link
                  to="/admin/customer-insights"
                  className="block p-4 border-2 border-gray-200 rounded-lg hover:border-pink-500 hover:bg-pink-50 transition-all"
                >
                  <p className="font-semibold text-gray-900">👥 Customer Insights</p>
                  <p className="text-sm text-gray-600 mt-1">Track preferences & recommendations</p>
                </Link>
              </div>
            </div>
          </>
        )}
      </div>
    </DashboardLayout>
  );
}
