"""LLM-powered notification generator with fallback templates"""
import random
import json
from datetime import datetime
from typing import Dict, Optional
import requests
import google.generativeai as genai

from src.models.models import Task, GeneratedNotification
from src.notifications.templates import FALLBACK_TEMPLATES
from src.config import (
    GEMINI_API_KEY, OLLAMA_HOST, OLLAMA_MODEL,
    ACTIVE_LLM, LLMProvider
)

class LLMNotificationGenerator:
    """LLM-powered notification generator with fallback templates"""
    
    def __init__(self, llm_provider: str = None, api_key: str = None):
        """Initialize the notification generator"""
        self.provider = llm_provider or ACTIVE_LLM
        self.api_key = api_key or GEMINI_API_KEY
        self.model = None
        self.ollama_url = f"{OLLAMA_HOST}/api/generate"
        
        if self.provider == LLMProvider.GEMINI.value:
            self._init_gemini()
        elif self.provider == LLMProvider.LOCAL.value:
            self._test_ollama_connection()
        else:
            print("Using fallback templates only.")
        
        self.fallback_templates = FALLBACK_TEMPLATES
    
    def _init_gemini(self):
        """Initialize Gemini API"""
        if not self.api_key:
            print("No Gemini API key provided. Using fallback templates.")
            return
        
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-pro')
            response = self.model.generate_content("Hello!")
            print(f"Successfully initialized Gemini API")
        except Exception as e:
            print(f"Error initializing Gemini API: {e}")
            self.model = None
            print("Falling back to templates.")
    
    def _test_ollama_connection(self):
        """Test connection to Ollama server"""
        try:
            # Test with a simple prompt
            response = requests.post(
                self.ollama_url,
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": "Hello!",
                    "stream": False,
                    "options": {
                        "temperature": 0.7,  # for consistent responses
                        "num_predict": 50    # limit initial response length
                    }
                }
            )
            response.raise_for_status()
            print(f"Successfully connected to Ollama server using model: {OLLAMA_MODEL}")
            self.model = True
        except requests.RequestException as e:
            print(f"Error connecting to Ollama server: {e}")
            print("Make sure Ollama is running and the model is pulled.")
            self.model = None
            print("Falling back to templates.")
    
    def _generate_with_ollama(self, prompt: str) -> str:
        """Generate text using Ollama"""
        try:
            response = requests.post(
                self.ollama_url,
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,    # for more focused responses
                        "top_p": 0.9,         # slightly increased for better creativity
                        "top_k": 40,          # keep top 40 tokens
                        "num_predict": 200,    # limit response length
                        "stop": ["}"],        # stop at the end of JSON
                        "repeat_penalty": 1.1  # reduce repetition
                    }
                }
            )
            response.raise_for_status()
            return response.json()["response"]
        except Exception as e:
            print(f"Error generating with Ollama: {e}")
            raise    
    def generate_notification(self, task: Task, context: Dict, 
                            user_performance: Dict = None) -> GeneratedNotification:
        """Generate contextual notification using LLM or fallback.
        
        Args:
            task: The task to generate notification for
            context: Dictionary containing contextual information like time, scrolling_time, etc.
            user_performance: Optional dict containing user's past performance metrics
            
        Returns:
            GeneratedNotification object with the generated notification content
        """
        # Input validation and normalization
        if not isinstance(task, Task):
            print("Warning: Invalid task object provided")
            return self._generate_fallback_notification(task, context or {})
            
        if not hasattr(task, 'id') or not task.id:
            print("Warning: Task missing ID")
            task.id = 0
            
        if not context:
            context = {}
            
        # Determine notification type and generate
        try:
            task_type = getattr(task, 'task_type', 'simple')
            if task_type == 'simple':
                return self._generate_simple_notification(task, context)
            else:
                return self._generate_complex_notification(task, context, user_performance)
        except Exception as e:
            print(f"Error generating notification: {str(e)}")
            return self._generate_fallback_notification(task, context)
    
    def _generate_simple_notification(self, task: Task, context: Dict) -> GeneratedNotification:
        """Generate simple notification with templates"""
        templates = self.fallback_templates['simple'].get(task.category, 
                                                        self.fallback_templates['simple']['work'])
        hook_message = random.choice(templates)
        next_step = f"Ready to {task.title.lower()}?"
        
        return GeneratedNotification(
            id=None,
            notification_id=f"notif_{task.id}_{int(datetime.now().timestamp())}",
            task_id=task.id,
            hook_message=hook_message,
            expanded_content=None,
            next_step=next_step,
            confidence_score=0.7,
            generation_strategy="simple_template",
            timestamp=datetime.now()
        )
    
    def _generate_notification_id(self, task_id: int) -> str:
        """Generate a unique notification ID"""
        timestamp = int(datetime.now().timestamp() * 1000)  # millisecond precision
        random_suffix = ''.join([str(random.randint(0, 9)) for _ in range(4)])
        return f"notif_{task_id}_{timestamp}_{random_suffix}"

    def _generate_complex_notification(self, task: Task, context: Dict, 
                                    user_performance: Dict = None) -> GeneratedNotification:
        """Generate complex notification using LLM"""
        
        if not self.model:
            return self._generate_fallback_notification(task, context)
        
        try:
            # Prepare context for LLM
            prompt = self._build_llm_prompt(task, context, user_performance)
            
            if self.provider == LLMProvider.GEMINI.value:
                return self._generate_with_gemini(task, prompt)
            elif self.provider == LLMProvider.LOCAL.value:
                return self._generate_with_local(task, prompt)
            else:
                return self._generate_fallback_notification(task, context)
                
        except Exception as e:
            print(f"Error during LLM generation: {e}")
            return self._generate_fallback_notification(task, context)
    
    def _generate_with_gemini(self, task: Task, prompt: str) -> GeneratedNotification:
        """Generate notification using Gemini"""
        try:
            response = self.model.generate_content(
                prompt,
                generation_config={
                    'temperature': 0.7,
                    'top_p': 0.8,
                    'top_k': 40,
                    'max_output_tokens': 150,
                }
            )
            llm_response = response.text
            
        except Exception as e:
            print(f"Gemini generation error: {e}")
            raise
            
        return self._create_notification(task, prompt, llm_response, "gemini_generated")
    
    def _generate_with_local(self, task: Task, prompt: str) -> GeneratedNotification:
        """Generate notification using local Ollama"""
        try:
            llm_response = self._generate_with_ollama(prompt)
            return self._create_notification(task, prompt, llm_response, "ollama_generated")
            
        except Exception as e:
            print(f"Ollama generation error: {e}")
            raise

    def _parse_llm_response(self, response_text: str) -> dict:
        """Parse LLM response text into notification data"""
        try:
            # Clean up the text - keep only the JSON part
            json_text = response_text
            
            # If response starts with text before JSON, find the first {
            if not response_text.strip().startswith('{'):
                start_idx = response_text.find('{')
                if start_idx != -1:
                    json_text = response_text[start_idx:]
            
            # If there's text after JSON, find the last }
            end_idx = json_text.rfind('}')
            if end_idx != -1:
                json_text = json_text[:end_idx + 1]
            
            # Parse the cleaned JSON
            data = json.loads(json_text)
            
            # Extract fields, handling various JSON structures
            notification_data = {
                'hook': data.get('hook', '').strip('"'),
                'next_step': data.get('next_step', '').strip('"'),
                'expanded_content': data.get('expanded_content', '').strip('"'),
                'confidence': float(data.get('confidence', 0.7))
            }
            
            return notification_data
            
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error parsing LLM response: {e}")
            print(f"Raw response: {response_text}")
            
            # Extract information from raw text as fallback
            lines = response_text.split('\n')
            return {
                'hook': next((l.split(':', 1)[1].strip(' "',) 
                            for l in lines if '"hook"' in l.lower()), 
                            "Time to focus! 🎯"),
                'next_step': next((l.split(':', 1)[1].strip(' "',) 
                                 for l in lines if '"next_step"' in l.lower()), 
                                 "Ready to start?"),
                'confidence': 0.7
            }

    def _create_notification(self, task: Task, prompt: str, 
                           llm_response: str, strategy: str) -> GeneratedNotification:
        """Create notification from LLM response"""
        # Parse the response
        notification_data = self._parse_llm_response(llm_response)
        
        # Validate lengths
        if len(notification_data['hook']) > 100:
            notification_data['hook'] = notification_data['hook'][:97] + "..."
        if len(notification_data.get('next_step', '')) > 50:
            notification_data['next_step'] = notification_data['next_step'][:47] + "..."
        
        return GeneratedNotification(
            id=None,
            notification_id=self._generate_notification_id(task.id),
            task_id=task.id,
            hook_message=notification_data['hook'],
            expanded_content=notification_data.get('expanded_content'),
            next_step=notification_data['next_step'],
            confidence_score=notification_data['confidence'],
            generation_strategy=strategy,
            timestamp=datetime.now(),
            llm_prompt_used=prompt,
            llm_response_raw=llm_response
        )

    def _build_llm_prompt(self, task: Task, context: Dict, user_performance: Dict = None) -> str:
        """Build prompt for LLM"""
        
        # Analyze task progress from notes
        progress_level = self._analyze_progress_level(task.notes)
        
        # Build performance context
        performance_context = ""
        if user_performance and user_performance['total'] > 0:
            success_rate = user_performance['positive'] / user_performance['total']
            performance_context = f"\nUser typically responds positively to notifications about this task {success_rate:.1%} of the time."
        
        # Current time context
        hour = context.get('hour', datetime.now().hour)
        time_context = "morning" if 6 <= hour <= 11 else "afternoon" if 12 <= hour <= 17 else "evening"
        
        prompt = f"""You are a notification generator for a focus app. Generate a compelling notification to help break scrolling habits.

CONTEXT:
Task: {task.title}
Category: {task.category}
Importance: {task.importance}/10
Progress Level: {progress_level}
User's Notes: "{task.notes}"
Time of day: {time_context}
Scrolling duration: {context.get('scrolling_time', 30)} seconds{performance_context}

INSTRUCTIONS:
1. Generate a notification that's relevant to the user's progress level
2. Connect the task to real-world applications or interesting facts
3. Make it personally relevant and timely
4. Use emojis sparingly

RESPONSE FORMAT:
Return ONLY a JSON object with these fields:
{{
  "hook": "Brief attention-grabbing message (max 100 chars)",
  "next_step": "Clear call-to-action (max 50 chars)",
  "expanded_content": "Optional detailed motivation (max 300 chars)",
  "confidence": 0.85
}}

EXAMPLE RESPONSE:
{{
  "hook": "Ready to level up your coding skills? 🚀",
  "next_step": "Complete the next tutorial chapter",
  "expanded_content": "Did you know programmers spend 50% of their time debugging? Master these skills now to save time later!",
  "confidence": 0.85
}}

YOUR RESPONSE (JSON only, no other text):
"""
        
        return prompt

    def _analyze_progress_level(self, notes: str) -> str:
        """Analyze progress level from task notes"""
        notes_lower = notes.lower()
        
        beginner_keywords = ['just started', 'beginning', 'new to', 'learning basics']
        intermediate_keywords = ['halfway', 'currently', 'working on', 'understanding']
        advanced_keywords = ['almost done', 'finishing', 'advanced', 'mastering']
        
        for keyword in advanced_keywords:
            if keyword in notes_lower:
                return 'advanced'
        
        for keyword in intermediate_keywords:
            if keyword in notes_lower:
                return 'intermediate'
        
        for keyword in beginner_keywords:
            if keyword in notes_lower:
                return 'beginner'
        
        return 'beginner'

    def _generate_fallback_notification(self, task: Task, context: Dict) -> GeneratedNotification:
        """Generate fallback notification when LLM is not available"""
        templates = self.fallback_templates['simple'].get(task.category, 
                                                    self.fallback_templates['simple']['work'])
        hook_message = random.choice(templates)
        next_step = f"Ready to work on {task.title}?"
        
        return GeneratedNotification(
            id=None,
            notification_id=self._generate_notification_id(task.id),
            task_id=task.id,
            hook_message=hook_message,
            expanded_content=f"You've been working on: {task.title}. {task.notes[:100]}...",
            next_step=next_step,
            confidence_score=0.6,
            generation_strategy="fallback_template",
            timestamp=datetime.now()
        )
