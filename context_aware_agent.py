#!/usr/bin/env python3

import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import hashlib
import os
import re
from collections import deque
import logging
import random

# Import LLM integration
try:
    from llm_integration import llm_manager, setup_llm_integration
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    print("Warning: LLM integration not available. Install llm_integration.py for intelligent responses.")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConversationContext:
    def __init__(self, max_history: int = 100):
        self.max_history = max_history
        self.conversation_history = deque(maxlen=max_history)
        self.context_summary = ""
        self.emotional_state = "neutral"
        self.topics = set()
        self.user_preferences = {}
        self.conversation_flow = []
        self.last_interaction = None
        self.interaction_count = 0
        
    def add_message(self, role: str, content: str, timestamp: Optional[datetime] = None):
        """Add a message to conversation history"""
        if timestamp is None:
            timestamp = datetime.now()
            
        message = {
            'role': role,
            'content': content,
            'timestamp': timestamp.isoformat(),
            'message_id': self._generate_message_id(content, timestamp)
        }
        
        self.conversation_history.append(message)
        self.last_interaction = timestamp
        self.interaction_count += 1
        
        # Update context
        self._update_context()
        
    def _generate_message_id(self, content: str, timestamp: datetime) -> str:
        """Generate unique message ID"""
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        timestamp_str = timestamp.strftime('%Y%m%d%H%M%S')
        return f"{timestamp_str}_{content_hash}"
    
    def _update_context(self):
        """Update conversation context and summary"""
        if len(self.conversation_history) < 2:
            return
            
        # Extract topics from recent messages
        recent_messages = list(self.conversation_history)[-10:]
        topics = set()
        
        for message in recent_messages:
            content = message['content'].lower()
            # Simple topic extraction (can be enhanced with NLP)
            words = re.findall(r'\b\w+\b', content)
            for word in words:
                if len(word) > 3:  # Filter out short words
                    topics.add(word)
        
        self.topics = topics
        
        # Generate context summary
        self._generate_summary()
        
        # Analyze emotional state
        self._analyze_emotional_state()
        
        # Track conversation flow
        self._track_conversation_flow()
    
    def _generate_summary(self):
        """Generate a summary of recent conversation context"""
        if len(self.conversation_history) < 3:
            self.context_summary = "New conversation started"
            return
            
        recent_messages = list(self.conversation_history)[-5:]
        summary_parts = []
        
        for message in recent_messages:
            role = message['role']
            content = message['content'][:100]  # Truncate long messages
            summary_parts.append(f"{role}: {content}")
        
        self.context_summary = " | ".join(summary_parts)
    
    def _analyze_emotional_state(self):
        """Analyze emotional state from recent messages"""
        if len(self.conversation_history) < 2:
            return
            
        recent_content = " ".join([
            msg['content'].lower() for msg in list(self.conversation_history)[-3:]
        ])
        
        # Simple emotion detection (can be enhanced with sentiment analysis)
        positive_words = ['good', 'great', 'excellent', 'happy', 'satisfied', 'love', 'like']
        negative_words = ['bad', 'terrible', 'angry', 'frustrated', 'hate', 'dislike', 'problem']
        urgent_words = ['help', 'urgent', 'emergency', 'quick', 'fast', 'now']
        
        positive_count = sum(1 for word in positive_words if word in recent_content)
        negative_count = sum(1 for word in negative_words if word in recent_content)
        urgent_count = sum(1 for word in urgent_words if word in recent_content)
        
        if urgent_count > 0:
            self.emotional_state = "urgent"
        elif positive_count > negative_count:
            self.emotional_state = "positive"
        elif negative_count > positive_count:
            self.emotional_state = "negative"
        else:
            self.emotional_state = "neutral"
    
    def _track_conversation_flow(self):
        """Track conversation flow patterns"""
        if len(self.conversation_history) < 2:
            return
            
        recent_messages = list(self.conversation_history)[-5:]
        flow_pattern = []
        
        for message in recent_messages:
            flow_pattern.append(message['role'])
        
        self.conversation_flow = flow_pattern
    
    def get_context_for_continuation(self) -> Dict[str, Any]:
        """Get context information for conversation continuation"""
        return {
            'summary': self.context_summary,
            'emotional_state': self.emotional_state,
            'topics': list(self.topics),
            'flow_pattern': self.conversation_flow,
            'interaction_count': self.interaction_count,
            'last_interaction': self.last_interaction.isoformat() if self.last_interaction else None,
            'recent_messages': list(self.conversation_history)[-3:] if self.conversation_history else []
        }
    
    def get_conversation_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversation history"""
        return list(self.conversation_history)[-limit:]
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history.clear()
        self.context_summary = ""
        self.emotional_state = "neutral"
        self.topics.clear()
        self.conversation_flow = []
        self.last_interaction = None
        self.interaction_count = 0

class ContextAwareAgent:
    def __init__(self, agent_id: str = "context_agent"):
        self.agent_id = agent_id
        self.context = ConversationContext()
        self.memory = {}
        self.learning_patterns = {}
        self.response_templates = self._load_response_templates()
        self.conversation_continuity_enabled = True
        self.auto_response_enabled = False
        self.response_delay = 1.0  # seconds
        
        # LLM integration
        self.llm_enabled = False
        if LLM_AVAILABLE:
            self.llm_enabled = setup_llm_integration()
            if self.llm_enabled:
                logger.info("LLM integration enabled for intelligent responses")
            else:
                logger.warning("LLM integration failed, using template-based responses")
        else:
            logger.info("Using template-based responses (LLM not available)")
        
        # Response quality tracking
        self.response_quality = {
            'llm_responses': 0,
            'template_responses': 0,
            'user_feedback': []
        }
    
    def _load_response_templates(self) -> Dict[str, List[str]]:
        """Load response templates for different contexts"""
        return {
            'greeting': [
                "Hello! I'm here to help you continue our conversation.",
                "Hi there! I remember our previous discussion. How can I assist you further?",
                "Welcome back! I've been following our conversation and I'm ready to help."
            ],
            'continuation': [
                "Based on our previous discussion about {topic}, I think we can continue from where we left off.",
                "I see we were talking about {topic}. Let me help you with that.",
                "Continuing from our conversation about {topic}, here's what I can suggest."
            ],
            'clarification': [
                "I want to make sure I understand correctly. Are you referring to {context}?",
                "To help you better, could you clarify if you mean {context}?",
                "I want to ensure I'm on the right track. Is this about {context}?"
            ],
            'emotional_support': [
                "I understand this might be {emotion}. Let me help you with that.",
                "I can see this is important to you. Let's work through this together.",
                "I'm here to support you with this {emotion} situation."
            ],
            'urgent': [
                "I understand this is urgent. Let me help you quickly.",
                "I'll prioritize this for you right away.",
                "Let's address this immediately."
            ],
            'general': [
                "I understand. How can I help you with that?",
                "That's interesting! Tell me more about what you'd like to discuss.",
                "I'm here to assist you. What would you like to explore or work on?",
                "Thanks for sharing that with me. How can I be of help?",
                "I'm listening and ready to help. What's on your mind?"
            ],
            'help_request': [
                "I'd be happy to help you! What specific assistance do you need?",
                "I'm here to support you. What can I help you with today?",
                "Let me know what you need help with and I'll do my best to assist you."
            ],
            'information_request': [
                "I'd be glad to provide information about that. What specifically would you like to know?",
                "I can help you find information on that topic. What aspects are you most interested in?",
                "Let me gather some information for you. What details are you looking for?"
            ],
            'gratitude': [
                "You're very welcome! I'm glad I could help.",
                "It's my pleasure to assist you. Is there anything else you'd like to discuss?",
                "Thank you for the kind words. I'm here whenever you need help."
            ],
            'farewell': [
                "Goodbye! It was great talking with you. Feel free to return anytime.",
                "Take care! I'll be here when you want to continue our conversation.",
                "See you later! Don't hesitate to come back if you need anything."
            ]
        }
    
    def process_message(self, message: str, role: str = "user") -> Dict[str, Any]:
        """Process incoming message and generate context-aware response"""
        # Add message to context
        self.context.add_message(role, message)
        
        # Analyze message and generate response
        analysis = self._analyze_message(message)
        response = self._generate_response(analysis)
        
        # Add response to context
        self.context.add_message("assistant", response['content'])
        
        return {
            'response': response,
            'context': self.context.get_context_for_continuation(),
            'analysis': analysis
        }
    
    def _analyze_message(self, message: str) -> Dict[str, Any]:
        """Analyze message for context and intent"""
        message_lower = message.lower()
        
        analysis = {
            'intent': self._detect_intent(message_lower),
            'topics': self._extract_topics(message_lower),
            'emotion': self._detect_emotion(message_lower),
            'urgency': self._detect_urgency(message_lower),
            'continuation_needed': self._needs_continuation(message_lower),
            'context_reference': self._find_context_reference(message_lower)
        }
        
        return analysis
    
    def _detect_intent(self, message: str) -> str:
        """Detect user intent from message"""
        message_lower = message.lower()
        
        # Check for greetings first
        greeting_words = ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening', 'greetings']
        if any(word in message_lower for word in greeting_words):
            return 'greeting'
        
        # Check for help requests
        if any(word in message_lower for word in ['help', 'assist', 'support']):
            return 'help_request'
        
        # Check for continuation requests
        if any(word in message_lower for word in ['continue', 'more', 'next', 'what else', 'and then']):
            return 'continuation_request'
        
        # Check for information requests
        if any(word in message_lower for word in ['explain', 'what', 'how', 'why', 'tell me', 'show me']):
            return 'information_request'
        
        # Check for gratitude
        if any(word in message_lower for word in ['thank', 'thanks', 'appreciate', 'grateful']):
            return 'gratitude'
        
        # Check for farewell
        if any(word in message_lower for word in ['goodbye', 'bye', 'end', 'stop', 'see you', 'later']):
            return 'farewell'
        
        # Default to general
        return 'general'
    
    def _extract_topics(self, message: str) -> List[str]:
        """Extract topics from message"""
        # Simple topic extraction (can be enhanced with NLP)
        words = re.findall(r'\b\w+\b', message)
        topics = [word for word in words if len(word) > 3]
        return topics[:5]  # Limit to 5 topics
    
    def _detect_emotion(self, message: str) -> str:
        """Detect emotion in message"""
        positive_words = ['good', 'great', 'excellent', 'happy', 'satisfied', 'love', 'like']
        negative_words = ['bad', 'terrible', 'angry', 'frustrated', 'hate', 'dislike', 'problem']
        
        positive_count = sum(1 for word in positive_words if word in message)
        negative_count = sum(1 for word in negative_words if word in message)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'
    
    def _detect_urgency(self, message: str) -> bool:
        """Detect if message is urgent"""
        urgent_words = ['help', 'urgent', 'emergency', 'quick', 'fast', 'now', 'immediately']
        return any(word in message for word in urgent_words)
    
    def _needs_continuation(self, message: str) -> bool:
        """Detect if message needs conversation continuation"""
        continuation_words = ['continue', 'more', 'next', 'what else', 'and then']
        return any(word in message for word in continuation_words)
    
    def _find_context_reference(self, message: str) -> Optional[str]:
        """Find references to previous context"""
        if not self.context.conversation_history:
            return None
            
        # Look for references to previous topics
        for topic in self.context.topics:
            if topic in message:
                return topic
        
        return None
    
    def _generate_response(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate context-aware response using LLM or templates"""
        
        # Try LLM first if available
        if self.llm_enabled and LLM_AVAILABLE:
            try:
                llm_response = self._generate_llm_response(analysis)
                if llm_response and llm_response != "Error generating response":
                    self.response_quality['llm_responses'] += 1
                    return {
                        'content': llm_response,
                        'type': 'llm_generated',
                        'context_aware': True,
                        'timestamp': datetime.now().isoformat(),
                        'provider': llm_manager.get_provider_info()
                    }
            except Exception as e:
                logger.warning(f"LLM response generation failed: {e}")
        
        # Fallback to template-based response
        response_type = self._determine_response_type(analysis)
        template = self._select_response_template(response_type, analysis)
        content = self._customize_template(template, analysis)
        
        self.response_quality['template_responses'] += 1
        
        return {
            'content': content,
            'type': response_type,
            'context_aware': True,
            'timestamp': datetime.now().isoformat(),
            'provider': 'template'
        }
    
    def _generate_llm_response(self, analysis: Dict[str, Any]) -> str:
        """Generate response using LLM"""
        if not self.llm_enabled or not LLM_AVAILABLE:
            return ""
        
        # Build context for LLM
        context = self.context.get_context_for_continuation()
        
        # Create a natural prompt based on analysis
        prompt = self._build_llm_prompt(analysis, context)
        
        # Generate response using LLM
        response = llm_manager.generate_response(prompt, context)
        
        return response
    
    def _build_llm_prompt(self, analysis: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Build natural language prompt for LLM"""
        intent = analysis.get('intent', 'general')
        emotion = analysis.get('emotion', 'neutral')
        urgency = analysis.get('urgency', False)
        
        # Build context-aware prompt
        prompt_parts = []
        
        # Add conversation context
        if context.get('summary'):
            prompt_parts.append(f"Context: {context['summary']}")
        
        # Add emotional awareness
        if emotion != 'neutral':
            prompt_parts.append(f"The user seems to be in a {emotion} emotional state.")
        
        # Add urgency awareness
        if urgency:
            prompt_parts.append("This appears to be an urgent request.")
        
        # Add intent-specific instructions
        if intent == 'greeting':
            prompt_parts.append("Respond warmly to this greeting.")
        elif intent == 'help_request':
            prompt_parts.append("Provide helpful assistance for this request.")
        elif intent == 'continuation_request':
            prompt_parts.append("Continue the conversation naturally based on previous context.")
        elif intent == 'information_request':
            prompt_parts.append("Provide informative and helpful information.")
        elif intent == 'gratitude':
            prompt_parts.append("Respond graciously to this expression of gratitude.")
        elif intent == 'farewell':
            prompt_parts.append("Respond appropriately to this farewell.")
        
        # Add the user's message
        recent_messages = context.get('recent_messages', [])
        if recent_messages:
            user_message = recent_messages[-1].get('content', '')
            prompt_parts.append(f"User: {user_message}")
        
        prompt_parts.append("Assistant:")
        
        return " ".join(prompt_parts)
    
    def _determine_response_type(self, analysis: Dict[str, Any]) -> str:
        """Determine appropriate response type"""
        if analysis['urgency']:
            return 'urgent'
        elif analysis['emotion'] == 'negative':
            return 'emotional_support'
        elif analysis['continuation_needed']:
            return 'continuation'
        elif analysis['intent'] == 'help_request':
            return 'clarification'
        elif analysis['intent'] == 'greeting':
            return 'greeting'
        else:
            return 'general'
    
    def _select_response_template(self, response_type: str, analysis: Dict[str, Any]) -> str:
        """Select appropriate response template"""
        templates = self.response_templates.get(response_type, self.response_templates['general'])
        
        # Select template based on context
        if response_type == 'continuation' and analysis['context_reference']:
            return templates[0]  # Use continuation template
        elif response_type == 'emotional_support':
            return templates[0]  # Use emotional support template
        elif response_type == 'urgent':
            return templates[0]  # Use urgent template
        elif response_type == 'greeting':
            return templates[0]  # Use greeting template
        elif response_type == 'help_request':
            return templates[0]  # Use help request template
        elif response_type == 'information_request':
            return templates[0]  # Use information request template
        elif response_type == 'gratitude':
            return templates[0]  # Use gratitude template
        elif response_type == 'farewell':
            return templates[0]  # Use farewell template
        else:
            # For general responses, select a random template for variety
            return random.choice(templates)
    
    def _customize_template(self, template: str, analysis: Dict[str, Any]) -> str:
        """Customize template with context information"""
        # Replace placeholders with actual context
        if '{topic}' in template and analysis['context_reference']:
            template = template.replace('{topic}', analysis['context_reference'])
        
        if '{context}' in template and self.context.context_summary:
            template = template.replace('{context}', self.context.context_summary[:50])
        
        if '{emotion}' in template:
            template = template.replace('{emotion}', analysis['emotion'])
        
        return template
    
    def continue_conversation(self, message: str) -> str:
        """Continue conversation with context awareness"""
        if not self.conversation_continuity_enabled:
            return "I'm here to help! What would you like to discuss?"
        
        # Process message and get response
        result = self.process_message(message)
        
        # Add delay for more natural conversation
        if self.response_delay > 0:
            time.sleep(self.response_delay)
        
        return result['response']['content']
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get summary of current conversation"""
        return {
            'agent_id': self.agent_id,
            'context': self.context.get_context_for_continuation(),
            'memory': self.memory,
            'learning_patterns': self.learning_patterns,
            'conversation_continuity_enabled': self.conversation_continuity_enabled,
            'auto_response_enabled': self.auto_response_enabled
        }
    
    def save_conversation_state(self, filepath: str):
        """Save conversation state to file"""
        state = {
            'agent_id': self.agent_id,
            'context': {
                'conversation_history': list(self.context.conversation_history),
                'context_summary': self.context.context_summary,
                'emotional_state': self.context.emotional_state,
                'topics': list(self.context.topics),
                'conversation_flow': self.context.conversation_flow,
                'interaction_count': self.context.interaction_count,
                'last_interaction': self.context.last_interaction.isoformat() if self.context.last_interaction else None
            },
            'memory': self.memory,
            'learning_patterns': self.learning_patterns,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
            logger.info(f"Conversation state saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving conversation state: {e}")
    
    def load_conversation_state(self, filepath: str):
        """Load conversation state from file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                state = json.load(f)
            
            # Restore context
            context_data = state.get('context', {})
            self.context.conversation_history = deque(context_data.get('conversation_history', []), maxlen=self.context.max_history)
            self.context.context_summary = context_data.get('context_summary', '')
            self.context.emotional_state = context_data.get('emotional_state', 'neutral')
            self.context.topics = set(context_data.get('topics', []))
            self.context.conversation_flow = context_data.get('conversation_flow', [])
            self.context.interaction_count = context_data.get('interaction_count', 0)
            
            last_interaction = context_data.get('last_interaction')
            if last_interaction:
                self.context.last_interaction = datetime.fromisoformat(last_interaction)
            
            # Restore memory and patterns
            self.memory = state.get('memory', {})
            self.learning_patterns = state.get('learning_patterns', {})
            
            logger.info(f"Conversation state loaded from {filepath}")
        except Exception as e:
            logger.error(f"Error loading conversation state: {e}")
    
    def toggle_conversation_continuity(self):
        """Toggle conversation continuity feature"""
        self.conversation_continuity_enabled = not self.conversation_continuity_enabled
        return self.conversation_continuity_enabled
    
    def toggle_auto_response(self):
        """Toggle auto-response feature"""
        self.auto_response_enabled = not self.auto_response_enabled
        return self.auto_response_enabled
    
    def set_response_delay(self, delay: float):
        """Set response delay in seconds"""
        self.response_delay = max(0.0, delay)
        logger.info(f"Response delay set to {self.response_delay} seconds")
    
    def get_llm_provider_info(self) -> Dict[str, Any]:
        """Get information about current LLM provider"""
        if not self.llm_enabled or not LLM_AVAILABLE:
            return {"error": "LLM not available"}
        
        return llm_manager.get_provider_info()
    
    def set_llm_provider(self, provider_name: str) -> bool:
        """Set LLM provider"""
        if not self.llm_enabled or not LLM_AVAILABLE:
            return False
        
        try:
            llm_manager.set_provider(provider_name)
            logger.info(f"Switched to {provider_name} LLM provider")
            return True
        except Exception as e:
            logger.error(f"Failed to switch to {provider_name}: {e}")
            return False
    
    def get_available_llm_providers(self) -> List[str]:
        """Get list of available LLM providers"""
        if not LLM_AVAILABLE:
            return []
        
        return llm_manager.get_available_providers()
    
    def get_response_quality_stats(self) -> Dict[str, Any]:
        """Get response quality statistics"""
        total_responses = self.response_quality['llm_responses'] + self.response_quality['template_responses']
        
        if total_responses == 0:
            return {
                "total_responses": 0,
                "llm_percentage": 0,
                "template_percentage": 0,
                "llm_responses": 0,
                "template_responses": 0
            }
        
        llm_percentage = (self.response_quality['llm_responses'] / total_responses) * 100
        template_percentage = (self.response_quality['template_responses'] / total_responses) * 100
        
        return {
            "total_responses": total_responses,
            "llm_percentage": round(llm_percentage, 1),
            "template_percentage": round(template_percentage, 1),
            "llm_responses": self.response_quality['llm_responses'],
            "template_responses": self.response_quality['template_responses'],
            "llm_enabled": self.llm_enabled,
            "current_provider": self.get_llm_provider_info()
        }
    
    def add_user_feedback(self, feedback: str, rating: int = 5):
        """Add user feedback for response quality"""
        feedback_entry = {
            'feedback': feedback,
            'rating': max(1, min(5, rating)),  # Ensure rating is 1-5
            'timestamp': datetime.now().isoformat()
        }
        self.response_quality['user_feedback'].append(feedback_entry)
        
        # Keep only last 50 feedback entries
        if len(self.response_quality['user_feedback']) > 50:
            self.response_quality['user_feedback'] = self.response_quality['user_feedback'][-50:]
        
        logger.info(f"Added user feedback: {feedback} (rating: {rating})")
    
    def get_conversation_intelligence_level(self) -> Dict[str, Any]:
        """Get conversation intelligence level assessment"""
        stats = self.get_response_quality_stats()
        
        # Calculate intelligence level based on various factors
        intelligence_score = 0
        factors = []
        
        # LLM usage factor (0-40 points)
        if stats['llm_percentage'] > 0:
            intelligence_score += min(40, stats['llm_percentage'] * 0.4)
            factors.append(f"LLM responses: {stats['llm_percentage']}%")
        
        # Context awareness factor (0-30 points)
        context_length = len(self.context.conversation_history)
        if context_length > 10:
            intelligence_score += 30
            factors.append("Strong context awareness")
        elif context_length > 5:
            intelligence_score += 20
            factors.append("Good context awareness")
        elif context_length > 0:
            intelligence_score += 10
            factors.append("Basic context awareness")
        
        # Learning patterns factor (0-20 points)
        if self.learning_patterns:
            intelligence_score += min(20, len(self.learning_patterns) * 2)
            factors.append(f"Learning patterns: {len(self.learning_patterns)}")
        
        # User feedback factor (0-10 points)
        if self.response_quality['user_feedback']:
            avg_rating = sum(f['rating'] for f in self.response_quality['user_feedback']) / len(self.response_quality['user_feedback'])
            intelligence_score += min(10, avg_rating * 2)
            factors.append(f"User satisfaction: {avg_rating:.1f}/5")
        
        # Determine intelligence level
        if intelligence_score >= 80:
            level = "Highly Intelligent"
        elif intelligence_score >= 60:
            level = "Intelligent"
        elif intelligence_score >= 40:
            level = "Moderately Intelligent"
        elif intelligence_score >= 20:
            level = "Basic Intelligence"
        else:
            level = "Template-Based"
        
        return {
            "intelligence_score": round(intelligence_score, 1),
            "intelligence_level": level,
            "factors": factors,
            "stats": stats,
            "context_length": len(self.context.conversation_history),
            "learning_patterns": len(self.learning_patterns),
            "user_feedback_count": len(self.response_quality['user_feedback'])
        }

# Global context-aware agent instance
context_agent = ContextAwareAgent()

if __name__ == "__main__":
    # Test the context-aware agent
    print("Testing Context-Aware Agent...")
    
    # Test conversation continuation
    messages = [
        "Hello! I need help with Python programming.",
        "I'm working on a web application.",
        "I'm having trouble with async functions.",
        "Can you continue explaining async programming?",
        "Thank you for your help!"
    ]
    
    for message in messages:
        print(f"\nUser: {message}")
        response = context_agent.continue_conversation(message)
        print(f"Agent: {response}")
    
    # Show conversation summary
    summary = context_agent.get_conversation_summary()
    print(f"\nConversation Summary:")
    print(f"Topics: {summary['context']['topics']}")
    print(f"Emotional State: {summary['context']['emotional_state']}")
    print(f"Interaction Count: {summary['context']['interaction_count']}")
