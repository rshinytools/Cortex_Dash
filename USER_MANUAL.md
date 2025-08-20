# Cortex Clinical Dashboard - User Manual

## 1. Getting Started

Welcome to the Cortex Clinical Dashboard! This guide will help you get started with the basics.

### 1.1. Logging In

To access the platform, you'll need to log in with your credentials.

1.  **Navigate to the login page.** In your web browser, go to `http://localhost:3000/login`.
2.  **Enter your credentials.** Type in your email address and password.
3.  **Click "Sign In".**

If your login is successful, you'll be redirected to the main dashboard.

### 1.2. Your First Study

The first thing you'll want to do is create a study. Studies are where you'll manage your clinical trial data.

1.  **Go to the Studies page.** Click on "Studies" in the main navigation menu.
2.  **Click "Create New Study".**
3.  **Fill in the study details.** You'll be asked to provide information like the study name, code, and protocol number.
4.  **Click "Create Study".**

After you create a study, you'll be guided through the study initialization process.

### 1.3. Navigating the Application

The main navigation menu on the left side of the screen is your primary way to get around the application. Here's a quick overview of the main sections:

*   **Dashboard:** Your main landing page, where you can see an overview of your studies.
*   **Studies:** Manage your studies, including creating new ones and configuring existing ones.
*   **Analytics:** View reports and visualizations of your data.
*   **Settings:** Configure your application settings.
*   **Profile:** Manage your user profile.
*   **Admin:** (For administrators only) Manage users, organizations, and other system-level settings.

---

## 2. Authentication

### 2.1. Password Recovery

If you forget your password, you can easily reset it.

1.  **Click "Forgot password?"** on the login page.
2.  **Enter your email address.**
3.  **Click "Send reset instructions".**

Check your email for a link to reset your password. The link is valid for 24 hours.

### 2.2. Resetting Your Password

1.  **Click the reset link** in the email you received.
2.  **Enter your new password.** Make sure it's at least 8 characters long.
3.  **Confirm your new password.**
4.  **Click "Reset password".**

You can now log in with your new password.

---

## 3. Study Management

### 3.1. Creating a Study

Studies are the heart of the Cortex Clinical Dashboard. They hold all the data and configurations for a specific clinical trial.

1.  **Go to the Studies page.**
2.  **Click "Create New Study".**
3.  **Fill in the required information:**
    *   **Study Name:** A descriptive name for your study.
    *   **Study Code:** A short identifier (e.g., "COV-VAC-P3").
    *   **Protocol Number:** The unique protocol identifier.
    *   **Phase:** The clinical trial phase.
    *   **Therapeutic Area:** The disease or condition being studied.
    *   **Description:** A brief description of the study.
4.  **Click "Create Study".**

### 3.2. Study Initialization

After you create a study, you'll need to initialize it. This is a four-step process that sets up your study with templates, data, and configurations.

1.  **Template Application:** Apply a dashboard template to your study.
2.  **Data Upload & Processing:** Upload your clinical data files.
3.  **Field Mapping Configuration:** Map the fields in your data to the fields in the dashboard.
4.  **Study Activation:** Activate your study to make it live.

The initialization process runs in the background, and you can monitor its progress in real-time.

### 3.3. Study Configuration

Once a study is initialized, you can configure its settings.

1.  **Go to the Studies page.**
2.  **Click on the study you want to configure.**
3.  **Click the "Settings" tab.**

Here, you can modify the study's general settings, dashboard configuration, data pipelines, and compliance settings.

---

## 4. Dashboard Designer

The Dashboard Designer is a powerful tool that allows you to create and customize dashboards for your studies.

### 4.1. Creating a Dashboard

1.  **Go to the Dashboard Designer.** Click on "Admin" in the main navigation menu, then select "Dashboards".
2.  **Click "Create Dashboard".**
3.  **Give your dashboard a name and description.**
4.  **Drag and drop widgets** from the widget palette onto the design canvas.
5.  **Configure your widgets.** Click on a widget to open the property panel, where you can customize its settings.
6.  **Save your dashboard.**

### 4.2. Widget Types

The Dashboard Designer includes a variety of widget types to help you visualize your data:

*   **Metric Cards:** Display single key performance indicators (KPIs).
*   **Charts:** Line charts, bar charts, pie charts, and more.
*   **Data Tables:** Display tabular data with sorting and filtering.
*   **Geographic Maps:** Visualize data on a map.
*   **Text Widgets:** Add custom text and descriptions to your dashboard.

### 4.3. Unified Dashboard Designer

The Unified Dashboard Designer is an advanced tool that allows you to create complete dashboard solutions with menus and multiple dashboards. This is ideal for creating comprehensive templates that can be applied to multiple studies.

---

## 5. Widget Filtering System

The Widget Filtering System allows you to apply SQL-like filters to your dashboard widgets to focus on specific subsets of data.

### 5.1. Filter Syntax

Filters use standard SQL WHERE clause syntax:

*   **Comparison Operators:** `=`, `!=`, `<`, `<=`, `>`, `>=`
*   **Logical Operators:** `AND`, `OR`, `NOT`
*   **Special Operators:** `IN`, `NOT IN`, `LIKE`, `NOT LIKE`, `BETWEEN`, `IS NULL`, `IS NOT NULL`
*   **Grouping:** Use parentheses `()` to group conditions

### 5.2. Filter Examples

Here are some common filter patterns:

*   **Simple equality:** `AESER = 'Y'`
*   **Multiple conditions:** `AESER = 'Y' AND AETERM IS NOT NULL`
*   **Range filtering:** `AGE BETWEEN 18 AND 65`
*   **List matching:** `COUNTRY IN ('USA', 'UK', 'CANADA')`
*   **Pattern matching:** `AETERM LIKE '%headache%'`
*   **Complex logic:** `(AESER = 'Y' AND AGE >= 65) OR (AESEV IN ('SEVERE', 'LIFE THREATENING'))`

### 5.3. Performance Considerations

*   Filters starting with wildcards (e.g., `LIKE '%pattern'`) may be slower on large datasets
*   Complex filters with many OR conditions may impact performance
*   The system automatically validates filters against the dataset schema before execution
*   Filter execution metrics are tracked for performance monitoring

### 5.4. Filter Validation

Before a filter is applied, the system validates:

*   **Column existence:** All referenced columns must exist in the dataset
*   **Type compatibility:** Values are checked for type compatibility with columns
*   **Syntax correctness:** The SQL expression must be syntactically valid

Validation errors will be displayed, helping you correct the filter expression.

---

## 6. Troubleshooting

### 6.1. Can't Log In

*   **Check your password.** Make sure you're entering the correct password. If you've forgotten it, use the "Forgot password?" link to reset it.
*   **Check your email address.** Make sure you're using the email address that you registered with.
*   **Contact your administrator.** If you're still having trouble, contact your system administrator for assistance.

### 6.2. Study Initialization Failed

*   **Check the error message.** The error message will usually provide a clue as to what went wrong.
*   **Check your data files.** Make sure your data files are in the correct format and that they contain all the required fields.
*   **Retry the initialization.** You can retry the initialization process from the point where it failed.

### 6.3. Dashboard Not Loading

*   **Check your internet connection.** Make sure you have a stable internet connection.
*   **Clear your browser cache.** Sometimes, clearing your browser cache can resolve loading issues.
*   **Contact your administrator.** If the dashboard is still not loading, contact your system administrator.