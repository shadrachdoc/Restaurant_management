# Restaurant Management Frontend Setup

## Project Structure Created

The React frontend has been initialized with the following structure:

```
frontend/
├── src/
│   ├── components/
│   │   ├── common/       # Reusable components
│   │   └── layout/       # Layout components
│   ├── pages/
│   │   ├── Auth/         # Login, Signup
│   │   ├── Admin/        # Restaurant Admin Dashboard
│   │   ├── Customer/     # Customer ordering interface
│   │   ├── Kitchen/      # Chef kitchen display
│   │   └── MasterAdmin/  # Master admin panel
│   ├── services/
│   │   └── api.js        # API service layer (COMPLETED)
│   ├── store/
│   │   └── authStore.js  # Authentication state (COMPLETED)
│   ├── hooks/            # Custom React hooks
│   ├── utils/            # Utility functions
│   ├── styles/
│   │   └── index.css     # Tailwind styles (COMPLETED)
│   ├── App.jsx           # Main app with routing (COMPLETED)
│   └── main.jsx          # Entry point (COMPLETED)
├── index.html
├── vite.config.js
├── tailwind.config.js
├── postcss.config.js
└── package.json
```

## Installation

1. Navigate to the frontend directory:
```bash
cd /home/shadrach/Restaurant_management/frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create `.env` file:
```bash
cat > .env << 'EOF'
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
EOF
```

## Running the Application

### Development Mode
```bash
npm run dev
```

The app will be available at: **http://localhost:3000**

### Build for Production
```bash
npm run build
```

### Preview Production Build
```bash
npm run preview
```

## What's Already Implemented

### ✅ Core Infrastructure
- **Vite + React 18** - Fast development server
- **React Router v6** - Client-side routing
- **Tailwind CSS** - Utility-first styling
- **Zustand** - State management
- **Axios** - HTTP client with interceptors
- **React Hot Toast** - Toast notifications

### ✅ API Service Layer (`src/services/api.js`)
Complete API integration with:
- Auth API (login, signup, logout, refresh token)
- Restaurant API (CRUD, analytics, branding)
- Menu API (CRUD, toggle availability)
- Table API (CRUD, QR code generation)
- Feedback API (CRUD, statistics)

Features:
- Automatic token refresh
- Request/response interceptors
- Error handling
- Authorization headers

### ✅ Authentication Store (`src/store/authStore.js`)
- Login/Signup/Logout
- Token management
- User state persistence
- Error handling with toast notifications

### ✅ Routing (`src/App.jsx`)
- Protected routes with role-based access
- Automatic redirection based on user role
- 404 handling

## Pages to Implement

### 1. Authentication Pages
**Priority: HIGH**

#### `src/pages/Auth/LoginPage.jsx`
```jsx
- Email/username + password form
- Remember me checkbox
- Link to signup page
- Error display
- Loading state
```

#### `src/pages/Auth/SignupPage.jsx`
```jsx
- Registration form with role selection
- Form validation
- Success/error handling
```

### 2. Customer Interface
**Priority: HIGH**

#### `src/pages/Customer/CustomerHome.jsx`
```jsx
- Restaurant search/list
- QR code scanner integration
- Recent orders
```

#### `src/pages/Customer/MenuView.jsx`
```jsx
- Display menu items with categories
- Add to cart functionality
- Dietary filters (vegetarian, vegan, etc.)
- Item details modal
- Cart sidebar
- Checkout process
```

#### `src/pages/Customer/OrderTracking.jsx`
```jsx
- Real-time order status
- Order history
- Feedback submission
```

### 3. Restaurant Admin Dashboard
**Priority: HIGH**

#### `src/pages/Admin/AdminDashboard.jsx`
```jsx
- Sales analytics (charts)
- Today's orders summary
- Table status overview
- Recent feedback
- Quick actions
```

#### `src/pages/Admin/RestaurantManagement.jsx`
```jsx
- Edit restaurant details
- Upload logo/banner
- Add upcoming events
- Manage advertisements
- Business hours
```

#### `src/pages/Admin/MenuManagement.jsx`
```jsx
- List all menu items (with categories)
- Add/Edit/Delete items
- Bulk import
- Toggle availability
- Price management
- Image upload
```

#### `src/pages/Admin/TableManagement.jsx`
```jsx
- List all tables
- Create new tables (auto-generates QR)
- View/Download QR codes
- Update table status
- Floor/section organization
- Print QR codes
```

#### `src/pages/Admin/FeedbackView.jsx`
```jsx
- List customer feedback
- Rating statistics
- Filter by date/rating
- Respond to feedback
- Export feedback data
```

### 4. Kitchen Interface
**Priority: MEDIUM**

#### `src/pages/Kitchen/KitchenDashboard.jsx`
```jsx
- Real-time order queue
- Order cards with items
- Status update buttons (Preparing → Ready)
- Audio notification for new orders
- Filter by priority
- Estimated preparation time
```

### 5. Master Admin Interface
**Priority: LOW**

#### `src/pages/MasterAdmin/MasterAdminDashboard.jsx`
```jsx
- List all restaurants
- Subscription management
- Global analytics
- User management
- System settings
```

## Common Components Needed

Create these in `src/components/common/`:

1. **Button.jsx** - Reusable button component
2. **Input.jsx** - Form input with validation
3. **Modal.jsx** - Modal dialog
4. **Card.jsx** - Content card
5. **Loader.jsx** - Loading spinner
6. **Badge.jsx** - Status badge
7. **Table.jsx** - Data table
8. **Dropdown.jsx** - Dropdown menu
9. **Sidebar.jsx** - Navigation sidebar
10. **Navbar.jsx** - Top navigation bar

## Layout Components

Create these in `src/components/layout/`:

1. **DashboardLayout.jsx** - Admin/Kitchen layout with sidebar
2. **CustomerLayout.jsx** - Customer-facing layout
3. **AuthLayout.jsx** - Login/Signup layout

## Quick Start Example: Login Page

Create `src/pages/Auth/LoginPage.jsx`:
```jsx
import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import useAuthStore from '../../store/authStore';

export default function LoginPage() {
  const [credentials, setCredentials] = useState({ username: '', password: '' });
  const { login, isLoading } = useAuthStore();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    const result = await login(credentials);
    if (result.success) {
      navigate('/');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center p-4">
      <div className="card max-w-md w-full">
        <h1 className="text-3xl font-bold text-center mb-6">Restaurant Management</h1>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Username</label>
            <input
              type="text"
              className="input-field"
              value={credentials.username}
              onChange={(e) => setCredentials({ ...credentials, username: e.target.value })}
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Password</label>
            <input
              type="password"
              className="input-field"
              value={credentials.password}
              onChange={(e) => setCredentials({ ...credentials, password: e.target.value })}
              required
            />
          </div>
          <button type="submit" className="btn-primary w-full" disabled={isLoading}>
            {isLoading ? 'Logging in...' : 'Login'}
          </button>
        </form>
        <p className="text-center mt-4 text-sm">
          Don't have an account? <Link to="/signup" className="text-primary-600 hover:underline">Sign up</Link>
        </p>
      </div>
    </div>
  );
}
```

## Testing the Backend Integration

Once you run `npm run dev`, you can:

1. Go to http://localhost:3000/login
2. Login with: `testadmin` / `Password123!`
3. You'll be redirected to the admin dashboard

## Next Steps

1. Install dependencies: `npm install`
2. Start development server: `npm run dev`
3. Implement the Login and Signup pages first
4. Then implement Admin Dashboard
5. Then Customer interface
6. Finally Kitchen and Master Admin interfaces

## Useful Commands

```bash
# Install new package
npm install package-name

# Run linter
npm run lint

# Clear node_modules and reinstall
rm -rf node_modules package-lock.json && npm install
```

## Important Notes

- The API service layer is complete and ready to use
- All API endpoints are properly configured
- Authentication flow with token refresh is implemented
- Error handling and toast notifications are set up
- Routing and protected routes are configured

You just need to build the UI components and pages!
