import { useState, useEffect } from 'react';
import DashboardLayout from '../../components/layout/DashboardLayout';
import { restaurantAPI } from '../../services/api';
import useAuthStore from '../../store/authStore';
import toast from 'react-hot-toast';

export default function RestaurantManagement() {
  const { user, updateUser } = useAuthStore();
  const [restaurant, setRestaurant] = useState(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [creating, setCreating] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    cuisine_type: '',
    description: '',
    address: '',
    phone: '',
    email: '',
    max_tables: 20,
    is_active: true,
  });

  useEffect(() => {
    if (user?.restaurant_id) {
      fetchRestaurant();
    } else {
      // No restaurant yet - show create form
      setLoading(false);
      setCreating(true);
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

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      const response = await restaurantAPI.create(formData);
      const newRestaurant = response.data;
      toast.success('Restaurant created successfully!');

      // Update user with restaurant_id
      updateUser({ restaurant_id: newRestaurant.id });

      setCreating(false);
      setRestaurant(newRestaurant);
      setFormData(newRestaurant);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create restaurant');
    }
  };

  const handleUpdate = async (e) => {
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

  // Show create form if user doesn't have a restaurant
  if (creating) {
    return (
      <DashboardLayout>
        <div className="p-8">
          <div className="max-w-4xl mx-auto">
            <div className="text-center mb-8">
              <h1 className="text-4xl font-bold text-gray-900 mb-2">Create Your Restaurant</h1>
              <p className="text-gray-600">Let's get your restaurant set up</p>
            </div>

            <div className="bg-white rounded-xl shadow-md p-8">
              <form onSubmit={handleCreate} className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Restaurant Name *</label>
                    <input
                      type="text"
                      className="input-field"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      required
                      placeholder="My Restaurant"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Cuisine Type</label>
                    <input
                      type="text"
                      className="input-field"
                      value={formData.cuisine_type}
                      onChange={(e) => setFormData({ ...formData, cuisine_type: e.target.value })}
                      placeholder="Italian, Chinese, etc."
                    />
                  </div>

                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
                    <textarea
                      className="input-field"
                      rows="3"
                      value={formData.description}
                      onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                      placeholder="Brief description of your restaurant"
                    />
                  </div>

                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-2">Address</label>
                    <input
                      type="text"
                      className="input-field"
                      value={formData.address}
                      onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                      placeholder="123 Main Street, City, State"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Phone</label>
                    <input
                      type="tel"
                      className="input-field"
                      value={formData.phone}
                      onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                      placeholder="+1 (555) 123-4567"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
                    <input
                      type="email"
                      className="input-field"
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      placeholder="contact@restaurant.com"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Max Tables</label>
                    <input
                      type="number"
                      className="input-field"
                      value={formData.max_tables}
                      onChange={(e) => setFormData({ ...formData, max_tables: parseInt(e.target.value) })}
                      min="1"
                    />
                  </div>
                </div>

                <div className="flex gap-4 pt-6 border-t">
                  <button type="submit" className="btn-primary flex-1 px-6 py-3 text-lg">
                    Create Restaurant
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="p-8">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Restaurant Management</h1>
          {!editing && restaurant && (
            <button onClick={() => setEditing(true)} className="btn-primary">
              Edit Details
            </button>
          )}
        </div>

        <div className="bg-white rounded-xl shadow-md p-8">
          <form onSubmit={handleUpdate} className="space-y-6">
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
