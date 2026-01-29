"""
Production AI Content Agent with Grok API
Generates real, platform-specific content
"""

import os
import requests
import json
from typing import Dict, List, Optional
from dataclasses import dataclass
import base64
from PIL import Image
import io

@dataclass
class BrandVoice:
    company_name: str
    tone: str
    personality_traits: List[str]
    target_audience: str
    content_pillars: List[str]
    forbidden_topics: List[str]

class ContentAgent:
    def __init__(self, api_key: str):
        self.api_key = api_key or os.environ.get("GROQ_API_KEY") or os.environ.get("GROK_API_KEY")
        
        
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
        
        # Analyze media if provided
        media_context = self._analyze_media(media_files) if media_files else None
        
        # Construct detailed prompt
        prompt = self._construct_prompt(platform, topic, brand_voice, tone, media_context)
        
        try:
            # Call Grok API
            response = self._call_grok_api(prompt)
            
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
            # Fallback to template-based generation
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
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    
    def _analyze_media(self, media_files: List) -> str:
        """Extract context from uploaded media"""
        contexts = []
        
        for file in media_files:
            if file.type.startswith('image'):
                # For images, we can describe them
                try:
                    image = Image.open(file)
                    contexts.append(f"Image: {image.size[0]}x{image.size[1]} pixels, format: {image.format}")
                except:
                    contexts.append(f"Image file: {file.name}")
            
            elif file.type.startswith('video'):
                contexts.append(f"Video file: {file.name}")
        
        return " | ".join(contexts) if contexts else "Media files uploaded"
    
    def _parse_ai_response(self, response: str, platform: str) -> Dict:
        """Parse and clean AI response"""
        
        try:
            # Try to extract JSON
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            
            if json_match:
                data = json.loads(json_match.group())
                
                # Ensure required fields
                if "content" not in data:
                    data["content"] = response[:500]  # Fallback
                
                return data
        except:
            pass
        
        # Fallback parsing
        return {
            "content": response[:500],
            "hashtags": self._extract_hashtags(response),
            "engagement_question": "What are your thoughts?",
            "ai_notes": f"AI-generated {platform} content"
        }
    
    def _extract_hashtags(self, text: str) -> List[str]:
        """Extract hashtags from text"""
        import re
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
        
        templates = {
            "linkedin": f""" {topic}

At {brand_voice.company_name}, we're passionate about driving innovation. Here's what we're seeing in the market:

🔹 Key insight 1
🔹 Key insight 2  
🔹 Key insight 3

What challenges are you facing with {topic.split()[0]}? Share your experiences below!

#{brand_voice.company_name.replace(' ', '')} #Innovation #Tech""",
            
            "twitter": f"""Just explored {topic}!

The intersection of technology and business is evolving rapidly. Key takeaways:

• Point 1
• Point 2

Thoughts? #Tech #Business #AI""",
            
            "instagram": f""" Deep dive into {topic}!

{media_context or 'Visual exploration of technology trends'}

What excites you most about the future of tech? 

#TechLife #Innovation #FutureTech"""
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
                "ai_notes": "Generated from template (API unavailable)"
            }
        }
