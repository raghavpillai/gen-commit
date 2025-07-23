import time

from src.gencommit import CommitMessage, format_diff, generate_commit_message


class FakeGitDiffs:
    """Collection of fake git diffs for testing gencommit performance."""

    @staticmethod
    def small_python_change() -> str:
        """Small Python file modification."""
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
     return total
 
 def process_order(order):"""

    @staticmethod
    def medium_javascript_refactor() -> str:
        """Medium-sized JavaScript refactoring."""
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
+  }, [userId]);
+
+  if (loading) return <div>Loading...</div>;
   return (
     <div className="user-profile">
       <h2>{user.name}</h2>
-      <p>{user.email}</p>
+      <p>Email: {user.email}</p>
+      <p>Joined: {new Date(user.createdAt).toLocaleDateString()}</p>
     </div>
   );
 };"""

    @staticmethod
    def large_database_migration() -> str:
        """Large database migration with multiple tables."""
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
+CREATE INDEX idx_user_preferences_language ON user_preferences(language);
+
+-- Add trigger to update updated_at timestamp
+CREATE OR REPLACE FUNCTION update_updated_at_column()
+RETURNS TRIGGER AS $$
+BEGIN
+    NEW.updated_at = CURRENT_TIMESTAMP;
+    RETURN NEW;
+END;
+$$ language 'plpgsql';
+
+CREATE TRIGGER update_user_preferences_updated_at
+    BEFORE UPDATE ON user_preferences
+    FOR EACH ROW
+    EXECUTE FUNCTION update_updated_at_column();
+
+-- Insert default preferences for existing users
+INSERT INTO user_preferences (user_id)
+SELECT id FROM users WHERE id NOT IN (SELECT user_id FROM user_preferences);
+
+-- Add new columns to users table
+ALTER TABLE users ADD COLUMN last_login_at TIMESTAMP;
+ALTER TABLE users ADD COLUMN login_count INTEGER DEFAULT 0;
+ALTER TABLE users ADD COLUMN is_premium BOOLEAN DEFAULT false;
+
+-- Create index on new columns
+CREATE INDEX idx_users_last_login ON users(last_login_at);
+CREATE INDEX idx_users_is_premium ON users(is_premium);"""

    @staticmethod
    def config_file_changes() -> str:
        """Configuration file updates."""
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
+  timeout: 5000
+  prepared_statements: false
+  advisory_locks: true

diff --git a/config/redis.conf b/config/redis.conf
index 789abc..012def 100644
--- a/config/redis.conf
+++ b/config/redis.conf
@@ -50,10 +50,15 @@ save 900 1
 save 300 10
 save 60 10000
 
-maxmemory 2gb
+maxmemory 4gb
 maxmemory-policy allkeys-lru
+maxmemory-samples 5
 
 # Network
 bind 127.0.0.1
-port 6379
+port <%= ENV['REDIS_PORT'] || 6379 %>
 timeout 0
+tcp-keepalive 300
+tcp-backlog 511
+
+# Security
+requirepass <%= ENV['REDIS_PASSWORD'] %>"""

    @staticmethod
    def multi_file_feature() -> str:
        """Multiple files changed for a new feature."""
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
+    return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

diff --git a/src/models/user.py b/src/models/user.py
index abc123..def456 100644
--- a/src/models/user.py
+++ b/src/models/user.py
@@ -1,4 +1,5 @@
 from sqlalchemy import Column, Integer, String, DateTime, Boolean
+from werkzeug.security import generate_password_hash
 from database import db
 import datetime
 
@@ -8,8 +9,18 @@ class User(db.Model):
     email = Column(String(120), unique=True, nullable=False)
     password_hash = Column(String(128), nullable=False)
     is_active = Column(Boolean, default=True)
+    is_verified = Column(Boolean, default=False)
     created_at = Column(DateTime, default=datetime.datetime.utcnow)
+    last_login = Column(DateTime)
 
     def __repr__(self):
         return f'<User {self.email}>'
+    
+    def set_password(self, password):
+        self.password_hash = generate_password_hash(password)
+    
+    def to_dict(self):
+        return {
+            'id': self.id,
+            'email': self.email,
+            'is_active': self.is_active
+        }

diff --git a/tests/test_auth.py b/tests/test_auth.py
new file mode 100644
index 0000000..7890abc
--- /dev/null
+++ b/tests/test_auth.py
@@ -0,0 +1,20 @@
+import pytest
+from app import create_app
+from models.user import User
+
+@pytest.fixture
+def client():
+    app = create_app('testing')
+    with app.test_client() as client:
+        yield client
+
+def test_login_success(client):
+    # Create test user
+    user = User(email='test@example.com')
+    user.set_password('password123')
+    
+    response = client.post('/api/auth/login', json={
+        'email': 'test@example.com',
+        'password': 'password123'
+    })
+    assert response.status_code == 200"""


def benchmark_generate_commit_message():
    """Benchmark generate_commit_message performance with different diff sizes."""

    test_diffs: list[tuple[str, str]] = [
        ("Small Python Change", FakeGitDiffs.small_python_change()),
        ("Medium JS Refactor", FakeGitDiffs.medium_javascript_refactor()),
        ("Large DB Migration", FakeGitDiffs.large_database_migration()),
        ("Config File Changes", FakeGitDiffs.config_file_changes()),
        ("Multi-file Feature", FakeGitDiffs.multi_file_feature()),
    ]

    for test_name, diff_content in test_diffs:
        print(f"\nTesting: {test_name}")
        print("-" * 40)

        formatted_diff: str = format_diff(diff_content)

        start_time = time.time()
        try:
            commit_message: CommitMessage = generate_commit_message(formatted_diff)
            generation_time = time.time() - start_time

            print(f"Duration: {generation_time:.2f}s")
            print(f"Thinking: {commit_message.thinking}")
            print(f"Commit Message: {commit_message.commit_message}")
            print(f"Description: {commit_message.commit_description}")

        except Exception as e:
            generation_time = time.time() - start_time
            print(f"Duration: {generation_time:.2f}s")
            print(f"Error: {e}")


if __name__ == "__main__":
    try:
        benchmark_generate_commit_message()

        print("\nAll tests completed successfully!")

    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback

        traceback.print_exc()
