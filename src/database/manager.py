import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List
from src.models.models import User, Task, GeneratedNotification, NotificationResponse

class DatabaseManager:
    """Handles all database operations"""
    
    def __init__(self, db_path: str = "scroll_breaker.db"):
        self.db_path = db_path
        self.init_database()
        self.seed_initial_data()
    
    def init_database(self):
        """Initialize database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                preferences TEXT DEFAULT '{}'
            )
        ''')
        
        # Tasks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                importance INTEGER NOT NULL CHECK (importance >= 1 AND importance <= 10),
                notes TEXT DEFAULT '',
                task_type TEXT NOT NULL CHECK (task_type IN ('simple', 'complex')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Generated notifications table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS generated_notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                notification_id TEXT UNIQUE NOT NULL,
                task_id INTEGER NOT NULL,
                hook_message TEXT NOT NULL,
                expanded_content TEXT,
                next_step TEXT NOT NULL,
                confidence_score REAL NOT NULL,
                generation_strategy TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                llm_prompt_used TEXT,
                llm_response_raw TEXT,
                FOREIGN KEY (task_id) REFERENCES tasks (id)
            )
        ''')
        
        # Notification responses table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notification_responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                notification_id TEXT NOT NULL,
                task_id INTEGER NOT NULL,
                user_action TEXT NOT NULL,
                response_time REAL NOT NULL,
                was_expanded BOOLEAN NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                context TEXT DEFAULT '{}',
                FOREIGN KEY (task_id) REFERENCES tasks (id)
            )
        ''')
        
        # Task engagement metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS task_engagement (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                last_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                consecutive_dismissals INTEGER DEFAULT 0,
                last_success TIMESTAMP,
                engagement_score REAL DEFAULT 1.0,
                cooldown_until TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES tasks (id)
            )
        ''')
        
        conn.commit()
        conn.close()

    def seed_initial_data(self):
        """Seed database with initial user and tasks if empty"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if we already have data
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] > 0:
            conn.close()
            return
        
        # Create initial user
        cursor.execute('''
            INSERT INTO users (username, email, preferences)
            VALUES (?, ?, ?)
        ''', ("john_doe", "john@example.com", json.dumps({
            "notification_frequency": "medium",
            "preferred_times": [9, 14, 19],
            "categories_enabled": ["learning", "work", "health", "personal"]
        })))
        
        user_id = cursor.lastrowid
        
        # Create initial tasks
        initial_tasks = [
            {
                "title": "Learn Computer Vision with OpenCV",
                "category": "learning",
                "importance": 9,
                "notes": "Just started learning basic concepts like image processing and feature detection.",
                "task_type": "complex"
            },
            {
                "title": "Master React Hooks and Context API",
                "category": "learning", 
                "importance": 8,
                "notes": "Halfway through - understanding useEffect and useState well.",
                "task_type": "complex"
            },
            # Add more tasks as needed
        ]
        
        for task_data in initial_tasks:
            cursor.execute('''
                INSERT INTO tasks (user_id, title, category, importance, notes, task_type)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, task_data["title"], task_data["category"], 
                  task_data["importance"], task_data["notes"], task_data["task_type"]))
        
        conn.commit()
        conn.close()
        print(f"Seeded database with 1 user and {len(initial_tasks)} tasks")

    def get_user_tasks(self, user_id: int) -> List[Task]:
        """Get all active tasks for a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, user_id, title, category, importance, notes, task_type,
                   created_at, updated_at, is_active
            FROM tasks 
            WHERE user_id = ? AND is_active = 1
            ORDER BY importance DESC, created_at DESC
        ''', (user_id,))
        
        tasks = []
        for row in cursor.fetchall():
            tasks.append(Task(
                id=row[0], user_id=row[1], title=row[2], category=row[3],
                importance=row[4], notes=row[5], task_type=row[6],
                created_at=datetime.fromisoformat(row[7]),
                updated_at=datetime.fromisoformat(row[8]),
                is_active=bool(row[9])
            ))
        
        conn.close()
        return tasks

    def save_notification(self, notification: GeneratedNotification) -> int:
        """Save generated notification to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO generated_notifications 
            (notification_id, task_id, hook_message, expanded_content, next_step,
             confidence_score, generation_strategy, llm_prompt_used, llm_response_raw)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (notification.notification_id, notification.task_id, notification.hook_message,
              notification.expanded_content, notification.next_step, notification.confidence_score,
              notification.generation_strategy, notification.llm_prompt_used,
              notification.llm_response_raw))
        
        notification_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return notification_id

    def save_response(self, response: NotificationResponse) -> int:
        """Save user response to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO notification_responses 
            (notification_id, task_id, user_action, response_time, was_expanded, context)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (response.notification_id, response.task_id, response.user_action,
              response.response_time, response.was_expanded, json.dumps(response.context)))
        
        response_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return response_id

    def update_task_engagement(self, task_id: int, user_action: str) -> None:
        """Update task engagement metrics based on user action"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get current engagement data
        cursor.execute('''
            SELECT id, consecutive_dismissals, engagement_score 
            FROM task_engagement 
            WHERE task_id = ?
        ''', (task_id,))
        row = cursor.fetchone()
        
        now = datetime.now()
        
        if not row:
            # Create initial engagement record
            cursor.execute('''
                INSERT INTO task_engagement (task_id, last_interaction, engagement_score)
                VALUES (?, ?, 1.0)
            ''', (task_id, now))
            engagement_id = cursor.lastrowid
            consecutive_dismissals = 0
            engagement_score = 1.0
        else:
            engagement_id = row[0]
            consecutive_dismissals = row[1]
            engagement_score = row[2]

        # Update metrics based on action
        if user_action == 'dismissed':
            consecutive_dismissals += 1
            engagement_score *= 0.8  # Reduce score by 20%
            
            # Set cooldown period based on consecutive dismissals
            cooldown_minutes = min(30 * consecutive_dismissals, 240)  # Max 4 hours
            cooldown_until = now + timedelta(minutes=cooldown_minutes)
        else:
            consecutive_dismissals = 0
            engagement_score = min(engagement_score * 1.2, 1.0)  # Increase score up to max 1.0
            cooldown_until = None

        # Update engagement record
        cursor.execute('''
            UPDATE task_engagement 
            SET last_interaction = ?,
                consecutive_dismissals = ?,
                last_success = ?,
                engagement_score = ?,
                cooldown_until = ?
            WHERE id = ?
        ''', (now, consecutive_dismissals,
              now if user_action in ['acted', 'expanded'] else None,
              engagement_score, cooldown_until, engagement_id))

        conn.commit()
        conn.close()

    def get_task_engagement(self, task_id: int) -> Dict:
        """Get engagement metrics for a task"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT consecutive_dismissals, engagement_score, cooldown_until
            FROM task_engagement
            WHERE task_id = ?
        ''', (task_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return {
                'consecutive_dismissals': 0,
                'engagement_score': 1.0,
                'is_cooling_down': False
            }
            
        return {
            'consecutive_dismissals': row[0],
            'engagement_score': row[1],
            'is_cooling_down': (
                datetime.fromisoformat(row[2]) > datetime.now()
                if row[2] else False
            )
        }

    def get_task_performance(self, task_id: int) -> Dict:
        """Get performance metrics for a specific task"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_action, COUNT(*) as count
            FROM notification_responses
            WHERE task_id = ?
            GROUP BY user_action
        ''', (task_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        performance = {'total': 0, 'positive': 0, 'negative': 0}
        for action, count in results:
            performance['total'] += count
            if action in ['acted', 'expanded', 'clicked']:
                performance['positive'] += count
            elif action == 'dismissed':
                performance['negative'] += count
        
        return performance

    def get_system_stats(self, user_id: int) -> Dict:
        """Get comprehensive system statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Basic counts
        cursor.execute("""
            SELECT COUNT(*) FROM tasks WHERE user_id = ? AND is_active = 1
        """, (user_id,))
        active_tasks = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM generated_notifications")
        total_notifications = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM notification_responses")
        total_responses = cursor.fetchone()[0]
        
        # Performance by category
        cursor.execute('''
            SELECT t.category, 
                   COUNT(nr.id) as total_responses,
                   SUM(CASE WHEN nr.user_action IN ('acted', 'expanded', 'clicked') 
                           THEN 1 ELSE 0 END) as positive_responses
            FROM tasks t
            LEFT JOIN notification_responses nr ON t.id = nr.task_id
            WHERE t.user_id = ?
            GROUP BY t.category
        ''', (user_id,))
        
        category_performance = {}
        for row in cursor.fetchall():
            category, total, positive = row
            success_rate = (positive / total) if total > 0 else 0
            category_performance[category] = {
                'total_responses': total,
                'success_rate': success_rate
            }
        
        conn.close()
        
        return {
            'active_tasks': active_tasks,
            'total_notifications': total_notifications,
            'total_responses': total_responses,
            'category_performance': category_performance,
            'response_rate': (total_responses / total_notifications) 
                           if total_notifications > 0 else 0
        }

    def get_task_id_for_notification(self, notification_id: str) -> int:
        """Get the task ID associated with a notification"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT task_id
            FROM generated_notifications
            WHERE notification_id = ?
        ''', (notification_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        return row[0] if row else 0

    def _get_cooldown_remaining(self, task_id: int) -> float:
        """Get remaining cooldown time in minutes"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT cooldown_until
            FROM task_engagement
            WHERE task_id = ?
        ''', (task_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row or not row[0]:
            return 0
            
        cooldown = datetime.fromisoformat(row[0])
        remaining = (cooldown - datetime.now()).total_seconds() / 60
        return max(0, remaining)
