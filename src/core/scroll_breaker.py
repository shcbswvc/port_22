import random
from datetime import datetime
from typing import Dict, List, Optional

from src.database.manager import DatabaseManager
from src.notifications.generator import LLMNotificationGenerator
from src.models.models import Task, GeneratedNotification, NotificationResponse

class ScrollBreakerAI:
    """Main AI system with database integration and LLM support"""
    
    def __init__(self, db_path: str = "scroll_breaker.db", llm_provider: str = None):
        """Initialize the scroll breaker AI system"""
        self.db = DatabaseManager(db_path)
        self.llm_generator = LLMNotificationGenerator(llm_provider=llm_provider)
        self.user_id = 1  # Default user for demo
    
    def generate_smart_notification(self, context: Dict = None) -> Optional[GeneratedNotification]:
        """Generate a smart notification based on current context"""
        
        if context is None:
            context = {
                'scrolling_time': random.randint(20, 120),
                'hour': datetime.now().hour,
                'day_of_week': datetime.now().weekday()
            }
        
        # Get user's active tasks
        tasks = self.db.get_user_tasks(self.user_id)
        if not tasks:
            return None
        
        # Select best task based on context and scoring
        selected_task = self._select_best_task(tasks, context)
        
        # Get task performance for LLM context
        task_performance = self.db.get_task_performance(selected_task.id)
        
        # Generate notification using LLM
        notification = self.llm_generator.generate_notification(
            selected_task, context, task_performance
        )
        
        # Save to database
        self.db.save_notification(notification)
        
        return notification
    def _select_best_task(self, tasks: List[Task], context: Dict) -> Task:
        """Select the best task based on importance, context, engagement and performance"""
        scored_tasks = []
        
        for task in tasks:
            # Get engagement metrics
            engagement = self.db.get_task_engagement(task.id)
            
            # Skip tasks in cooldown
            if engagement['is_cooling_down']:
                continue
                
            # Base score from importance and engagement
            score = (task.importance / 10.0) * engagement['engagement_score']
            
            # Context adjustments
            hour = context.get('hour', 12)
            if task.category == 'health' and 6 <= hour <= 10:
                score += 0.2
            elif task.category == 'work' and 9 <= hour <= 17:
                score += 0.15
            elif task.category == 'personal' and 18 <= hour <= 21:
                score += 0.1
            elif task.category == 'learning' and (19 <= hour <= 22 or 14 <= hour <= 16):
                score += 0.1
            
            # Get performance data
            performance = self.db.get_task_performance(task.id)
            if performance['total'] > 0:
                success_rate = performance['positive'] / performance['total']
                # Boost tasks that historically perform well
                score += (success_rate - 0.5) * 0.2
                
                # Reduce score based on consecutive dismissals
                score *= max(0.2, 1 - (engagement['consecutive_dismissals'] * 0.2))
            
            scored_tasks.append((task, score))
        
        if not scored_tasks:
            # If all tasks are in cooldown, get the one with shortest remaining cooldown
            return min(tasks, key=lambda t: self.db._get_cooldown_remaining(t.id))
        
        # Sort by score
        scored_tasks.sort(key=lambda x: x[1], reverse=True)
        
        # Adaptive exploration rate - more exploration with poor engagement
        avg_engagement = sum(self.db.get_task_engagement(t.id)['engagement_score'] 
                           for t in tasks) / len(tasks)
        explore_rate = 0.3 + (1 - avg_engagement) * 0.2  # 30-50% exploration based on engagement
        
        if random.random() < explore_rate:
            # Weighted random selection from all tasks
            tasks_only, scores = zip(*scored_tasks)
            weights = [max(0.1, score) for score in scores]
            return random.choices(tasks_only, weights=weights)[0]
        else:
            return scored_tasks[0][0]
    def process_user_response(self, notification_id: str, user_action: str, 
                            response_time: float, context: Dict = None) -> Dict:
        """Process user response and update engagement metrics"""
        
        if context is None:
            context = {}
        
        # Create and save response
        response = NotificationResponse(
            id=None,
            notification_id=notification_id,
            task_id=0,  # Will be set by database manager
            user_action=user_action,
            response_time=response_time,
            was_expanded=context.get('was_expanded', False),
            timestamp=datetime.now(),
            context=context
        )
        
        # Save response and get task_id
        response_id = self.db.save_response(response)
        task_id = self.db.get_task_id_for_notification(notification_id)
        
        # Update engagement metrics
        self.db.update_task_engagement(task_id, user_action)
        
        # Get updated metrics
        updated_performance = self.db.get_task_performance(task_id)
        updated_engagement = self.db.get_task_engagement(task_id)
        
        return {
            'status': 'success',
            'updated_performance': updated_performance,
            'engagement_metrics': updated_engagement,
            'message': f'Response recorded: {user_action}'
        }
    
    def get_system_stats(self) -> Dict:
        """Get comprehensive system statistics"""
        return self.db.get_system_stats(self.user_id)
