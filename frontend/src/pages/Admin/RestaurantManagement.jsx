import { useState, useEffect } from 'react';
import DashboardLayout from '../../components/layout/DashboardLayout';
import { restaurantAPI } from '../../services/api';
import useAuthStore from '../../store/authStore';
import toast from 'react-hot-toast';

export default function RestaurantManagement() {
  const { user } = useAuthStore();
  const [restaurant, setRestaurant] = useState(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [formData, setFormData] = useState({});

  useEffect(() => {
    if (user?.restaurant_id) {
      fetchRestaurant();
    }
  }, [user]);

  const fetchRestaurant = async () => {
    try {
      const response = await restaurantAPI.get(user.restaurant_id);
      setRestaurant(response.data);
      setFormData(response.data);
    } catch (error) {
      toast.error('Failed to load restaurant details');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await restaurantAPI.update(user.restaurant_id, formData);
      toast.success('Restaurant updated successfully!');
      setEditing(false);
      fetchRestaurant();
    } catch (error) {
      toast.error('Failed to update restaurant');
    }
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex justify-center items-center h-screen">
          <div className="animate-spin h-12 w-12 border-4 border-blue-500 border-t-transparent rounded-full"></div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="p-8">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Restaurant Management</h1>
          {!editing && (
            <button onClick={() => setEditing(true)} className="btn-primary">
              Edit Details
            </button>
          )}
        </div>

        <div className="bg-white rounded-xl shadow-md p-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Restaurant Name</label>
                <input
                  type="text"
                  className="input-field"
                  value={formData.name || ''}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  disabled={!editing}
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Cuisine Type</label>
                <input
                  type="text"
                  className="input-field"
                  value={formData.cuisine_type || ''}
                  onChange={(e) => setFormData({ ...formData, cuisine_type: e.target.value })}
                  disabled={!editing}
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
                <textarea
                  className="input-field"
                  rows="3"
                  value={formData.description || ''}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  disabled={!editing}
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">Address</label>
                <input
                  type="text"
                  className="input-field"
                  value={formData.address || ''}
                  onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                  disabled={!editing}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Phone</label>
                <input
                  type="tel"
                  className="input-field"
                  value={formData.phone || ''}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  disabled={!editing}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
                <input
                  type="email"
                  className="input-field"
                  value={formData.email || ''}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  disabled={!editing}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Max Tables</label>
                <input
                  type="number"
                  className="input-field"
                  value={formData.max_tables || ''}
                  onChange={(e) => setFormData({ ...formData, max_tables: parseInt(e.target.value) })}
                  disabled={!editing}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Status</label>
                <select
                  className="input-field"
                  value={formData.is_active ? 'active' : 'inactive'}
                  onChange={(e) => setFormData({ ...formData, is_active: e.target.value === 'active' })}
                  disabled={!editing}
                >
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                </select>
              </div>
            </div>

            {editing && (
              <div className="flex gap-4 pt-6 border-t">
                <button type="submit" className="btn-primary px-6 py-3">
                  Save Changes
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setEditing(false);
                    setFormData(restaurant);
                  }}
                  className="btn-secondary px-6 py-3"
                >
                  Cancel
                </button>
              </div>
            )}
          </form>
        </div>
      </div>
    </DashboardLayout>
  );
}
