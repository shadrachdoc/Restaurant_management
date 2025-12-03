import { useState, useEffect } from 'react';
import { FiClock, FiCheck, FiX } from 'react-icons/fi';
import toast from 'react-hot-toast';

export default function KitchenDashboard() {
  const [orders, setOrders] = useState([
    {
      id: '1',
      order_number: 'ORD-001',
      table_number: 'T1',
      status: 'pending',
      items: [
        { name: 'Margherita Pizza', quantity: 2, notes: 'Extra cheese' },
        { name: 'Caesar Salad', quantity: 1, notes: '' },
      ],
      created_at: new Date().toISOString(),
      estimated_time: 15,
    },
    {
      id: '2',
      order_number: 'ORD-002',
      table_number: 'T3',
      status: 'preparing',
      items: [
        { name: 'Pasta Carbonara', quantity: 1, notes: '' },
        { name: 'Garlic Bread', quantity: 2, notes: 'Well done' },
      ],
      created_at: new Date(Date.now() - 300000).toISOString(),
      estimated_time: 12,
    },
  ]);

  const updateOrderStatus = (orderId, newStatus) => {
    setOrders(
      orders.map((order) =>
        order.id === orderId ? { ...order, status: newStatus } : order
      )
    );
    toast.success(`Order ${newStatus}!`);
  };

  const statusColors = {
    pending: 'bg-yellow-100 border-yellow-300 text-yellow-800',
    preparing: 'bg-blue-100 border-blue-300 text-blue-800',
    ready: 'bg-green-100 border-green-300 text-green-800',
  };

  const pendingOrders = orders.filter((o) => o.status === 'pending');
  const preparingOrders = orders.filter((o) => o.status === 'preparing');
  const readyOrders = orders.filter((o) => o.status === 'ready');

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-gray-900">Kitchen Display</h1>
        <div className="flex gap-6 mt-4">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-yellow-400 rounded"></div>
            <span className="font-semibold">Pending: {pendingOrders.length}</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-blue-500 rounded"></div>
            <span className="font-semibold">Preparing: {preparingOrders.length}</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-green-500 rounded"></div>
            <span className="font-semibold">Ready: {readyOrders.length}</span>
          </div>
        </div>
      </div>

      {/* Orders Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {orders.map((order) => (
          <div
            key={order.id}
            className={`${statusColors[order.status]} border-4 rounded-xl p-6 bg-white shadow-lg`}
          >
            {/* Order Header */}
            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 className="text-2xl font-bold text-gray-900">{order.order_number}</h3>
                <p className="text-lg font-semibold text-gray-700">Table {order.table_number}</p>
              </div>
              <div className="flex items-center gap-2 text-gray-600">
                <FiClock />
                <span className="font-semibold">{order.estimated_time}min</span>
              </div>
            </div>

            {/* Order Items */}
            <div className="mb-6 space-y-3">
              {order.items.map((item, idx) => (
                <div key={idx} className="bg-white p-3 rounded-lg border border-gray-200">
                  <div className="flex justify-between items-start mb-1">
                    <p className="font-semibold text-gray-900">{item.name}</p>
                    <span className="bg-gray-900 text-white px-3 py-1 rounded-full text-sm font-bold">
                      x{item.quantity}
                    </span>
                  </div>
                  {item.notes && (
                    <p className="text-sm text-red-600 font-medium">Note: {item.notes}</p>
                  )}
                </div>
              ))}
            </div>

            {/* Action Buttons */}
            <div className="space-y-2">
              {order.status === 'pending' && (
                <button
                  onClick={() => updateOrderStatus(order.id, 'preparing')}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-4 rounded-lg flex items-center justify-center gap-2 text-lg"
                >
                  <FiClock /> Start Preparing
                </button>
              )}

              {order.status === 'preparing' && (
                <button
                  onClick={() => updateOrderStatus(order.id, 'ready')}
                  className="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-4 rounded-lg flex items-center justify-center gap-2 text-lg"
                >
                  <FiCheck /> Mark as Ready
                </button>
              )}

              {order.status === 'ready' && (
                <div className="bg-green-600 text-white font-bold py-4 rounded-lg flex items-center justify-center gap-2 text-lg">
                  <FiCheck /> Ready for Pickup
                </div>
              )}

              <button
                onClick={() => updateOrderStatus(order.id, 'cancelled')}
                className="w-full bg-red-100 hover:bg-red-200 text-red-700 font-semibold py-3 rounded-lg flex items-center justify-center gap-2"
              >
                <FiX /> Cancel Order
              </button>
            </div>
          </div>
        ))}
      </div>

      {orders.length === 0 && (
        <div className="text-center py-20">
          <p className="text-gray-500 text-xl">No active orders</p>
        </div>
      )}
    </div>
  );
}
