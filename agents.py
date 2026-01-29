import os
import requests
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
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable is required")
        
        self.base_url = "https://api.groq.com/openai/v1"
        print(f"✓ Agent initialized for {self.base_url}")
    
    def generate_content(self, platform: str, topic: str, brand_voice: BrandVoice,
                        tone: Optional[str] = None, include_hashtags: bool = True,
                        include_question: bool = True, call_to_action: str = None) -> Dict:
        """
        Generate AI content - NO FALLBACK - API CALL ONLY
        """
        
        # Build detailed prompt with ALL parameters
        prompt = self._build_complete_prompt(
            platform=platform,
            topic=topic,
            brand_voice=brand_voice,
            tone=tone,
            include_hashtags=include_hashtags,
            include_question=include_question,
            call_to_action=call_to_action
        )
        
        print(f"\n SENDING TO API:")
        print(f"   Company: {brand_voice.company_name}")
        print(f"   Platform: {platform}")
        print(f"   Tone: {tone or brand_voice.tone}")
        print(f"   Topic: {topic[:50]}...")
        
        # CALL API - NO FALLBACK
        try:
            response = self._call_groq_api(prompt)
            
            # Extract hashtags from response
            hashtags = re.findall(r'#\w+', response)
            hashtags = list(set(hashtags))[:5]
            
            # If no hashtags in response but they were requested, add some
            if include_hashtags and not hashtags:
                main_word = topic.split()[0].lower() if topic.split() else "topic"
                hashtags = [f"#{brand_voice.company_name.replace(' ', '')}", 
                          f"#{main_word.capitalize()}", "#Innovation"]
            
            # Build result
            result = {
                "content": response.strip(),
                "hashtags": hashtags,
                "engagement_question": self._extract_question(response) if include_question else "",
                "optimal_post_time": self._get_optimal_time(platform),
                "metadata": {
                    "generated_by": "groq_api",
                    "company": brand_voice.company_name,
                    "platform": platform,
                    "tone": tone or brand_voice.tone,
                    "audience": brand_voice.target_audience,
                    "word_count": len(response.split())
                }
            }
            
            print(f"✓ API Success: {len(response)} characters")
            return result
            
        except Exception as e:
            # CRITICAL ERROR - No fallback, show error
            print(f"✗ API CRITICAL ERROR: {e}")
            raise Exception(f"API Generation Failed: {str(e)}. Check your GROQ_API_KEY and internet connection.")
    
    def _build_complete_prompt(self, platform: str, topic: str, brand_voice: BrandVoice,
                              tone: Optional[str], include_hashtags: bool,
                              include_question: bool, call_to_action: str) -> str:
        """Build comprehensive prompt with ALL parameters"""
        
        # Platform-specific instructions
        platform_guides = {
            "LinkedIn": "Professional, business-focused, 150-300 words, industry insights, thought leadership",
            "Twitter": "Concise, engaging, under 280 characters, conversational, use emojis sparingly",
            "Instagram": "Visual-first, engaging storytelling, 100-150 words, use emojis, ask questions",
            "Facebook": "Community-focused, conversational, 100-200 words, encourage comments and shares"
        }
        
        platform_guide = platform_guides.get(platform, "Professional social media post")
        
        # Build prompt parts
        prompt_parts = [
            f"Create a {platform} social media post about: {topic}",
            "",
            "=== COMPANY BRAND VOICE ===",
            f"Company Name: {brand_voice.company_name}",
            f"Brand Tone: {tone or brand_voice.tone}",
            f"Personality Traits: {', '.join(brand_voice.personality_traits)}",
            f"Target Audience: {brand_voice.target_audience}",
            f"Content Focus Areas: {', '.join(brand_voice.content_pillars)}",
            f"Avoid These Topics: {', '.join(brand_voice.forbidden_topics)}",
            "",
            f"=== PLATFORM REQUIREMENTS ===",
            f"Platform: {platform}",
            f"Style: {platform_guide}",
            "",
            "=== CONTENT REQUIREMENTS ===",
            "1. Write in the exact brand tone specified above",
            "2. Address the target audience directly",
            "3. Include specific, actionable insights (not generic statements)",
            "4. Sound like a real expert in this field",
            "",
            "=== FORMATTING ===",
            "Use appropriate line breaks and formatting for the platform.",
            f"{'Include 3-5 relevant hashtags' if include_hashtags else 'Do not include hashtags'}",
            f"{'Include an engaging question for audience interaction' if include_question else ''}",
            f"{f'Include a call-to-action about: {call_to_action}' if call_to_action else ''}",
            "",
            "=== CRITICAL INSTRUCTIONS ===",
            "DO NOT use placeholder text like 'Key insight 1' or generic statements",
            "DO reference the company name naturally in the content",
            "DO adapt the tone exactly as specified",
            "DO provide specific insights about the topic",
            "DO format it ready-to-post on the specified platform",
            "",
            "Now create the post:"
        ]
        
        return "\n".join(prompt_parts)
    
    def _call_groq_api(self, prompt: str) -> str:
        """Call Groq API with error handling"""
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are a professional social media content creator who follows brand guidelines precisely."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "model": "mistral-saba-24b",
            "temperature": 0.8,  # More creative
            "max_tokens": 500,
            "max_completion_tokens": 400
        }
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code != 200:
            error_msg = f"API Error {response.status_code}"
            try:
                error_data = response.json()
                if 'error' in error_data:
                    error_msg += f": {error_data['error'].get('message', 'Unknown error')}"
            except:
                error_msg += f": {response.text[:100]}"
            raise Exception(error_msg)
        
        data = response.json()
        return data["choices"][0]["message"]["content"]
    
    def _extract_question(self, text: str) -> str:
        """Extract question from text"""
        sentences = text.replace('?', '?|').replace('!', '!|').replace('.', '.|').split('|')
        questions = [s.strip() for s in sentences if '?' in s]
        return questions[0] if questions else "What are your thoughts?"
    
    def _get_optimal_time(self, platform: str) -> str:
        times = {
            "LinkedIn": "8:30 AM",
            "Twitter": "12:00 PM", 
            "Instagram": "5:00 PM",
            "Facebook": "9:00 AM"
        }
        return times.get(platform, "10:00 AM")
