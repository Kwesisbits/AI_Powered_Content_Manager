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
        self.api_key = api_key or os.environ.get("GROK_API_KEY")
        
        # VERIFY KEY FORMAT
        if self.api_key:
            print(f"API Key found: {self.api_key[:15]}...")
            if not self.api_key.startswith('xai-'):
                print(f"WARNING: Key doesn't start with 'xai-'")
        else:
            print("NO API KEY FOUND")
            print("   Set with: export GROK_API_KEY='xai-your-key-here'")
        
        # CORRECT ENDPOINT for xAI
        self.base_url = "https://api.x.ai/v1"
        
    def generate_content(self, platform: str, topic: str, brand_voice: BrandVoice,
                        tone: Optional[str] = None, media_files: List = None) -> Dict:
        
        print(f"GENERATING CONTENT")
        print(f"   Platform: {platform}")
        print(f"   Topic: {topic}")
        print(f"   API Key valid: {bool(self.api_key and self.api_key.startswith('xai-'))}")
        
        # If no valid API key, use fallback immediately
        if not self.api_key or not self.api_key.startswith('xai-'):
            print("   Using fallback (invalid/missing API key)")
            return self._generate_fallback_content(platform, topic, brand_voice)
        
        try:
            # Try real API call
            prompt = self._construct_prompt(platform, topic, brand_voice, tone, None)
            print(f"   Calling xAI API...")
            
            response_text = self._call_xai_api(prompt)
            
            print(f"   API call successful")
            
            # Parse response
            content_data = self._parse_ai_response(response_text, platform)
            
            content_data["metadata"] = {
                "generated_by": "xai_api",
                "platform": platform,
                "hashtags": content_data.get("hashtags", []),
            }
            
            return content_data
            
        except Exception as e:
            print(f"   API failed: {str(e)[:100]}")
            return self._generate_fallback_content(platform, topic, brand_voice)
    
    def _construct_prompt(self, platform: str, topic: str, brand_voice: BrandVoice,
                         tone: Optional[str], media_context: Optional[str]) -> str:
        
        # SIMPLER PROMPT - More likely to work
        prompt = f"""Create a {platform} social media post about: {topic}

Company: {brand_voice.company_name}
Tone: {tone or brand_voice.tone}
Target audience: {brand_voice.target_audience}

Make it engaging and include 2-3 relevant hashtags.
Add a question to engage the audience."""
        
        return prompt
    
    def _call_xai_api(self, prompt: str) -> str:
        """Call xAI API with proper error handling"""
        
        url = f"{self.base_url}/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # SIMPLER PAYLOAD - matches xAI documentation
        payload = {
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "model": "grok-beta",
            "temperature": 0.7,
            "max_tokens": 500
        }
        
        print(f"   Request to: {url}")
        
        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            print(f"   Response status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"   API Error {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                raise Exception(f"API error {response.status_code}")
            
            response_json = response.json()
            return response_json["choices"][0]["message"]["content"]
            
        except requests.exceptions.RequestException as e:
            print(f"   Network error: {e}")
            raise Exception(f"Network error: {e}")
    
    def _parse_ai_response(self, response: str, platform: str) -> Dict:
        """Parse API response"""
        
        # Just return the text as content
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
        """Better fallback that uses actual inputs"""
        
        company = brand_voice.company_name
        topic_words = topic.split()
        main_topic = topic_words[0] if topic_words else topic[:20]
        
        # Create dynamic content based on inputs
        content = f"{topic}\n\n"
        content += f"At {company}, we're examining the implications and opportunities in this space. "
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
                "ai_notes": "Generated from improved fallback template"
            }
        }
