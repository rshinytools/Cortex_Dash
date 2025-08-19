# System Admin Workflow - Step by Step

## 🔐 Step 1: Login
**URL:** `http://localhost:3000/login`

**Credentials:**
```
Email: admin@sagarmatha.ai
Password: adadad123
```

**After Login:** Automatically redirected to → `/admin` (Admin Dashboard)

---

## 📊 Step 2: Admin Dashboard
**URL:** `http://localhost:3000/admin`

**What You See:**
- System Overview Cards showing:
  - Total Users (e.g., 142)
  - Active Studies (e.g., 12)
  - Organizations (e.g., 8)
  - Templates (e.g., 5)
- Real-time activity charts
- Recent audit logs
- System health metrics

**Quick Actions Available:**
1. **Organizations** → Create/Manage organizations
2. **Studies** → Create/Manage studies
3. **Users** → Manage users and permissions
4. **RBAC** → Configure roles and permissions
5. **Widget Engines** → Manage dashboard widgets
6. **Dashboard Templates** → Create reusable templates

---

## 🏢 Step 3: Create Organization (First Time Setup)
**Click:** "Organizations" from admin dashboard
**URL:** `http://localhost:3000/organizations`

**Then Click:** "New Organization" button
**URL:** `http://localhost:3000/organizations/new`

**Fill in:**
```
Organization Name: Pharma Corp
Organization Code: PHARMA
Address: 123 Clinical Way
City: Boston
State: MA
Country: USA
```

**Click:** "Create Organization"
**Result:** Organization created, redirected to organization list

---

## 🔬 Step 4: Create Study
**Click:** "Studies" from admin dashboard
**URL:** `http://localhost:3000/studies`

**Then Click:** "New Study" button
**URL:** `http://localhost:3000/studies/new`

### 4.1: Basic Study Information
```
Study Name: COVID-19 Vaccine Trial
Protocol Number: COV-VAC-001
Study Code: CVAC
Description: Phase 3 vaccine efficacy study
Phase: Phase 3
Therapeutic Area: Vaccines
Target Enrollment: 5000
Number of Sites: 50
Organization: Pharma Corp (select from dropdown)
```

**Click:** "Save as Draft"
**Status:** Study created in DRAFT status

---

## 📁 Step 5: Configure Data Source
**From Study Page:** Click on the newly created study
**URL:** `http://localhost:3000/studies/{study-id}`

**Click:** "Configure Data Source" button

### Option A: Manual Upload (Most Common for Admin)
**Select:** "Manual File Upload"

**Configuration:**
```
Upload Type: ZIP_UPLOAD
Allowed Formats: [✓] SAS (.sas7bdat)
                 [✓] CSV (.csv)
                 [✓] XPT (.xpt)
Max File Size: 500 MB
```

### Option B: Medidata Rave API
**Select:** "Medidata Rave API"

**Configuration:**
```
API URL: https://api.mdsol.com
Study OID: COV-VAC-001
Username: [API Username]
Password: [API Password]
Refresh Schedule: Daily at 6 AM
```

### Option C: Veeva Vault
**Select:** "Veeva Vault"

**Configuration:**
```
Vault URL: https://pharma.veevavault.com
Study ID: VS-2024-001
Username: [Vault Username]
Password: [Vault Password]
```

**Click:** "Save Configuration"

---

## 📤 Step 6: Upload Data Files
**Click:** "Upload Data" button

### 6.1: File Upload Interface
**Drag and Drop or Browse:**
```
Files to Upload:
✓ ae.sas7bdat (111 MB) - Adverse Events
✓ dm.sas7bdat (5 MB) - Demographics  
✓ ds.sas7bdat (1.8 MB) - Disposition
✓ lb.sas7bdat - Laboratory Results
✓ vs.sas7bdat - Vital Signs
```

**Click:** "Start Upload"

### 6.2: Processing Status
**You'll See:**
```
Processing Files...
✓ ae.sas7bdat - Uploaded
  ↳ Converting to Parquet...
  ↳ Detecting patterns... (Medidata Rave SDTM detected)
  ↳ Extracting metadata...
  ↳ Complete: 245,678 rows processed

✓ dm.sas7bdat - Uploaded
  ↳ Converting to Parquet...
  ↳ Complete: 5,000 rows processed
```

**Time:** ~2-5 minutes for all files

---

## 🎨 Step 7: Select Dashboard Template
**After Data Upload:** System prompts → "Select Dashboard Template"

**Available Templates:**
1. **Safety Dashboard** (Recommended for AE data)
   - SAE Summary KPI
   - AE Distribution Chart
   - Timeline Chart
   - Site Safety Metrics

2. **Enrollment Dashboard**
   - Enrollment Rate KPI
   - Site Performance
   - Demographics Chart

3. **Custom Dashboard**
   - Build from scratch

**Select:** "Safety Dashboard"
**Click:** "Apply Template"

---

## 🔄 Step 8: Review Auto-Mapping
**System Shows:** Auto-detected field mappings

**Auto-Mapping Results:**
```
✓ USUBJID → Subject ID (95% confidence)
✓ AESER → Serious AE Flag (92% confidence)
✓ AESTDTC → AE Start Date (88% confidence)
✓ SITEID → Site ID (90% confidence)
✓ ARM → Treatment Arm (85% confidence)

⚠️ AEDECOD → [Manual Review Needed]
```

**Actions:**
- ✅ Accept correct mappings
- ✏️ Edit incorrect mappings
- ➕ Add missing mappings

**Click:** "Confirm Mappings"

---

## 📊 Step 9: Configure Widgets
**Dashboard Designer Opens**

### 9.1: KPI Widget - SAE Count
```
Widget Type: KPI Card
Title: Serious Adverse Events
Data Source: ae.parquet
Filter: AESER = 'Y'
Calculation: COUNT(*)
Refresh: Every 30 seconds
```

### 9.2: KPI Widget - Enrollment Rate
```
Widget Type: KPI Card
Title: Enrollment Rate
Data Source: dm.parquet
Calculation: COUNT(USUBJID) / Days_Since_Start
Show Trend: Yes
```

### 9.3: Chart Widget - AE Distribution
```
Widget Type: Bar Chart
Title: AE by System Organ Class
Data Source: ae.parquet
X-Axis: AEBODSYS
Y-Axis: COUNT(*)
```

**Click:** "Save Configuration"

---

## ✅ Step 10: Validate & Activate
**System Runs Validation:**
```
Validation Checklist:
✓ Data source connected
✓ Files processed successfully
✓ All required fields mapped
✓ Widget configurations valid
✓ User permissions set
✓ Audit trail configured
```

**Click:** "Activate Study"

**Status Changes:**
- Study Status: `DRAFT` → `ACTIVE`
- Dashboard Status: `CONFIGURATION` → `LIVE`

---

## 👀 Step 11: View Live Dashboard
**Click:** "View Dashboard"
**URL:** `http://localhost:3000/dashboard/{study-id}`

**What You See:**
- Live KPI cards with real data
- Interactive charts
- Data refresh countdown
- Export options
- Last updated timestamp

---

## 🔄 Step 12: Ongoing Admin Tasks

### Daily Tasks:
1. **Check System Health**
   - Visit `/admin` dashboard
   - Review any alerts

2. **Upload New Data** (if manual)
   - Go to study page
   - Click "Upload New Data"
   - Upload latest files

3. **Monitor User Activity**
   - Check audit logs
   - Review access patterns

### Weekly Tasks:
1. **Review Data Quality**
   - Check mapping accuracy
   - Review error logs

2. **User Management**
   - Add/remove users
   - Update permissions

3. **Performance Check**
   - Query execution times
   - Storage usage

### Monthly Tasks:
1. **Security Audit**
   - Review access logs
   - Check failed login attempts

2. **Backup Verification**
   - Ensure backups running
   - Test restore process

---

## 🎯 Quick Actions Menu

From any page, admin can:

### Top Navigation Bar:
```
[Sagarmatha Logo] | Organizations | Studies | Users | Templates | Settings | [User Menu ▼]
```

### User Menu Dropdown:
- Profile
- System Settings
- Audit Logs
- Help & Support
- Logout

---

## ⚡ Keyboard Shortcuts

- `Ctrl + K` - Quick search
- `Ctrl + N` - New study
- `Ctrl + U` - Upload data
- `Ctrl + D` - Go to dashboard
- `Ctrl + ?` - Help

---

## 🚨 Common Admin Workflows

### A. Weekly Data Update (Manual)
1. Login → Admin Dashboard
2. Studies → Select Study
3. Click "Upload New Data"
4. Drop files → Process
5. Review logs → Done

### B. Add New User
1. Admin → Users
2. Click "New User"
3. Fill details + Assign role
4. Set study access
5. Send invite email

### C. Create New Dashboard Template
1. Admin → Dashboard Templates
2. Click "Create Template"
3. Design layout
4. Configure widgets
5. Save as template

### D. Emergency Data Refresh
1. Studies → Select Study
2. Data Sources → Manual Sync
3. Monitor progress
4. Verify dashboard updated

---

## 📝 Important URLs for Admin

- **Login:** `/login`
- **Admin Dashboard:** `/admin`
- **Organizations:** `/organizations`
- **Studies:** `/studies`
- **Users:** `/admin/users`
- **RBAC:** `/admin/rbac`
- **Templates:** `/admin/dashboard-templates`
- **Audit Trail:** `/admin/audit-trail`
- **System Health:** `/admin/system-health`
- **Live Dashboard:** `/dashboard/{study-id}`

---

## 💡 Pro Tips for Admins

1. **Batch Upload:** Upload all SAS files at once - system processes in parallel
2. **Template Reuse:** Save successful mappings as templates for similar studies
3. **Schedule Uploads:** Set calendar reminders for manual data uploads
4. **Monitor Performance:** Check dashboard load times after large uploads
5. **Audit Trail:** All actions are logged - use for compliance reports

---

## 🔧 Troubleshooting

### "Upload Failed"
- Check file format (must be .sas7bdat, .csv, or .xpt)
- Verify file size < 500MB
- Check disk space on server

### "Mapping Failed"
- Review column names in uploaded file
- Manually map unrecognized fields
- Save successful mapping as template

### "Dashboard Not Updating"
- Check data source status
- Verify refresh schedule
- Manual sync from study page

### "Access Denied"
- Verify user has correct role
- Check study-level permissions
- Review organization access