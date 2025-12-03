import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { FiCheck, FiClock, FiPackage } from 'react-icons/fi';

export default function OrderTracking() {
  const { orderId } = useParams();
  const [order, setOrder] = useState({
    id: orderId,
    status: 'preparing',
    items: [
      { name: 'Margherita Pizza', quantity: 2, price: 12.99 },
      { name: 'Caesar Salad', quantity: 1, price: 8.99 },
    ],
    total: 34.97,
    table_number: 'T1',
    estimated_time: 15,
  });

  const statuses = [
    { key: 'pending', label: 'Order Received', icon: FiCheck },
    { key: 'preparing', label: 'Preparing', icon: FiClock },
    { key: 'ready', label: 'Ready to Serve', icon: FiPackage },
  ];

  const currentIndex = statuses.findIndex((s) => s.key === order.status);

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-2xl mx-auto px-4">
        <div className="bg-white rounded-xl shadow-lg p-8">
          <h1 className="text-3xl font-bold text-center mb-2">Order Tracking</h1>
          <p className="text-center text-gray-600 mb-8">Table {order.table_number}</p>

          {/* Status Timeline */}
          <div className="mb-12">
            {statuses.map((status, index) => {
              const Icon = status.icon;
              const isActive = index <= currentIndex;
              const isCurrent = index === currentIndex;

              return (
                <div key={status.key} className="flex items-center">
                  <div className="flex flex-col items-center">
                    <div
                      className={`w-12 h-12 rounded-full flex items-center justify-center ${
                        isActive ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-400'
                      } ${isCurrent ? 'ring-4 ring-blue-200' : ''}`}
                    >
                      <Icon className="text-xl" />
                    </div>
                    {index < statuses.length - 1 && (
                      <div className={`w-1 h-16 ${isActive ? 'bg-blue-600' : 'bg-gray-200'}`} />
                    )}
                  </div>
                  <div className="ml-6">
                    <p className={`font-semibold ${isActive ? 'text-gray-900' : 'text-gray-400'}`}>
                      {status.label}
                    </p>
                    {isCurrent && (
                      <p className="text-sm text-gray-600 mt-1">Estimated: {order.estimated_time} min</p>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Order Items */}
          <div className="border-t pt-6">
            <h3 className="font-bold text-lg mb-4">Order Items</h3>
            <div className="space-y-3">
              {order.items.map((item, idx) => (
                <div key={idx} className="flex justify-between">
                  <div>
                    <p className="font-medium">{item.name}</p>
                    <p className="text-sm text-gray-600">Qty: {item.quantity}</p>
                  </div>
                  <p className="font-semibold">${(item.price * item.quantity).toFixed(2)}</p>
                </div>
              ))}
            </div>
            <div className="border-t mt-4 pt-4 flex justify-between items-center">
              <p className="text-lg font-bold">Total</p>
              <p className="text-2xl font-bold text-blue-600">${order.total.toFixed(2)}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
