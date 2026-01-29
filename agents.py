"""
Production AI Content Agent with Grok API
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
        self.api_key = api_key or os.environ.get("GROQ_API_KEY") or os.environ.get("GROK_API_KEY")
        #self.base_url = "https://api.x.ai/v1"
        
        # Debug output
        print(f"ContentAgent initialized")
        print(f"API Key available: {'YES' if self.api_key else 'NO'}")
        if self.api_key:
            print(f"Key starts with xai-: {self.api_key.startswith('xai-')}")
            print(f"Key length: {len(self.api_key)}")
        
        # Platform-specific templates
        self.platform_templates = {
            "linkedin": {
                "description": "Professional network for business content",
                "length": "150-300 words",
                "structure": "Hook, Value proposition, Insights, Call-to-action",
                "hashtag_count": "3-5",
                "tone": "Professional, insightful"
            },
            "twitter": {
                "description": "Fast-paced microblogging platform",
                "length": "240-280 characters",
                "structure": "Main point, Supporting detail, Hashtags",
                "hashtag_count": "2-3",
                "tone": "Concise, engaging"
            },
            "instagram": {
                "description": "Visual-first platform",
                "length": "100-150 words",
                "structure": "Caption, Storytelling, Questions, Hashtags",
                "hashtag_count": "5-10",
                "tone": "Engaging, visual-focused"
            }
        }
    
    def generate_content(self, platform: str, topic: str, brand_voice: BrandVoice,
                        tone: Optional[str] = None, media_files: List = None) -> Dict:
        """
        Generate high-quality, platform-specific content using Grok API
        """
        
        print(f"generate_content called for {platform}: {topic[:50]}...")
        
        # Analyze media if provided
        media_context = self._analyze_media(media_files) if media_files else None
        
        # Construct detailed prompt
        prompt = self._construct_prompt(platform, topic, brand_voice, tone, media_context)
        
        # Check if we have a valid API key
        has_valid_key = bool(self.api_key and len(self.api_key) > 20)
        
        if has_valid_key:
            try:
                print("Attempting Grok API call...")
                # Call Grok API
                response = self._call_grok_api(prompt)
                print("Grok API call successful")
                
                # Parse and structure response
                content_data = self._parse_ai_response(response, platform)
                
                # Add metadata
                content_data["metadata"] = {
                    "generated_by": "grok_api",
                    "platform": platform,
                    "tone": tone or brand_voice.tone,
                    "hashtags": content_data.get("hashtags", []),
                    "optimal_post_time": self._get_optimal_time(platform),
                    "ai_notes": content_data.get("ai_notes", ""),
                    "media_context": media_context
                }
                
                return content_data
                
            except Exception as e:
                print(f"Grok API failed: {str(e)}")
                # Fallback to template-based generation
                return self._generate_fallback_content(platform, topic, brand_voice, media_context)
        else:
            print("Using fallback (no valid API key)")
            return self._generate_fallback_content(platform, topic, brand_voice, media_context)
    
    def _construct_prompt(self, platform: str, topic: str, brand_voice: BrandVoice,
                         tone: Optional[str], media_context: Optional[str]) -> str:
        """Construct detailed prompt for Grok"""
        
        platform_spec = self.platform_templates.get(platform.lower(), self.platform_templates["linkedin"])
        
        prompt = f"""You are a professional social media content creator for {brand_voice.company_name}.

BRAND IDENTITY:
- Company: {brand_voice.company_name}
- Tone: {tone or brand_voice.tone}
- Personality: {', '.join(brand_voice.personality_traits)}
- Target Audience: {brand_voice.target_audience}
- Content Focus Areas: {', '.join(brand_voice.content_pillars)}
- NEVER mention: {', '.join(brand_voice.forbidden_topics)}

PLATFORM: {platform.upper()}
- Platform Type: {platform_spec['description']}
- Ideal Length: {platform_spec['length']}
- Structure: {platform_spec['structure']}
- Hashtags: {platform_spec['hashtag_count']}
- Tone: {platform_spec['tone']}

CONTENT BRIEF:
{topic}

{"MEDIA CONTEXT: " + media_context if media_context else "No media provided. Create compelling text content."}

SPECIFIC INSTRUCTIONS:
1. Create platform-optimized content
2. Include relevant hashtags (platform-appropriate count)
3. Add an engagement question for the audience
4. Provide optimal posting time based on {platform} audience behavior
5. Include a clear call-to-action

FORMAT YOUR RESPONSE AS JSON:
{{
    "content": "full post content here",
    "hashtags": ["#relevant1", "#relevant2"],
    "engagement_question": "question for audience",
    "optimal_post_time": "HH:MM AM/PM",
    "ai_notes": "brief explanation of why this content works for this platform"
}}"""

        return prompt
    
    def _call_grok_api(self, prompt: str) -> str:
        """Make actual API call to Grok"""
        
        if not self.api_key:
            raise Exception("No API key provided")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are a professional social media content creator specializing in platform-specific optimization."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "model": "grok-beta",
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            # Check response
            if response.status_code != 200:
                error_msg = f"API error {response.status_code}"
                try:
                    error_data = response.json()
                    if 'error' in error_data:
                        error_msg += f": {error_data['error'].get('message', 'Unknown error')}"
                except:
                    error_msg += f": {response.text[:100]}"
                print(error_msg)
                raise Exception(error_msg)
            
            return response.json()["choices"][0]["message"]["content"]
            
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            raise Exception(f"API request failed: {e}")
    
    def _analyze_media(self, media_files: List) -> str:
        """Extract context from uploaded media"""
        if not media_files:
            return None
        
        contexts = []
        for file in media_files:
            try:
                if hasattr(file, 'type') and file.type.startswith('image'):
                    contexts.append(f"Image: {file.name}")
                elif hasattr(file, 'type') and file.type.startswith('video'):
                    contexts.append(f"Video: {file.name}")
                else:
                    contexts.append(f"File: {file.name}")
            except:
                contexts.append("Media file")
        
        return " | ".join(contexts) if contexts else None
    
    def _parse_ai_response(self, response: str, platform: str) -> Dict:
        """Parse and clean AI response"""
        
        try:
            # Try to extract JSON
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            
            if json_match:
                data = json.loads(json_match.group())
                
                # Ensure required fields
                if "content" not in data:
                    data["content"] = response[:500]
                
                return data
        except json.JSONDecodeError as e:
            print(f"JSON parsing failed: {e}")
        
        # Fallback parsing
        return {
            "content": response[:500],
            "hashtags": self._extract_hashtags(response),
            "engagement_question": "What are your thoughts?",
            "ai_notes": f"AI-generated {platform} content"
        }
    
    def _extract_hashtags(self, text: str) -> List[str]:
        """Extract hashtags from text"""
        hashtags = re.findall(r'#\w+', text)
        return list(set(hashtags))[:5]  # Max 5 unique hashtags
    
    def _get_optimal_time(self, platform: str) -> str:
        """Get optimal posting time based on platform"""
        times = {
            "linkedin": "8:30 AM",
            "twitter": "12:00 PM",
            "instagram": "5:00 PM",
            "facebook": "9:00 AM"
        }
        return times.get(platform.lower(), "10:00 AM")
    
    def _generate_fallback_content(self, platform: str, topic: str, 
                                  brand_voice: BrandVoice, media_context: Optional[str]) -> Dict:
        """Generate fallback content if API fails"""
        
        # Use actual company name from brand_voice
        company = brand_voice.company_name
        topic_words = topic.split()
        main_topic = topic_words[0] if topic_words else "innovation"
        
        templates = {
            "linkedin": f"{topic}\n\nAt {company}, we're seeing transformative changes. Key insights:\n\n1. Strategic implementation of {main_topic.lower()}\n2. Integration challenges and solutions\n3. Measuring business impact\n\nWhat challenges are you facing with {main_topic.lower()} implementation?\n\n#{company.replace(' ', '')} #{main_topic.capitalize()} #DigitalTransformation",
            
            "twitter": f"Exploring {topic} today. Key points:\n\n1. Current trends\n2. Business implications\n3. Future outlook\n\nThoughts on this space?\n\n#{main_topic.capitalize()} #Tech #Innovation",
            
            "instagram": f"Deep dive into {topic}!\n\n{media_context or 'Visual exploration of modern technology'}\n\nWhat excites you most about {main_topic.lower()}? Share below!\n\n#{main_topic.capitalize()} #TechInnovation #FutureForward"
        }
        
        content = templates.get(platform.lower(), templates["linkedin"])
        
        return {
            "content": content,
            "hashtags": self._extract_hashtags(content),
            "engagement_question": "What are your thoughts?",
            "optimal_post_time": self._get_optimal_time(platform),
            "metadata": {
                "generated_by": "fallback_template",
                "platform": platform,
                "ai_notes": "Generated from fallback template"
            }
        }
