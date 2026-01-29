"""
Production AI Content Agent with Groq API
Generates real, platform-specific content
"""

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
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable is required")
        
        self.base_url = "https://api.groq.com/openai/v1"
        print(f"✓ Agent initialized for {self.base_url}")
    
    def generate_content(self, platform: str, topic: str, brand_voice: BrandVoice,
                        tone: Optional[str] = None, media_files: List = None,
                        include_hashtags: bool = True, include_question: bool = True,
                        call_to_action: str = None) -> Dict:
        """
        Generate AI content - NO FALLBACK - API CALL ONLY
        """
        
        # Get media context from uploaded files
        media_context = self._get_media_context(media_files)
        
        # Build detailed prompt with ALL parameters
        prompt = self._build_complete_prompt(
            platform=platform,
            topic=topic,
            brand_voice=brand_voice,
            tone=tone,
            media_context=media_context,
            include_hashtags=include_hashtags,
            include_question=include_question,
            call_to_action=call_to_action
        )
        
        print(f"\n🔧 SENDING TO API:")
        print(f"   Company: {brand_voice.company_name}")
        print(f"   Platform: {platform}")
        print(f"   Tone: {tone or brand_voice.tone}")
        print(f"   Topic: {topic[:50]}...")
        if media_context:
            print(f"   Media: {media_context}")
        
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
            
            # Extract engagement question
            engagement_question = self._extract_question(response) if include_question else ""
            
            # Build result
            result = {
                "content": response.strip(),
                "hashtags": hashtags,
                "engagement_question": engagement_question,
                "optimal_post_time": self._get_optimal_time(platform),
                "metadata": {
                    "generated_by": "groq_api",
                    "company": brand_voice.company_name,
                    "platform": platform,
                    "tone": tone or brand_voice.tone,
                    "audience": brand_voice.target_audience,
                    "media_context": media_context,
                    "word_count": len(response.split())
                }
            }
            
            print(f"✓ API Success: {len(response)} characters")
            return result
            
        except Exception as e:
            # CRITICAL ERROR - No fallback, show error
            print(f"✗ API CRITICAL ERROR: {e}")
            raise Exception(f"API Generation Failed: {str(e)}. Check your GROQ_API_KEY and internet connection.")
    
    def _get_media_context(self, media_files: List) -> str:
        """Extract context from uploaded media files"""
        if not media_files:
            return ""
        
        context_parts = []
        for file in media_files:
            try:
                # Get file info
                if hasattr(file, 'name'):
                    filename = file.name
                    # Check file type
                    if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                        context_parts.append(f"Image: {filename}")
                    elif filename.lower().endswith(('.mp4', '.mov', '.avi')):
                        context_parts.append(f"Video: {filename}")
                    elif filename.lower().endswith(('.pdf', '.doc', '.docx')):
                        context_parts.append(f"Document: {filename}")
                    else:
                        context_parts.append(f"File: {filename}")
                else:
                    context_parts.append("Media file")
            except Exception as e:
                print(f"Error processing media file: {e}")
                context_parts.append("Media file")
        
        return " | ".join(context_parts) if context_parts else ""
    
    def _build_complete_prompt(self, platform: str, topic: str, brand_voice: BrandVoice,
                              tone: Optional[str], media_context: str,
                              include_hashtags: bool, include_question: bool, 
                              call_to_action: str) -> str:
        """Build comprehensive prompt with ALL parameters"""
        
        # Platform-specific instructions
        platform_guides = {
            "LinkedIn": "Professional, business-focused, 150-300 words, industry insights, thought leadership. Use a professional tone with data-driven insights.",
            "Twitter": "Concise, engaging, under 280 characters, conversational, use 1-2 relevant emojis. Focus on key takeaways and conversation starters.",
            "Instagram": "Visual-first, engaging storytelling, 100-150 words, use emojis, ask questions. Write for a visual platform with emphasis on aesthetics.",
            "Facebook": "Community-focused, conversational, 100-200 words, encourage comments and shares. Focus on community engagement and discussion.",
            "Blog": "In-depth, detailed, 300-500 words, educational, include subheadings. Provide comprehensive analysis and actionable insights."
        }
        
        platform_guide = platform_guides.get(platform, "Professional social media post")
        
        # Build prompt parts
        prompt_parts = [
            f"Create a {platform} social media post about: {topic}",
            "",
            "=== COMPANY BRAND VOICE ===",
            f"Company Name: {brand_voice.company_name} (MUST mention this company name in the post)",
            f"Brand Tone: {tone or brand_voice.tone} (WRITE IN THIS EXACT TONE throughout)",
            f"Personality Traits: {', '.join(brand_voice.personality_traits)} (reflect these traits in the writing)",
            f"Target Audience: {brand_voice.target_audience} (address this specific audience)",
            f"Content Focus Areas: {', '.join(brand_voice.content_pillars)}",
            f"Avoid These Topics: {', '.join(brand_voice.forbidden_topics)} (never mention these)",
            "",
            f"=== PLATFORM REQUIREMENTS ===",
            f"Platform: {platform}",
            f"Style: {platform_guide}",
            "",
        ]
        
        # Add media context if provided
        if media_context:
            prompt_parts.append("=== MEDIA CONTEXT ===")
            prompt_parts.append(f"Uploaded media files: {media_context}")
            prompt_parts.append("Incorporate context from these media files in the post.")
            prompt_parts.append("")
        
        prompt_parts.extend([
            "=== CONTENT REQUIREMENTS ===",
            "1. Write in the exact brand tone specified above",
            "2. Address the target audience directly",
            "3. Include specific, actionable insights (not generic statements)",
            "4. Sound like a real expert in this field",
            "5. Make it engaging and share-worthy",
            "",
            "=== FORMATTING ===",
            f"Platform: {platform} - use appropriate formatting and line breaks",
            f"{'Include 3-5 relevant hashtags at the end' if include_hashtags else 'Do not include hashtags'}",
            f"{'Include an engaging question for audience interaction' if include_question else ''}",
            f"{f'Include a clear call-to-action about: {call_to_action}' if call_to_action else ''}",
            "",
            "=== CRITICAL INSTRUCTIONS ===",
            "DO NOT use placeholder text like 'Key insight 1' or generic statements",
            f"DO reference '{brand_voice.company_name}' naturally in the content",
            "DO adapt the tone exactly as specified",
            "DO provide specific insights about the topic",
            "DO format it ready-to-post on the specified platform",
            f"{'DO consider the media context when writing' if media_context else ''}",
            "",
            f"Now create the {platform} post for {brand_voice.company_name}:"
        ])
        
        return "\n".join(prompt_parts)
    
    def _call_groq_api(self, prompt: str) -> str:
        """Call Groq API with error handling"""
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Using llama-3.3-70b-versatile as requested
        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are a professional social media content creator who follows brand guidelines precisely. You create engaging, platform-specific content."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "model": "llama-3.3-70b-versatile",  # Updated to working model
            "temperature": 0.8,  # Creative but consistent
            "max_tokens": 500,
            "top_p": 0.9,
            "stream": False
        }
        
        print(f"   Using model: {payload['model']}")
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            print(f"   Response status: {response.status_code}")
            
            if response.status_code != 200:
                error_msg = f"API Error {response.status_code}"
                try:
                    error_data = response.json()
                    if 'error' in error_data:
                        error_msg += f": {error_data['error'].get('message', 'Unknown error')}"
                except:
                    error_msg += f": {response.text[:100]}"
                print(f"   Error details: {error_msg}")
                raise Exception(error_msg)
            
            response_json = response.json()
            return response_json["choices"][0]["message"]["content"]
            
        except requests.exceptions.RequestException as e:
            print(f"   Network error: {e}")
            raise Exception(f"Network error: {e}")
    
    def _extract_question(self, text: str) -> str:
        """Extract question from text"""
        sentences = text.replace('?', '?|').replace('!', '!|').replace('.', '.|').split('|')
        questions = [s.strip() for s in sentences if '?' in s]
        return questions[0] if questions else "What are your thoughts?"
    
    def _get_optimal_time(self, platform: str) -> str:
        """Get optimal posting time based on platform"""
        times = {
            "LinkedIn": "8:30 AM",
            "Twitter": "12:00 PM", 
            "Instagram": "5:00 PM",
            "Facebook": "9:00 AM",
            "Blog": "10:00 AM"
        }
        return times.get(platform, "10:00 AM")
