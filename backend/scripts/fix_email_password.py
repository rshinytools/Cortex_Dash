# ABOUTME: Fix email password by prompting user to enter it
# ABOUTME: Simple script to ensure password is properly saved

print("""
============================================================
EMAIL PASSWORD FIX
============================================================

The SMTP authentication is failing because the password is not
properly stored in the database.

Please do the following:

1. Go to http://localhost:3000/admin/email-settings
2. Enter your GoDaddy SMTP password in the password field
3. Click "Update Settings"
4. Come back here and run the test

The password for admin@sagarmatha.ai needs to be the actual
email account password from GoDaddy.

============================================================
""")