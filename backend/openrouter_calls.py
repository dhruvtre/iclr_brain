
import requests
import json
from backend.config import OPENROUTER_API_KEY, logger

def send_ai_request(prompt, model, temperature=0.7, max_tokens=None):
    """Send a request to the OpenRouter API and return the response"""
    logger.info(f"Sending request to OpenRouter, model: {model}")
    logger.info(f"Request payload prepared with prompt length: {len(prompt)} characters")
    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}"
            },
            data=json.dumps({
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt,
                        "temperature": temperature,
                        "max_tokens": None
                    }
                ]
            })
        )
        logger.info(f"Received response from OpenRouter, status: {response.status_code}")
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.info(f"OpenRouter API request failed: {str(e)}")
        return {
            'success': False,
            'error': f"Request failed: {str(e)}"
        }

def parse_ai_response(response):
    """Extract the content and usage metrics from API response"""
    logger.info("Parsing OpenRouter API response")
    try:
        content = response['choices'][0]['message']['content']
        usage = response['usage']
        logger.info(f"Successfully parsed response with {usage.get('total_tokens', 'unknown')} total tokens")
        return {
            'content': content,
            'usage': usage,
            'success': True
        }
    except (KeyError, IndexError) as e:
        logger.error(f"Failed to parse OpenRouter response: {str(e)}")
        return {
            'content': None,
            'usage': None,
            'success': False,
            'error': str(e),
            'response': response
        }