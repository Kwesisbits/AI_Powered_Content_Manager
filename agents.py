import os
import requests
import json
from typing import Dict, List, Optional
from dataclasses import dataclass
import re

@dataclass
class BrandVoice:
    company_name: str
    tone: str
    personality_traits: List[str]
    target_audience: str
    content_pillars: List[str]
    forbidden_topics: List[str]

class ContentAgent:
    def __init__(self, api_key: str = None):
        # Try Groq first, then Grok
        self.api_key = api_key or os.environ.get("GROQ_API_KEY") or os.environ.get("GROK_API_KEY")
        
        print(f"API Key: {'SET' if self.api_key else 'NOT SET'}")
        if self.api_key:
            print(f"Key starts with: {self.api_key[:10]}...")
        
        # Groq API endpoint (free tier available)
        self.base_url = "https://api.groq.com/openai/v1"
        
    def generate_content(self, platform: str, topic: str, brand_voice: BrandVoice,
                        tone: Optional[str] = None, media_files: List = None) -> Dict:
        
        print(f"Generating {platform} content: {topic[:50]}...")
        
        # Check if we should use API
        use_api = bool(self.api_key and len(self.api_key) > 20)
        
        if use_api:
            try:
                prompt = self._construct_prompt(platform, topic, brand_voice, tone, None)
                response = self._call_groq_api(prompt)
                content_data = self._parse_response(response, platform)
                
                content_data["metadata"] = {
                    "generated_by": "groq_api",
                    "platform": platform,
                    "hashtags": content_data.get("hashtags", []),
                }
                
                return content_data
                
            except Exception as e:
                print(f"API failed: {e}")
                return self._generate_fallback(platform, topic, brand_voice)
        
        return self._generate_fallback(platform, topic, brand_voice)
    
    def _construct_prompt(self, platform: str, topic: str, brand_voice: BrandVoice,
                         tone: Optional[str], media_context: Optional[str]) -> str:
        
        prompt = f"""Create a {platform} social media post about: {topic}

Company: {brand_voice.company_name}
Brand Tone: {tone or brand_voice.tone}
Target Audience: {brand_voice.target_audience}
Personality Traits: {', '.join(brand_voice.personality_traits)}

Platform Guidelines:
- {platform}: Write in a {platform.lower()} style with appropriate length and format
- Include 3-5 relevant hashtags
- Add an engaging question for audience interaction
- Keep it professional yet engaging

Do NOT mention: {', '.join(brand_voice.forbidden_topics)}

Format the post naturally for {platform}. Make it creative and platform-appropriate."""
        
        return prompt
    
    def _call_groq_api(self, prompt: str) -> str:
        """Call Groq API - free tier available"""
        
        if not self.api_key:
            raise Exception("No API key")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Groq supports multiple models - Mixtral is good and fast
        payload = {
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "model": "mixtral-8x7b-32768",  # Fast and good quality
            "temperature": 0.7,
            "max_tokens": 500
        }
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"Groq API error {response.status_code}: {response.text[:200]}")
            raise Exception(f"API error {response.status_code}")
        
        data = response.json()
        return data["choices"][0]["message"]["content"]
    
    def _parse_response(self, response: str, platform: str) -> Dict:
        """Parse API response"""
        return {
            "content": response,
            "hashtags": self._extract_hashtags(response),
            "engagement_question": "What are your thoughts?",
            "optimal_post_time": "10:00 AM"
        }
    
    def _extract_hashtags(self, text: str) -> List[str]:
        hashtags = re.findall(r'#\w+', text)
        return list(set(hashtags))[:5]
    
    def _generate_fallback(self, platform: str, topic: str, brand_voice: BrandVoice) -> Dict:
        """High-quality fallback template"""
        
        company = brand_voice.company_name
        main_topic = topic.split()[0] if topic.split() else topic[:20].strip()
        
        # Creative templates for each platform
        templates = {
            "linkedin": f"""**Deep Dive: {topic}**

At {company}, we're examining how {main_topic.lower()} is transforming business operations. Our analysis reveals key insights:

 **Strategic Impact**: Organizations implementing {main_topic.lower()} solutions report significant efficiency gains and competitive advantages.

 **Implementation Roadmap**: Successful adoption requires careful planning, stakeholder alignment, and measurable milestones.

 **Future Outlook**: The trajectory suggests accelerated adoption as technology matures and use cases expand.

**Discussion Question**: What challenges or successes has your organization experienced with {main_topic.lower()} implementation?

#{company.replace(' ', '')} #{main_topic.capitalize()} #DigitalTransformation #BusinessStrategy""",
            
            "twitter": f"""Exploring {topic}:

• Market evolution and current trends
• Key implementation considerations  
• Measuring ROI and business impact

What's your perspective on this space?

#{main_topic.capitalize()} #Tech #Innovation #Business""",
            
            "instagram": f""" {topic}

At {company}, we're passionate about how technology drives meaningful change. {main_topic.capitalize()} represents one of the most exciting areas of innovation today.

Key considerations:
• Strategic alignment
• Technical integration
• Value realization

What tech innovation excites you most right now? Share below! 

#{company.replace(' ', '')} #{main_topic.capitalize()} #TechInnovation #FutureForward"""
        }
        
        content = templates.get(platform.lower(), templates["linkedin"])
        
        return {
            "content": content,
            "hashtags": self._extract_hashtags(content),
            "engagement_question": f"What's your take on {main_topic.lower()}?",
            "optimal_post_time": "9:00 AM",
            "metadata": {
                "generated_by": "creative_fallback",
                "platform": platform,
                "ai_notes": "Generated from creative template"
            }
        }
