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
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        self.base_url = "https://api.groq.com/openai/v1"
        
        print(f"Agent initialized with key: {'YES' if self.api_key else 'NO'}")
        
    def generate_content(self, platform: str, topic: str, brand_voice: BrandVoice,
                        tone: Optional[str] = None, media_files: List = None) -> Dict:
        """Generate AI content - SIMPLIFIED VERSION"""
        
        print(f"\n=== GENERATING CONTENT ===")
        print(f"Platform: {platform}")
        print(f"Topic: {topic}")
        print(f"Company: {brand_voice.company_name}")
        
        # If no API key, use minimal fallback
        if not self.api_key:
            print("No API key - using simple fallback")
            return self._simple_fallback(platform, topic, brand_voice)
        
        try:
            # Create prompt
            prompt = f"""Create a creative, engaging {platform} social media post about: {topic}
            
Company: {brand_voice.company_name}
Brand Voice: {brand_voice.tone}
Audience: {brand_voice.target_audience}
Key Traits: {', '.join(brand_voice.personality_traits)}

Make it:
1. Platform-appropriate for {platform}
2. Include 3-5 relevant hashtags
3. Add a thought-provoking question
4. Be creative and insightful
5. Don't use placeholders like "Key insight 1" - provide actual insights

Write naturally as a social media post, not in JSON format."""
            
            # Call API
            print("Calling Groq API...")
            response = self._call_api(prompt)
            
            # Process response
            content = response.strip()
            print(f"API Response received ({len(content)} chars)")
            
            # Extract hashtags
            hashtags = re.findall(r'#\w+', content)
            hashtags = list(set(hashtags))[:5]
            
            # If no hashtags in response, add some
            if not hashtags:
                main_word = topic.split()[0].lower() if topic.split() else "innovation"
                hashtags = [f"#{brand_voice.company_name.replace(' ', '')}", 
                          f"#{main_word.capitalize()}", "#TechInnovation"]
            
            # Return result
            result = {
                "content": content,
                "hashtags": hashtags,
                "engagement_question": "What are your thoughts?",
                "optimal_post_time": "9:00 AM",
                "metadata": {
                    "generated_by": "groq_api",
                    "platform": platform,
                    "tone": tone or brand_voice.tone,
                    "word_count": len(content.split())
                }
            }
            
            print("Content generation successful")
            return result
            
        except Exception as e:
            print(f"API Error: {e}")
            # Use better fallback
            return self._creative_fallback(platform, topic, brand_voice)
    
    def _call_api(self, prompt: str) -> str:
        """Simple API call"""
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messages": [{"role": "user", "content": prompt}],
            "model": "mixtral-8x7b-32768",
            "temperature": 0.8,  # More creative
            "max_tokens": 400
        }
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code != 200:
            raise Exception(f"API error {response.status_code}: {response.text[:100]}")
        
        data = response.json()
        return data["choices"][0]["message"]["content"]
    
    def _simple_fallback(self, platform: str, topic: str, brand_voice: BrandVoice) -> Dict:
        """Absolute simplest fallback"""
        content = f"Exploring {topic} at {brand_voice.company_name}. #Innovation #Tech"
        return {
            "content": content,
            "hashtags": ["#Innovation", "#Tech"],
            "metadata": {"generated_by": "simple_fallback"}
        }
    
    def _creative_fallback(self, platform: str, topic: str, brand_voice: BrandVoice) -> Dict:
        """Creative fallback that actually generates content"""
        
        import random
        
        company = brand_voice.company_name
        topic_lower = topic.lower()
        
        # Different intro templates
        intros = [
            f" Exciting developments in {topic_lower}!",
            f" Deep dive into {topic_lower} today.",
            f" Analyzing the impact of {topic_lower}.",
            f" Exploring innovations in {topic_lower}."
        ]
        
        # Different insights
        insights = [
            f"Organizations implementing {topic_lower} solutions report significant efficiency gains.",
            f"The adoption curve for {topic_lower} is accelerating across industries.",
            f"{topic_lower} represents one of the most transformative technologies today.",
            f"Successful {topic_lower} implementation requires strategic planning and execution."
        ]
        
        # Different questions
        questions = [
            f"What's been your experience with {topic_lower}?",
            f"How is your organization approaching {topic_lower}?",
            f"What challenges have you faced with {topic_lower} implementation?",
            f"Where do you see {topic_lower} making the biggest impact?"
        ]
        
        # Build content
        content = f"{random.choice(intros)}\n\n"
        content += f"At {company}, we're seeing {topic_lower} reshape business landscapes. "
        content += f"{random.choice(insights)}\n\n"
        content += f"Key considerations:\n• Strategic alignment\n• Technical integration\n• ROI measurement\n• Future scalability\n\n"
        content += f"{random.choice(questions)}\n\n"
        content += f"#{company.replace(' ', '')} #{topic.split()[0].capitalize() if topic.split() else 'Innovation'} #BusinessStrategy"
        
        hashtags = [f"#{company.replace(' ', '')}", 
                   f"#{topic.split()[0].capitalize() if topic.split() else 'Innovation'}", 
                   "#BusinessStrategy", "#Tech"]
        
        return {
            "content": content,
            "hashtags": hashtags,
            "engagement_question": random.choice(questions),
            "optimal_post_time": "9:00 AM",
            "metadata": {
                "generated_by": "creative_fallback",
                "platform": platform,
                "ai_notes": "Generated with creative variation"
            }
        }
