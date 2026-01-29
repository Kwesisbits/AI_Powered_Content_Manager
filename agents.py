import os
import requests
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import re
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class BrandVoice:
    company_name: str
    tone: str
    personality_traits: List[str]
    target_audience: str
    content_pillars: List[str]
    forbidden_topics: List[str]


class ContentAgentException(Exception):
    pass


class APIConnectionException(ContentAgentException):
    pass


class InvalidAPIKeyException(ContentAgentException):
    pass


class RateLimitException(ContentAgentException):
    pass


class ContentAgent:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        
        if not self.api_key:
            raise InvalidAPIKeyException(
                "No Groq API key provided. Set GROQ_API_KEY environment variable or pass api_key parameter."
            )
        
        if not self.api_key.startswith("gsk_"):
            raise InvalidAPIKeyException(
                "Invalid Groq API key format. Key should start with 'gsk_'"
            )
        
        self.base_url = "https://api.groq.com/openai/v1"
        self.model = "mixtral-8x7b-32768"
        self.timeout = 30
        self.max_retries = 3
        
        logger.info("ContentAgent initialized with Groq API")
    
    def test_connection(self) -> bool:
        """
        Test if API connection works.
        Returns True if connection successful, False otherwise.
        """
        try:
            logger.info("Testing Groq API connection...")
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self._get_headers(),
                json={
                    "messages": [{"role": "user", "content": "say hello"}],
                    "model": self.model,
                    "max_tokens": 10,
                    "temperature": 0.1
                },
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("Groq API connection successful")
                return True
            else:
                logger.error(f"API returned status {response.status_code}: {response.text[:200]}")
                return False
                
        except requests.exceptions.Timeout:
            logger.error("API request timed out (connection test)")
            return False
        except requests.exceptions.ConnectionError:
            logger.error("Cannot connect to Groq API endpoint")
            return False
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False
    
    def generate_content(
        self,
        platform: str,
        topic: str,
        brand_voice: BrandVoice,
        tone: Optional[str] = None,
        media_files: List = None
    ) -> Dict:
        """
        Generate content for specified platform.
        
        Args:
            platform: Target platform (linkedin, instagram, twitter)
            topic: Content topic
            brand_voice: BrandVoice configuration
            tone: Optional tone override
            media_files: Optional media context
            
        Returns:
            Dictionary with generated content and metadata
            
        Raises:
            ContentAgentException: If content generation fails
        """
        try:
            logger.info(f"Generating content for {platform} about '{topic}'")
            
            if not self._validate_inputs(platform, topic, brand_voice):
                raise ContentAgentException("Invalid input parameters")
            
            prompt = self._construct_prompt(platform, topic, brand_voice, tone, media_files)
            response_text = self._call_groq_api(prompt)
            
            if not response_text or response_text.strip() == "":
                raise ContentAgentException("API returned empty response")
            
            content_data = self._parse_ai_response(response_text, platform)
            content_data["metadata"] = {
                "generated_by": "groq_api",
                "platform": platform,
                "model": self.model,
                "hashtags": content_data.get("hashtags", []),
                "topic": topic
            }
            
            logger.info(f"Content generated successfully for {platform}")
            return content_data
            
        except (InvalidAPIKeyException, APIConnectionException, RateLimitException):
            raise
        except Exception as e:
            logger.error(f"Content generation failed: {str(e)}")
            raise ContentAgentException(f"Failed to generate content: {str(e)}")
    
    def _validate_inputs(self, platform: str, topic: str, brand_voice: BrandVoice) -> bool:
        """Validate input parameters"""
        if not platform or not isinstance(platform, str):
            logger.error("Invalid platform parameter")
            return False
        
        if not topic or not isinstance(topic, str):
            logger.error("Invalid topic parameter")
            return False
        
        if not brand_voice:
            logger.error("BrandVoice not provided")
            return False
        
        if not brand_voice.company_name:
            logger.error("BrandVoice missing company_name")
            return False
        
        return True
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with API key"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def _construct_prompt(
        self,
        platform: str,
        topic: str,
        brand_voice: BrandVoice,
        tone: Optional[str],
        media_context: Optional[str]
    ) -> str:
        """Construct the prompt for content generation"""
        
        platform_guidelines = self._get_platform_guidelines(platform)
        
        prompt = f"""Generate a {platform} social media post with the following requirements:

Topic: {topic}
Company: {brand_voice.company_name}
Brand Tone: {tone or brand_voice.tone}
Target Audience: {brand_voice.target_audience}
Content Pillars: {', '.join(brand_voice.content_pillars)}
Topics to Avoid: {', '.join(brand_voice.forbidden_topics)}

Platform Guidelines:
{platform_guidelines}

Requirements:
- Create engaging, authentic content
- Include 3-5 relevant hashtags
- Add a question to encourage engagement
- Provide value to the audience
- Keep professional yet conversational tone
- Ensure content aligns with brand voice

Generate ONLY the social media post content. Do not include any explanations or metadata."""
        
        return prompt
    
    def _get_platform_guidelines(self, platform: str) -> str:
        """Get platform-specific content guidelines"""
        guidelines = {
            "linkedin": """- Use professional yet approachable language
- Include industry insights or thought leadership
- Maximum 1300 characters recommended
- Use line breaks for readability
- Include relevant professional hashtags
- End with an engaging question for discussion""",
            
            "instagram": """- Use conversational, relatable language
- Include emojis where appropriate
- Maximum 2200 characters
- Use line breaks and spacing for visual appeal
- Include 10-15 relevant hashtags
- End with a call-to-action or question
- Mention visual elements if applicable""",
            
            "twitter": """- Keep within 280 character limit
- Use clear, concise language
- Include 2-3 relevant hashtags
- Can include a question or statement
- Avoid unnecessary jargon
- Make it shareable and memorable"""
        }
        
        return guidelines.get(platform.lower(), guidelines["linkedin"])
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((APIConnectionException, RateLimitException))
    )
    def _call_groq_api(self, prompt: str) -> str:
        """
        Call Groq API with automatic retry logic.
        
        Raises:
            InvalidAPIKeyException: If API key is invalid
            APIConnectionException: If connection fails
            RateLimitException: If rate limited
            ContentAgentException: For other API errors
        """
        url = f"{self.base_url}/chat/completions"
        
        payload = {
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "model": self.model,
            "temperature": 0.7,
            "max_tokens": 1000,
            "top_p": 1
        }
        
        logger.debug(f"Calling Groq API endpoint: {url}")
        
        try:
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=self.timeout
            )
            
            return self._handle_api_response(response)
            
        except requests.exceptions.Timeout:
            logger.warning("API request timed out")
            raise APIConnectionException("API request timed out. Retrying...")
        
        except requests.exceptions.ConnectionError as e:
            logger.warning(f"Connection error: {str(e)}")
            raise APIConnectionException("Network connection failed. Retrying...")
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            raise ContentAgentException(f"Request failed: {str(e)}")
        
        except Exception as e:
            logger.error(f"Unexpected error in API call: {str(e)}")
            raise ContentAgentException(f"Unexpected error: {str(e)}")
    
    def _handle_api_response(self, response: requests.Response) -> str:
        """
        Handle API response and raise appropriate exceptions.
        
        Returns:
            Generated content text
            
        Raises:
            InvalidAPIKeyException: For 401 errors
            RateLimitException: For 429 errors
            ContentAgentException: For other errors
        """
        status_code = response.status_code
        
        if status_code == 200:
            try:
                response_json = response.json()
                
                if not response_json.get("choices"):
                    raise ContentAgentException("No choices in API response")
                
                content = response_json["choices"][0].get("message", {}).get("content")
                
                if not content:
                    raise ContentAgentException("No content in API response")
                
                return content
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse API response JSON: {str(e)}")
                raise ContentAgentException(f"Invalid JSON in response: {str(e)}")
        
        elif status_code == 401:
            logger.error("Authentication failed - invalid API key")
            raise InvalidAPIKeyException("Invalid Groq API key. Check your credentials.")
        
        elif status_code == 429:
            logger.warning("Rate limit exceeded")
            raise RateLimitException("Rate limit exceeded. Retrying...")
        
        elif status_code == 400:
            error_msg = response.text[:300]
            logger.error(f"Bad request: {error_msg}")
            raise ContentAgentException(f"Bad request to API: {error_msg}")
        
        elif status_code == 500:
            logger.error("API server error")
            raise ContentAgentException("Groq API server error. Please retry later.")
        
        elif status_code == 503:
            logger.error("API service unavailable")
            raise ContentAgentException("Groq API service unavailable. Please retry later.")
        
        else:
            error_msg = response.text[:300]
            logger.error(f"API error {status_code}: {error_msg}")
            raise ContentAgentException(f"API error {status_code}: {error_msg}")
    
    def _parse_ai_response(self, response: str, platform: str) -> Dict:
        """
        Parse AI response and extract content components.
        
        Args:
            response: Raw response from API
            platform: Target platform
            
        Returns:
            Dictionary with parsed content and metadata
        """
        return {
            "content": response.strip(),
            "hashtags": self._extract_hashtags(response),
            "engagement_question": self._extract_engagement_question(response),
            "platform": platform,
            "character_count": len(response)
        }
    
    def _extract_hashtags(self, text: str) -> List[str]:
        """Extract unique hashtags from text"""
        try:
            hashtags = re.findall(r'#\w+', text)
            unique_hashtags = list(set(hashtags))
            logger.debug(f"Extracted {len(unique_hashtags)} unique hashtags")
            return unique_hashtags
        except Exception as e:
            logger.warning(f"Error extracting hashtags: {str(e)}")
            return []
    
    def _extract_engagement_question(self, text: str) -> Optional[str]:
        """Extract engagement question from text"""
        try:
            sentences = re.split(r'[.!?]+', text)
            for sentence in sentences:
                if '?' in sentence:
                    cleaned = sentence.strip()
                    if cleaned:
                        return cleaned
            return None
        except Exception as e:
            logger.warning(f"Error extracting engagement question: {str(e)}")
            return None


class ContentGenerationPipeline:
    """
    High-level pipeline for content generation with error recovery.
    """
    
    def __init__(self, api_key: str = None):
        try:
            self.agent = ContentAgent(api_key=api_key)
            self.is_ready = self.agent.test_connection()
            
            if not self.is_ready:
                logger.error("Content generation pipeline not ready - API connection failed")
            else:
                logger.info("Content generation pipeline initialized successfully")
                
        except InvalidAPIKeyException as e:
            logger.error(f"Pipeline initialization failed: {str(e)}")
            self.is_ready = False
            raise
    
    def generate(
        self,
        platform: str,
        topic: str,
        brand_voice: BrandVoice,
        tone: Optional[str] = None
    ) -> Tuple[bool, Dict]:
        """
        Generate content with error handling.
        
        Args:
            platform: Target platform
            topic: Content topic
            brand_voice: Brand voice configuration
            tone: Optional tone override
            
        Returns:
            Tuple of (success: bool, result: Dict)
            If success is False, result contains error information
        """
        if not self.is_ready:
            return False, {
                "error": "Pipeline not initialized",
                "details": "API connection test failed"
            }
        
        try:
            content = self.agent.generate_content(
                platform=platform,
                topic=topic,
                brand_voice=brand_voice,
                tone=tone
            )
            
            return True, content
            
        except InvalidAPIKeyException as e:
            logger.error(f"Authentication error: {str(e)}")
            return False, {
                "error": "authentication_failed",
                "details": str(e)
            }
        
        except RateLimitException as e:
            logger.error(f"Rate limit error: {str(e)}")
            return False, {
                "error": "rate_limit_exceeded",
                "details": str(e)
            }
        
        except APIConnectionException as e:
            logger.error(f"Connection error: {str(e)}")
            return False, {
                "error": "connection_failed",
                "details": str(e)
            }
        
        except ContentAgentException as e:
            logger.error(f"Generation error: {str(e)}")
            return False, {
                "error": "generation_failed",
                "details": str(e)
            }
        
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return False, {
                "error": "unexpected_error",
                "details": str(e)
            }


if __name__ == "__main__":
    test_brand = BrandVoice(
        company_name="TechCorp",
        tone="professional yet approachable",
        personality_traits=["innovative", "trustworthy", "forward-thinking"],
        target_audience="tech professionals and business leaders",
        content_pillars=["innovation", "thought leadership", "industry insights"],
        forbidden_topics=["politics", "controversial topics", "competitor bashing"]
    )
    
    try:
        pipeline = ContentGenerationPipeline()
        
        success, result = pipeline.generate(
            platform="linkedin",
            topic="AI and automation in business",
            brand_voice=test_brand,
            tone="informative"
        )
        
        if success:
            print("Content generated successfully:")
            print(result["content"])
            print(f"Hashtags: {result['hashtags']}")
        else:
            print(f"Generation failed: {result['error']}")
            print(f"Details: {result['details']}")
            
    except Exception as e:
        print(f"Pipeline error: {str(e)}")
