"""Demo of notification generation with LLM"""

import random
import time
from datetime import datetime
from src.core.scroll_breaker import ScrollBreakerAI
from src.config import ACTIVE_LLM, LLMProvider

def demo_enhanced_system():
    """Demonstrate the enhanced system with LLM and database"""
    
    print("=== Enhanced Scroll Breaker AI Demo ===\n")
    
    # Initialize the system with active LLM provider
    ai_system = ScrollBreakerAI(llm_provider=ACTIVE_LLM)
    print(f"System initialized with {ACTIVE_LLM} LLM provider")
    print("Database location:", ai_system.db.db_path)
    
    # Show initial stats
    stats = ai_system.get_system_stats()
    print(f"Active tasks: {stats['active_tasks']}")
    print(f"Categories: {list(stats['category_performance'].keys())}")
    print()
    
    # Generate several notifications in different contexts
    contexts = [
        {'scrolling_time': 45, 'hour': 10, 'day_of_week': 1},  # Morning
        {'scrolling_time': 120, 'hour': 15, 'day_of_week': 2},  # Afternoon
        {'scrolling_time': 90, 'hour': 20, 'day_of_week': 3}   # Evening
    ]
    
    for i, context in enumerate(contexts):
        print(f"--- Generating Notification {i+1} ---")
        print(f"Context: {context}")
        
        # Generate notification
        notification = ai_system.generate_smart_notification(context)
        
        if notification:
            print(f"✅ Generated notification:")
            print(f"   Hook: {notification.hook_message}")
            print(f"   Next Step: {notification.next_step}")
            print(f"   Strategy: {notification.generation_strategy}")
            print(f"   Confidence: {notification.confidence_score:.2f}")
            if notification.expanded_content:
                print(f"   Expanded: {notification.expanded_content}")
            
            # Simulate user response
            responses = ['acted', 'clicked', 'dismissed', 'expanded']
            simulated_action = random.choice(responses)
            simulated_time = random.uniform(2.0, 15.0)
            
            result = ai_system.process_user_response(
                notification.notification_id, 
                simulated_action,
                simulated_time,
                {'was_expanded': simulated_action == 'expanded'}
            )
            
            print(f"   User Response: {simulated_action} (took {simulated_time:.1f}s)")
            print(f"   Result: {result['message']}")
            print()
        
        time.sleep(1)  # Pause between notifications
    
    # Show final stats
    final_stats = ai_system.get_system_stats()
    print("\n=== Final System Stats ===")
    print(f"Total Notifications: {final_stats['total_notifications']}")
    print(f"Response Rate: {final_stats['response_rate']:.1%}")
    print("\nCategory Performance:")
    for category, perf in final_stats['category_performance'].items():
        if perf['total_responses'] > 0:
            print(f"- {category}: {perf['success_rate']:.1%} success rate" +
                  f" ({perf['total_responses']} responses)")

def test_notification_generation():
    """Test generating notifications with different contexts"""
    
    # Initialize the system
    ai_system = ScrollBreakerAI(llm_provider=ACTIVE_LLM)
    
    # Test contexts
    test_contexts = [
        {
            'scrolling_time': 45,
            'hour': 10,
            'day_of_week': 1,
            'description': "Morning scrolling break"
        },
        {
            'scrolling_time': 120,
            'hour': 15,
            'day_of_week': 2,
            'description': "Long afternoon session"
        }
    ]
    
    print("\n=== Testing Notification Generation ===")
    print(f"Active LLM Provider: {ACTIVE_LLM}")
    
    for context in test_contexts:
        print(f"\nTesting context: {context['description']}")
        notification = ai_system.generate_smart_notification(context)
        
        if notification:
            print("\nGenerated Notification:")
            print(f"Hook: {notification.hook_message}")
            print(f"Next Step: {notification.next_step}")
            if notification.expanded_content:
                print(f"Expanded: {notification.expanded_content}")
            print(f"Generation Strategy: {notification.generation_strategy}")
            print(f"Confidence Score: {notification.confidence_score:.2f}")
        else:
            print("Failed to generate notification")
        
        print("-" * 50)

if __name__ == "__main__":
    demo_enhanced_system()
    test_notification_generation()
