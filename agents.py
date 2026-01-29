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
        self.api_key = api_key or os.environ.get("GROQ_API_KEY") or os.environ.get("GROK_API_KEY")
        
        print(f"DEBUG: API Key provided: {'YES' if self.api_key else 'NO'}")
        if self.api_key:
            print(f"DEBUG: Key value: {self.api_key[:15]}...")
            print(f"DEBUG: Key starts with gsk_: {self.api_key.startswith('gsk_')}")
            print(f"DEBUG: Key starts with xai-: {self.api_key.startswith('xai-')}")
        
        # Groq API endpoint
        self.base_url = "https://api.groq.com/openai/v1"
        
    def generate_content(self, platform: str, topic: str, brand_voice: BrandVoice,
                        tone: Optional[str] = None, media_files: List = None) -> Dict:
        
        print(f"DEBUG: Generating content for {platform}")
        print(f"DEBUG: Topic: {topic}")
        print(f"DEBUG: API Key available: {'YES' if self.api_key else 'NO'}")
        
        # Check if we have ANY API key (Groq or xAI)
        if not self.api_key:
            print("DEBUG: No API key, using fallback")
            return self._generate_fallback_content(platform, topic, brand_voice)
        
        # Try to call the API regardless of prefix
        try:
            print("DEBUG: Constructing prompt...")
            prompt = self._construct_prompt(platform, topic, brand_voice, tone, None)
            
            print("DEBUG: Calling Groq API...")
            response_text = self._call_groq_api(prompt)
            
            print("DEBUG: API call successful!")
            print(f"DEBUG: Response length: {len(response_text)} chars")
            
            # Parse response
            content_data = self._parse_ai_response(response_text, platform)
            
            content_data["metadata"] = {
                "generated_by": "groq_api",
                "platform": platform,
                "hashtags": content_data.get("hashtags", []),
            }
            
            return content_data
            
        except Exception as e:
            print(f"DEBUG: API failed: {str(e)}")
            print("DEBUG: Using fallback content")
            return self._generate_fallback_content(platform, topic, brand_voice)
    
    def _construct_prompt(self, platform: str, topic: str, brand_voice: BrandVoice,
                         tone: Optional[str], media_context: Optional[str]) -> str:
        
        prompt = f"""Create a {platform} social media post about: {topic}

Company: {brand_voice.company_name}
Brand Tone: {tone or brand_voice.tone}
Target Audience: {brand_voice.target_audience}
Content Pillars: {', '.join(brand_voice.content_pillars)}
Forbidden Topics: {', '.join(brand_voice.forbidden_topics)}

Make it engaging, professional, and platform-appropriate. Include 3-5 relevant hashtags.
Add a question to engage the audience. Provide valuable insights about the topic."""
        
        return prompt
    
    def _call_groq_api(self, prompt: str) -> str:
        """Call Groq API"""
        
        if not self.api_key:
            raise Exception("No API key provided")
        
        url = f"{self.base_url}/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "model": "mixtral-8x7b-32768",
            "temperature": 0.7,
            "max_tokens": 500
        }
        
        print(f"DEBUG: Sending request to: {url}")
        print(f"DEBUG: Payload keys: {list(payload.keys())}")
        
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"DEBUG: Response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"DEBUG: Response error: {response.text[:200]}")
            raise Exception(f"API error {response.status_code}")
        
        response_json = response.json()
        
        # Debug the response structure
        print(f"DEBUG: Response keys: {list(response_json.keys())}")
        if 'choices' in response_json:
            print(f"DEBUG: Number of choices: {len(response_json['choices'])}")
        
        return response_json["choices"][0]["message"]["content"]
    
    def _parse_ai_response(self, response: str, platform: str) -> Dict:
        """Parse API response"""
        
        return {
            "content": response,
            "hashtags": self._extract_hashtags(response),
            "engagement_question": "What are your thoughts?",
            "optimal_post_time": "10:00 AM"
        }
    
    def _extract_hashtags(self, text: str) -> List[str]:
        hashtags = re.findall(r'#\w+', text)
        return list(set(hashtags))[:3]
    
    def _generate_fallback_content(self, platform: str, topic: str, 
                                  brand_voice: BrandVoice) -> Dict:
        """Fallback content - will only be used if API completely fails"""
        
        company = brand_voice.company_name
        topic_words = topic.split()
        main_topic = topic_words[0] if topic_words else topic[:20]
        
        content = f"{topic}\n\n"
        content += f"At {company}, we're exploring this important area. "
        content += f"Our analysis of {main_topic.lower()} reveals several key areas:\n\n"
        content += "• Strategic implementation approaches\n"
        content += "• Integration with existing systems\n"
        content += "• Measuring return on investment\n"
        content += "• Future developments and trends\n\n"
        content += f"How is your organization approaching {main_topic.lower()}? "
        content += "Share your insights and challenges in the comments.\n\n"
        content += f"#{company.replace(' ', '')} #{main_topic.capitalize()} #BusinessStrategy #TechInnovation"
        
        return {
            "content": content,
            "hashtags": [f"#{company.replace(' ', '')}", f"#{main_topic.capitalize()}", "#Innovation"],
            "engagement_question": f"What's your perspective on {main_topic.lower()}?",
            "optimal_post_time": "9:00 AM",
            "metadata": {
                "generated_by": "fallback_template",
                "platform": platform,
                "ai_notes": "Generated from fallback template"
            }
        }
