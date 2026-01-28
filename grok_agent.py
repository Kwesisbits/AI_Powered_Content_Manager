import os
import json
import requests
from dataclasses import dataclass
from typing import List, Dict
import random

@dataclass
class BrandVoice:
    company_name: str = "TechCorp"
    tone: str = "professional"
    personality_traits: List[str] = None
    target_audience: str = "professionals"
    
    def __post_init__(self):
        if self.personality_traits is None:
            self.personality_traits = ["Expert", "Innovative"]

class GrokContentAgent:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GROK_API_KEY", "demo-key")
        self.base_url = "https://api.x.ai/v1"
        
    def generate_platform_content(self, platform: str, topic: str, 
                                 brand_voice: BrandVoice, media_context: str = None) -> Dict:
        """
        Generate content using Grok API (with fallback for demo)
        """
        
        # Platform-specific templates
        templates = {
            "LinkedIn": {
                "template": """Create a professional LinkedIn post about {topic} for {company}.
                
                Brand voice: {tone}
                Audience: {audience}
                
                Include:
                1. Insightful analysis
                2. Actionable takeaway
                3. 3-5 professional hashtags
                4. Engagement question
                
                Post length: 150-300 words""",
                "hashtags": ["#AI", "#Tech", "#Innovation", "#Business"]
            },
            "Twitter": {
                "template": """Create a Twitter thread (2-3 tweets) about {topic}.
                
                Style: Concise, engaging, conversational
                Include 2-3 relevant hashtags
                Add emojis where appropriate""",
                "hashtags": ["#Tech", "#AI", "#Future"]
            },
            "Instagram": {
                "template": """Create Instagram caption about {topic}.
                
                Style: Engaging, visual-first
                Include: Emojis, call-to-action, 5-7 hashtags
                Keep it under 150 words""",
                "hashtags": ["#Tech", "#Innovation", "#DailyTech"]
            }
        }
        
        # Try to call Grok API
        try:
            if self.api_key and self.api_key != "demo-key":
                # Actual Grok API call
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                prompt = templates[platform]["template"].format(
                    topic=topic,
                    company=brand_voice.company_name,
                    tone=brand_voice.tone,
                    audience=brand_voice.target_audience
                )
                
                if media_context:
                    prompt += f"\n\nMedia context: {media_context}"
                
                payload = {
                    "messages": [{"role": "user", "content": prompt}],
                    "model": "grok-beta",
                    "temperature": 0.7,
                    "max_tokens": 500
                }
                
                response = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=10
                )
                
                if response.status_code == 200:
                    content = response.json()["choices"][0]["message"]["content"]
                    return self._format_response(content, platform, templates[platform]["hashtags"])
                
        except Exception as e:
            print(f"Grok API failed: {e}. Using demo content.")
        
        # Fallback demo content
        return self._generate_demo_content(platform, topic, brand_voice)
    
    def _format_response(self, content: str, platform: str, hashtags: List[str]) -> Dict:
        """Format Grok response"""
        return {
            "post_text": content[:500] if len(content) > 500 else content,
            "hashtags": hashtags,
            "optimal_post_time": self._get_optimal_time(platform),
            "engagement_question": self._get_engagement_question(),
            "platform": platform.lower()
        }
    
    def _generate_demo_content(self, platform: str, topic: str, brand_voice: BrandVoice) -> Dict:
        """Generate demo content when API is unavailable"""
        demos = {
            "LinkedIn": f"""Excited to share insights on {topic}! 

At {brand_voice.company_name}, we're seeing revolutionary changes in how businesses leverage technology. The key takeaway? Adaptability is everything.

Key points:
• Strategic implementation beats rushed adoption
• Human-AI collaboration is the future
• Continuous learning is non-negotiable

What's your biggest challenge with {topic.split()[0]} implementation? Share below! 👇

#{brand_voice.company_name.replace(' ', '')} #DigitalTransformation #BusinessTech""",
            
            "Twitter": f"""Just explored {topic} 🤖

The future is here, and it's collaborative. Humans + AI = unstoppable.

Thoughts? #AI #Tech #Future""",
            
            "Instagram": f"""Exploring {topic} today! ✨

The intersection of technology and human creativity is where magic happens. 

What tech excites you most right now? Let us know! 👇

#TechLife #Innovation #FutureIsNow #TechDaily"""
        }
        
        return {
            "post_text": demos.get(platform, f"Content about {topic}"),
            "hashtags": ["#Demo", "#Tech", "#AI"],
            "optimal_post_time": self._get_optimal_time(platform),
            "engagement_question": "What are your thoughts on this?",
            "platform": platform.lower()
        }
    
    def _get_optimal_time(self, platform: str) -> str:
        """Get optimal posting time"""
        times = {
            "LinkedIn": "9:00 AM",
            "Twitter": "12:00 PM",
            "Instagram": "6:00 PM"
        }
        return times.get(platform, "10:00 AM")
    
    def _get_engagement_question(self) -> str:
        """Get random engagement question"""
        questions = [
            "What are your thoughts on this?",
            "Has your company implemented this?",
            "What's your biggest challenge with this?",
            "Agree or disagree?"
        ]
        return random.choice(questions)
