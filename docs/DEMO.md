# Demo script (3-4 minutes)

Record this after migrate + seed. Use the default HR login unless you changed `.env`.

1. **Login (20s)**  
   Open the app. Show IncubyteESM branding and the prefilled HR account. Sign in. Mention cookies, not a JWT in DevTools Application > Local Storage.

2. **Insights (50s)**  
   Land on Insights. Point at active headcount, total annual payroll USD, average, median (or the Postgres-only note if you are on SQLite). Scroll distribution and country/department/level tables. This is the answer to "how does ESMINCUBYTE pay people?"

3. **Directory (40s)**  
   Employees. Search a name. Filter a country. Change page. Note the total count (~10,000). Export CSV of the current filter and open it in a spreadsheet — the Excel exit path, not the system of record.

4. **Create or open someone (30s)**  
   Open an employee. Show current local pay, FX snapshot, and USD. Optionally add a new employee with initial compensation.

5. **Adjust pay (40s)**  
   Adjust salary. Leave reason empty first to show validation. Then save a real reason (for example "Market adjustment"). Show the closed historical row and the new current row. Amounts on the old row did not change.

6. **Close (20s)**  
   Back to Insights. Recent changes should list the adjustment (seed rows are excluded). Log out. Refresh: login screen again.

Do not show XLSX. Do not claim live FX. Do not run seed on server start.
