# Automated Testing Setup with Playwright

**Recommended Tool**: Playwright
**Test Framework**: Playwright Test
**Language**: TypeScript
**CI/CD**: GitHub Actions

---

## Why Playwright?

1. **Fast & Reliable**: Auto-waits for elements, rarely flaky
2. **Record Tests**: Use `npx playwright codegen` to record interactions
3. **Parallel Execution**: Run tests in parallel for speed
4. **Screenshots/Videos**: Automatic on failure
5. **API Testing**: Can test backend APIs too
6. **Multi-Browser**: Chrome, Firefox, Safari, Mobile
7. **Modern**: Built by Microsoft, actively maintained

---

## Quick Start

### 1. Install Playwright

```bash
cd /home/shadrach/Restaurant_management
npm init playwright@latest

# Follow prompts:
# - TypeScript: Yes
# - Tests folder: tests
# - GitHub Actions: Yes
# - Install browsers: Yes
```

### 2. Project Structure

```
Restaurant_management/
├── tests/
│   ├── auth/
│   │   ├── login.spec.ts
│   │   ├── logout.spec.ts
│   │   └── staff-management.spec.ts
│   ├── orders/
│   │   ├── place-order-guest.spec.ts
│   │   ├── place-order-qr.spec.ts
│   │   ├── receipt-generation.spec.ts
│   │   └── kitchen-workflow.spec.ts
│   ├── tables/
│   │   ├── table-crud.spec.ts
│   │   ├── qr-regeneration.spec.ts
│   │   └── table-status.spec.ts
│   ├── menu/
│   │   ├── menu-crud.spec.ts
│   │   └── category-management.spec.ts
│   ├── fixtures/
│   │   ├── test-data.ts
│   │   └── auth.setup.ts
│   └── utils/
│       ├── test-helpers.ts
│       └── db-cleanup.ts
├── playwright.config.ts
└── package.json
```

---

## Sample Test Cases

### Test 1: Login Flow
**File**: `tests/auth/login.spec.ts`

```typescript
import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
  test('should login as restaurant admin', async ({ page }) => {
    // Navigate to login page
    await page.goto('https://restaurant.corpv3.com/login');

    // Fill login form
    await page.fill('input[name="username"]', 'admin@phalwan-briyani.com');
    await page.fill('input[name="password"]', 'your_password');

    // Click login button
    await page.click('button[type="submit"]');

    // Wait for navigation
    await page.waitForURL('**/admin/dashboard');

    // Verify logged in
    await expect(page.locator('text=Dashboard')).toBeVisible();
    await expect(page.locator('text=Logout')).toBeVisible();
  });

  test('should show error for invalid credentials', async ({ page }) => {
    await page.goto('https://restaurant.corpv3.com/login');

    await page.fill('input[name="username"]', 'wrong@email.com');
    await page.fill('input[name="password"]', 'wrongpassword');
    await page.click('button[type="submit"]');

    // Should show error toast
    await expect(page.locator('text=Invalid credentials')).toBeVisible();
  });
});
```

---

### Test 2: Receipt Generation Flow
**File**: `tests/orders/receipt-generation.spec.ts`

```typescript
import { test, expect } from '@playwright/test';

test.describe('Receipt Generation', () => {
  let orderId: string;

  test.beforeEach(async ({ page }) => {
    // Place an order first (setup)
    await page.goto('https://restaurant.corpv3.com/customer/menu?restaurant=phalwan-briyani&table=8caa756d-7fb9-4717-a816-cd3857fd058a&tableNumber=T1');

    // Add item to cart
    await page.click('button:has-text("Add to Cart")').first();

    // Checkout
    await page.click('button:has-text("Checkout")');

    // Fill customer details
    await page.fill('input[name="customer_name"]', 'Test Customer');
    await page.fill('input[name="customer_phone"]', '1234567890');

    // Place order
    await page.click('button:has-text("Place Order")');

    // Extract order ID from URL
    await page.waitForURL('**/order-tracking/**');
    orderId = page.url().split('/').pop()!;
  });

  test('chef marks order as served', async ({ page, context }) => {
    // Login as chef in new page
    const chefPage = await context.newPage();
    await chefPage.goto('https://restaurant.corpv3.com/login');
    await chefPage.fill('input[name="username"]', 'adminchef');
    await chefPage.fill('input[name="password"]', 'chef_password');
    await chefPage.click('button[type="submit"]');

    // Navigate to kitchen
    await chefPage.waitForURL('**/chef');

    // Find the order and mark as served
    await chefPage.click(`button:has-text("Confirm Order")`);
    await chefPage.click(`button:has-text("Start Preparing")`);
    await chefPage.click(`button:has-text("Mark as Ready")`);
    await chefPage.click(`button:has-text("Mark as Served")`);

    await chefPage.close();
  });

  test('table should still be occupied after served', async ({ page }) => {
    // Login as admin
    await page.goto('https://restaurant.corpv3.com/login');
    await page.fill('input[name="username"]', 'admin@phalwan-briyani.com');
    await page.fill('input[name="password"]', 'admin_password');
    await page.click('button[type="submit"]');

    // Go to tables
    await page.goto('https://restaurant.corpv3.com/admin/tables');

    // Table T1 should be red (occupied)
    const tableT1 = page.locator('text=T1').locator('..');
    await expect(tableT1.locator('.bg-red-100')).toBeVisible();
  });

  test('customer generates receipt and frees table', async ({ page }) => {
    // Go to order tracking
    await page.goto(`https://restaurant.corpv3.com/customer/order-tracking/${orderId}`);

    // Wait for receipt button to appear (order must be SERVED)
    await expect(page.locator('button:has-text("Generate Receipt")')).toBeVisible();

    // Click generate receipt
    await page.click('button:has-text("Generate Receipt")');

    // Confirm dialog
    page.on('dialog', dialog => dialog.accept());

    // Wait for success toast
    await expect(page.locator('text=Receipt generated')).toBeVisible();
  });

  test('table should be available after receipt', async ({ page }) => {
    // Login as admin
    await page.goto('https://restaurant.corpv3.com/login');
    await page.fill('input[name="username"]', 'admin@phalwan-briyani.com');
    await page.fill('input[name="password"]', 'admin_password');
    await page.click('button[type="submit"]');

    // Go to tables
    await page.goto('https://restaurant.corpv3.com/admin/tables');

    // Table T1 should be green (available)
    const tableT1 = page.locator('text=T1').locator('..');
    await expect(tableT1.locator('.bg-green-100')).toBeVisible();
  });
});
```

---

### Test 3: QR Code Regeneration Security
**File**: `tests/tables/qr-regeneration.spec.ts`

```typescript
import { test, expect } from '@playwright/test';

test.describe('QR Code Security', () => {
  test.beforeEach(async ({ page }) => {
    // Login as admin
    await page.goto('https://restaurant.corpv3.com/login');
    await page.fill('input[name="username"]', 'admin@phalwan-briyani.com');
    await page.fill('input[name="password"]', 'admin_password');
    await page.click('button[type="submit"]');

    // Navigate to tables
    await page.goto('https://restaurant.corpv3.com/admin/tables');
  });

  test('should show password modal on regenerate click', async ({ page }) => {
    // Click regenerate button
    await page.click('button:has-text("Regenerate")').first();

    // Password modal should appear
    await expect(page.locator('h2:has-text("Confirm QR Regeneration")')).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
    await expect(page.locator('button:has-text("Confirm & Regenerate")')).toBeVisible();
  });

  test('should reject invalid password', async ({ page }) => {
    await page.click('button:has-text("Regenerate")').first();

    // Enter wrong password
    await page.fill('input[type="password"]', 'wrongpassword');
    await page.click('button:has-text("Confirm & Regenerate")');

    // Should show error
    await expect(page.locator('text=Invalid password')).toBeVisible();

    // Modal should stay open
    await expect(page.locator('h2:has-text("Confirm QR Regeneration")')).toBeVisible();
  });

  test('should regenerate QR with valid password', async ({ page }) => {
    await page.click('button:has-text("Regenerate")').first();

    // Enter correct password
    await page.fill('input[type="password"]', 'admin_password');
    await page.click('button:has-text("Confirm & Regenerate")');

    // Should show success
    await expect(page.locator('text=QR code regenerated')).toBeVisible();

    // QR viewer should open
    await expect(page.locator('h2:has-text("Table")').first()).toBeVisible();
  });

  test('should close modal on cancel', async ({ page }) => {
    await page.click('button:has-text("Regenerate")').first();

    // Click cancel
    await page.click('button:has-text("Cancel")');

    // Modal should close
    await expect(page.locator('h2:has-text("Confirm QR Regeneration")')).not.toBeVisible();
  });

  test('should show warning message in modal', async ({ page }) => {
    await page.click('button:has-text("Regenerate")').first();

    // Warning should be visible
    await expect(page.locator('text=The old QR code will no longer work')).toBeVisible();
  });
});
```

---

### Test 4: Staff Management
**File**: `tests/auth/staff-management.spec.ts`

```typescript
import { test, expect } from '@playwright/test';

test.describe('Staff Management', () => {
  test.beforeEach(async ({ page }) => {
    // Login as restaurant admin
    await page.goto('https://restaurant.corpv3.com/login');
    await page.fill('input[name="username"]', 'admin@phalwan-briyani.com');
    await page.fill('input[name="password"]', 'admin_password');
    await page.click('button[type="submit"]');

    // Navigate to staff page
    await page.goto('https://restaurant.corpv3.com/admin/staff');
  });

  test('should load staff management page', async ({ page }) => {
    await expect(page.locator('h1:has-text("Staff Management")')).toBeVisible();
    await expect(page.locator('button:has-text("Add Staff")')).toBeVisible();
  });

  test('should create new chef account', async ({ page }) => {
    const uniqueUsername = `chef_${Date.now()}`;

    // Click add staff
    await page.click('button:has-text("Add Staff")');

    // Fill form
    await page.selectOption('select[name="role"]', 'chef');
    await page.fill('input[name="username"]', uniqueUsername);
    await page.fill('input[name="email"]', `${uniqueUsername}@test.com`);
    await page.fill('input[name="full_name"]', 'Test Chef');
    await page.fill('input[name="password"]', 'testpass123');

    // Submit
    await page.click('button:has-text("Create Chef")');

    // Should show success
    await expect(page.locator('text=Chef account created')).toBeVisible();

    // Should appear in list
    await expect(page.locator(`text=${uniqueUsername}`)).toBeVisible();
  });

  test('should filter by role', async ({ page }) => {
    // Click Chefs tab
    await page.click('button:has-text("Chefs")');

    // Should only show chefs
    await expect(page.locator('text=CHEF')).toBeVisible();

    // Click Customers tab
    await page.click('button:has-text("Customers")');

    // Should only show customers
    await expect(page.locator('text=CUSTOMER')).toBeVisible();
  });

  test('should delete staff member', async ({ page }) => {
    // Create a test staff first
    const uniqueUsername = `temp_chef_${Date.now()}`;
    await page.click('button:has-text("Add Staff")');
    await page.selectOption('select[name="role"]', 'chef');
    await page.fill('input[name="username"]', uniqueUsername);
    await page.fill('input[name="email"]', `${uniqueUsername}@test.com`);
    await page.fill('input[name="password"]', 'testpass123');
    await page.click('button:has-text("Create Chef")');

    // Wait for success
    await page.waitForSelector(`text=${uniqueUsername}`);

    // Delete it
    const staffRow = page.locator(`text=${uniqueUsername}`).locator('..');
    await staffRow.locator('button:has-text("Delete")').click();

    // Confirm dialog
    page.on('dialog', dialog => dialog.accept());

    // Should be removed
    await expect(page.locator(`text=${uniqueUsername}`)).not.toBeVisible();
  });
});
```

---

## Configuration

### `playwright.config.ts`

```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',

  // Run tests in parallel
  fullyParallel: true,

  // Fail build on CI if you accidentally left test.only
  forbidOnly: !!process.env.CI,

  // Retry on CI only
  retries: process.env.CI ? 2 : 0,

  // Opt out of parallel tests on CI
  workers: process.env.CI ? 1 : undefined,

  // Reporter
  reporter: [
    ['html'],
    ['json', { outputFile: 'test-results.json' }],
    ['junit', { outputFile: 'test-results.xml' }]
  ],

  use: {
    // Base URL
    baseURL: 'https://restaurant.corpv3.com',

    // Collect trace when retrying the failed test
    trace: 'on-first-retry',

    // Screenshot on failure
    screenshot: 'only-on-failure',

    // Video on failure
    video: 'retain-on-failure',
  },

  // Configure projects for major browsers
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
    // Mobile viewports
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
    },
    {
      name: 'Mobile Safari',
      use: { ...devices['iPhone 12'] },
    },
  ],
});
```

---

## Running Tests

### Local Development

```bash
# Run all tests
npx playwright test

# Run specific file
npx playwright test tests/orders/receipt-generation.spec.ts

# Run in UI mode (visual debugging)
npx playwright test --ui

# Run in headed mode (see browser)
npx playwright test --headed

# Run specific browser
npx playwright test --project=chromium

# Debug mode
npx playwright test --debug
```

### Generate Tests

```bash
# Record tests interactively
npx playwright codegen https://restaurant.corpv3.com

# This opens a browser and records your actions!
```

### View Reports

```bash
# Open HTML report
npx playwright show-report

# This shows screenshots, videos, traces of failed tests
```

---

## CI/CD Integration

### GitHub Actions

**File**: `.github/workflows/playwright.yml`

```yaml
name: Playwright Tests

on:
  push:
    branches: [ main, developer ]
  pull_request:
    branches: [ main, developer ]

jobs:
  test:
    timeout-minutes: 60
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - uses: actions/setup-node@v3
      with:
        node-version: 18

    - name: Install dependencies
      run: npm ci

    - name: Install Playwright Browsers
      run: npx playwright install --with-deps

    - name: Run Playwright tests
      run: npx playwright test

    - uses: actions/upload-artifact@v3
      if: always()
      with:
        name: playwright-report
        path: playwright-report/
        retention-days: 30
```

---

## Test Data Management

### Fixtures

**File**: `tests/fixtures/test-data.ts`

```typescript
export const testUsers = {
  admin: {
    username: 'admin@phalwan-briyani.com',
    password: process.env.TEST_ADMIN_PASSWORD || 'admin_password'
  },
  chef: {
    username: 'adminchef',
    password: process.env.TEST_CHEF_PASSWORD || 'chef_password'
  }
};

export const testRestaurant = {
  id: process.env.TEST_RESTAURANT_ID,
  slug: 'phalwan-briyani'
};

export const testTable = {
  id: '8caa756d-7fb9-4717-a816-cd3857fd058a',
  number: 'T1'
};
```

### Authentication Setup

**File**: `tests/fixtures/auth.setup.ts`

```typescript
import { test as setup } from '@playwright/test';
import { testUsers } from './test-data';

const authFile = 'playwright/.auth/user.json';

setup('authenticate as admin', async ({ page }) => {
  await page.goto('https://restaurant.corpv3.com/login');
  await page.fill('input[name="username"]', testUsers.admin.username);
  await page.fill('input[name="password"]', testUsers.admin.password);
  await page.click('button[type="submit"]');

  await page.waitForURL('**/admin/dashboard');
  await page.context().storageState({ path: authFile });
});
```

---

## Best Practices

### 1. Use Page Object Model

```typescript
// tests/pages/LoginPage.ts
export class LoginPage {
  constructor(private page: Page) {}

  async goto() {
    await this.page.goto('/login');
  }

  async login(username: string, password: string) {
    await this.page.fill('input[name="username"]', username);
    await this.page.fill('input[name="password"]', password);
    await this.page.click('button[type="submit"]');
  }
}

// Usage in test
import { LoginPage } from '../pages/LoginPage';

test('login test', async ({ page }) => {
  const loginPage = new LoginPage(page);
  await loginPage.goto();
  await loginPage.login('admin', 'password');
});
```

### 2. Use Data-Testid Attributes

Add to your React components:
```jsx
<button data-testid="add-to-cart-btn">Add to Cart</button>
```

Use in tests:
```typescript
await page.click('[data-testid="add-to-cart-btn"]');
```

### 3. Database Cleanup

```typescript
// tests/utils/db-cleanup.ts
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

export async function cleanupTestData() {
  await execAsync(`
    kubectl exec -n restaurant-system postgres-0 -- psql -U restaurant_admin -d restaurant_db -c "
      DELETE FROM orders WHERE customer_name LIKE 'Test%';
      DELETE FROM users WHERE username LIKE 'test_%';
    "
  `);
}
```

---

## Cost & Time Estimates

### Initial Setup
- **Time**: 2-4 hours
- **Cost**: Free (Playwright is open-source)

### Writing Tests
- **Login/Auth**: 30 min
- **Receipt Generation**: 1 hour
- **QR Security**: 45 min
- **Staff Management**: 1 hour
- **Order Flow**: 2 hours
- **Table Management**: 1 hour

**Total**: ~7 hours for comprehensive coverage

### Maintenance
- **Per test update**: 5-15 min
- **Monthly maintenance**: 2-4 hours

---

## Monitoring & Reporting

### Test Coverage Dashboard

```bash
# Generate coverage report
npx playwright test --reporter=html

# View at: playwright-report/index.html
```

### Slack Notifications (Optional)

Add to GitHub Actions:
```yaml
- name: Slack Notification
  if: failure()
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    text: 'Playwright tests failed!'
    webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

---

## Next Steps

1. **Install Playwright**: `npm init playwright@latest`
2. **Record first test**: `npx playwright codegen https://restaurant.corpv3.com`
3. **Run tests**: `npx playwright test`
4. **Add to CI/CD**: Create GitHub Actions workflow
5. **Expand coverage**: Add more test scenarios

---

## Alternative: Quick & Dirty Shell Script Testing

If you want something **RIGHT NOW** without setup:

```bash
# tests/quick-test.sh
#!/bin/bash

echo "🧪 Testing Restaurant Management System..."

# Test 1: Login
echo "Test 1: Login..."
curl -X POST https://restaurant.corpv3.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}' \
  | jq '.access_token' && echo "✅ Login works" || echo "❌ Login failed"

# Test 2: Create Order
echo "Test 2: Create order..."
# ... more curl commands

echo "✅ All tests passed!"
```

But I **strongly recommend Playwright** for maintainable, visual testing.
