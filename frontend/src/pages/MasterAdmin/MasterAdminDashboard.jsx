import { useState, useEffect } from 'react';
import { FiUsers, FiDollarSign, FiTrendingUp } from 'react-icons/fi';
import { restaurantAPI } from '../../services/api';
import toast from 'react-hot-toast';

export default function MasterAdminDashboard() {
  const [restaurants, setRestaurants] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchRestaurants();
  }, []);

  const fetchRestaurants = async () => {
    try {
      const response = await restaurantAPI.list();
      setRestaurants(response.data);
    } catch (error) {
      toast.error('Failed to load restaurants');
    } finally {
      setLoading(false);
    }
  };

  const stats = [
    {
      label: 'Total Restaurants',
      value: restaurants.length,
      icon: FiUsers,
      color: 'bg-blue-500',
    },
    {
      label: 'Active Restaurants',
      value: restaurants.filter((r) => r.is_active).length,
      icon: FiTrendingUp,
      color: 'bg-green-500',
    },
    {
      label: 'Total Revenue',
      value: '$0',
      icon: FiDollarSign,
      color: 'bg-purple-500',
    },
  ];

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900">Master Admin Dashboard</h1>
          <p className="text-gray-600 mt-2">Manage all restaurants and system settings</p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {stats.map((stat, index) => {
            const Icon = stat.icon;
            return (
              <div key={index} className="bg-white rounded-xl shadow-md p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-gray-600 text-sm mb-1">{stat.label}</p>
                    <p className="text-4xl font-bold text-gray-900">{stat.value}</p>
                  </div>
                  <div className={`${stat.color} w-16 h-16 rounded-full flex items-center justify-center`}>
                    <Icon className="text-white text-3xl" />
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Restaurants List */}
        <div className="bg-white rounded-xl shadow-md p-6">
          <h2 className="text-2xl font-bold mb-6">All Restaurants</h2>

          {loading ? (
            <div className="flex justify-center py-12">
              <div className="animate-spin h-12 w-12 border-4 border-blue-500 border-t-transparent rounded-full"></div>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-3 px-4">Name</th>
                    <th className="text-left py-3 px-4">Cuisine</th>
                    <th className="text-left py-3 px-4">Status</th>
                    <th className="text-left py-3 px-4">Tables</th>
                    <th className="text-left py-3 px-4">Subscription</th>
                  </tr>
                </thead>
                <tbody>
                  {restaurants.map((restaurant) => (
                    <tr key={restaurant.id} className="border-b hover:bg-gray-50">
                      <td className="py-3 px-4 font-semibold">{restaurant.name}</td>
                      <td className="py-3 px-4">{restaurant.cuisine_type || '-'}</td>
                      <td className="py-3 px-4">
                        <span
                          className={`badge ${
                            restaurant.is_active ? 'badge-success' : 'badge-error'
                          }`}
                        >
                          {restaurant.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="py-3 px-4">{restaurant.max_tables}</td>
                      <td className="py-3 px-4">
                        <span className="badge badge-info">{restaurant.pricing_plan || 'Basic'}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
