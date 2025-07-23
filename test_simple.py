import time
from src.gencommit import format_diff, generate_commit_message

class FakeGitDiffs:
    @staticmethod
    def small_python_change():
        return """diff --git a/src/main.py b/src/main.py
index 1234567..abcdefg 100644
--- a/src/main.py
+++ b/src/main.py
@@ -10,7 +10,8 @@ def calculate_total(items):
     total = 0
     for item in items:
-        total += item.price
+        # Apply discount if available
+        total += item.price * (1 - item.discount)
     return total"""

    @staticmethod
    def medium_javascript_refactor():
        return """diff --git a/frontend/components/UserProfile.js b/frontend/components/UserProfile.js
index abcd123..efgh456 100644
--- a/frontend/components/UserProfile.js
+++ b/frontend/components/UserProfile.js
@@ -1,15 +1,22 @@
-import React from 'react';
+import React, { useState, useEffect } from 'react';
+import { fetchUserData } from '../api/users';
 
-const UserProfile = ({ user }) => {
+const UserProfile = ({ userId }) => {
+  const [user, setUser] = useState(null);
+  const [loading, setLoading] = useState(true);
+
+  useEffect(() => {
+    const loadUser = async () => {
+      try {
+        const userData = await fetchUserData(userId);
+        setUser(userData);
+      } catch (error) {
+        console.error('Failed to load user:', error);
+      } finally {
+        setLoading(false);
+      }
+    };
+    loadUser();
+  }, [userId]);"""

    @staticmethod
    def large_database_migration():
        return """diff --git a/migrations/001_add_user_preferences.sql b/migrations/001_add_user_preferences.sql
new file mode 100644
index 0000000..1234567
--- /dev/null
+++ b/migrations/001_add_user_preferences.sql
@@ -0,0 +1,45 @@
+-- Add user preferences table
+CREATE TABLE user_preferences (
+    id SERIAL PRIMARY KEY,
+    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
+    theme VARCHAR(20) DEFAULT 'light',
+    language VARCHAR(10) DEFAULT 'en',
+    timezone VARCHAR(50) DEFAULT 'UTC',
+    email_notifications BOOLEAN DEFAULT true,
+    push_notifications BOOLEAN DEFAULT true,
+    marketing_emails BOOLEAN DEFAULT false,
+    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
+    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
+);
+
+-- Add indexes for better query performance
+CREATE INDEX idx_user_preferences_user_id ON user_preferences(user_id);
+CREATE INDEX idx_user_preferences_theme ON user_preferences(theme);
+CREATE INDEX idx_user_preferences_language ON user_preferences(language);"""

    @staticmethod
    def config_file_changes():
        return """diff --git a/config/database.yml b/config/database.yml
index abc123..def456 100644
--- a/config/database.yml
+++ b/config/database.yml
@@ -1,8 +1,12 @@
 development:
   adapter: postgresql
   encoding: unicode
-  database: myapp_development
+  database: myapp_dev
   pool: 5
-  username: postgres
-  password: password
+  username: <%= ENV['DB_USERNAME'] %>
+  password: <%= ENV['DB_PASSWORD'] %>
   host: localhost
+  port: 5432
+  timeout: 5000"""

    @staticmethod
    def multi_file_feature():
        return """diff --git a/src/api/auth.py b/src/api/auth.py
new file mode 100644
index 0000000..1234567
--- /dev/null
+++ b/src/api/auth.py
@@ -0,0 +1,25 @@
+from flask import Blueprint, request, jsonify
+from werkzeug.security import check_password_hash
+from models.user import User
+from utils.jwt_handler import generate_token
+
+auth_bp = Blueprint('auth', __name__)
+
+@auth_bp.route('/login', methods=['POST'])
+def login():
+    data = request.get_json()
+    email = data.get('email')
+    password = data.get('password')
+    
+    user = User.query.filter_by(email=email).first()
+    
+    if user and check_password_hash(user.password_hash, password):
+        token = generate_token(user.id)
+        return jsonify({
+            'success': True,
+            'token': token,
+            'user': user.to_dict()
+        })
+    
+    return jsonify({'success': False, 'message': 'Invalid credentials'}), 401"""

def test_all_diffs():
    tests = [
        ("Small Python Change", FakeGitDiffs.small_python_change()),
        ("Medium JS Refactor", FakeGitDiffs.medium_javascript_refactor()),
        ("Large DB Migration", FakeGitDiffs.large_database_migration()),
        ("Config File Changes", FakeGitDiffs.config_file_changes()),
        ("Multi-file Feature", FakeGitDiffs.multi_file_feature()),
    ]
    
    for test_name, diff_content in tests:
        print(f"\n{'='*60}")
        print(f"TEST: {test_name}")
        print('='*60)
        
        try:
            formatted_diff = format_diff(diff_content)
            
            start_time = time.time()
            result = generate_commit_message(formatted_diff)
            duration = time.time() - start_time
            
            print(f"DURATION: {duration:.2f}s")
            print(f"\nTHINKING: {result.thinking}")
            print(f"\nCOMMIT MESSAGE: {result.commit_message}")
            print(f"\nDESCRIPTION: {result.commit_description}")
            
        except Exception as e:
            print(f"ERROR: {e}")

if __name__ == "__main__":
    test_all_diffs()