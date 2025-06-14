Team port_22: Strategies for Algorithmic Freedom
Authored by Dhruv Mahajan, CM Shaik Abdul Rahim Batcha, and Monisha P
This project, port_22, presents two distinct approaches to mitigate and influence social media algorithms, empowering users to regain control over their digital experience. The first method offers a passive intervention through smart notifications, while the second actively seeks to modify the underlying algorithm through strategic interactions.
Scroll Breaker: A Focus Application for Habit Disruption
Scroll Breaker is a sophisticated focus application designed to interrupt habitual scrolling behavior through intelligently generated, AI-powered notifications. It aims to foster a more mindful and productive digital engagement.
Features:
 * Smart Notification Generation: Leverages advanced Large Language Models (LLMs), including Gemini (cloud-based) or Local Llama via Ollama, to create contextually relevant and timely notifications.
 * Context-Aware Task Selection: Dynamically suggests tasks or activities based on user context and predefined goals, helping redirect attention from endless scrolling.
 * Progress Tracking & Performance Analysis: Monitors user engagement and provides insights into habit-breaking progress, aiding in self-improvement.
 * Fallback Templates: Ensures continuous functionality by providing pre-defined notification templates when LLM services are unavailable.
 * Adaptive Feedback System: Learns from user interactions to refine notification strategies and improve effectiveness over time.
Setup Guide:
 * Clone the Repository:
   git clone https://github.com/shcbswvc/port_22.git
cd port_22

 * Install Dependencies:
   pip install -e .

 * Configure Environment Variables:
   cp .env.example .env
# Edit the .env file with your specific configuration details (e.g., API keys).

 * Local LLM Support (Optional - for Ollama):
   * Install Ollama from its official website: ollama.ai
   * Pull the Llama model required for local operation:
     ollama pull llama3.2:3b

Configuration Options:
Scroll Breaker offers flexible configuration to utilize various LLM providers:
 * Gemini: For cloud-based, high-performance notification generation.
 * Local (Ollama with Llama3.2): For privacy-conscious users preferring on-device LLM processing.
 * None: The application will default to template-based notifications, providing basic functionality without external LLM integration.
Usage:
To run a demonstration of the Scroll Breaker application:
python -m src.demo

Architectural Overview:
The project's structure is modular, facilitating maintainability and scalability:
 * src/core/: Contains the fundamental application logic and core functionalities.
 * src/notifications/: Manages notification generation, templating, and delivery mechanisms.
 * src/database/: Handles data persistence, storage, and retrieval operations.
 * src/models/: Defines the data structures and schemas used throughout the application.
Active Algorithm Modification: A Cautionary Approach
This component explores an active method to influence social media algorithms. The core concept revolves around leveraging an LLM to identify and generate a list of users or accounts relevant to a user's stated interests. Subsequently, the system would programmatically follow these suggested accounts.
The premise is that by strategically following accounts aligned with specific interests, the platform's algorithm, which heavily relies on user interactions, can be influenced to display more relevant content.
However, it is crucial to state a significant caveat: Due to the sophisticated automated detection mechanisms employed by platforms like Instagram, we strongly advise against using this script for active algorithm modification. Automated following activities are highly likely to be flagged, potentially leading to temporary or permanent account restrictions. This method is presented purely for conceptual understanding and experimental exploration.
License:
This project is released under the MIT License.
