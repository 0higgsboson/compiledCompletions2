import os
import requests
import time
import logging
from typing import Dict, Any, Optional

def check_perplexity_api_key() -> bool:
    """Check if Perplexity API key is configured."""
    api_key = os.getenv('PERPLEXITY_API_KEY')
    if not api_key:
        print("❌ PERPLEXITY_API_KEY environment variable not set")
        print("   Get your API key from: https://www.perplexity.ai/settings/api")
        return False
    return True

def call_perplexity_with_prompts(
    system_prompt: str, 
    user_prompt: str, 
    model: str = "llama-3.1-sonar-small-128k-online",
    max_tokens: int = 1024,
    temperature: float = 0.7,
    max_retries: int = 3
) -> Dict[str, Any]:
    """
    Call Perplexity API with retry logic for rate limits and server errors.
    
    Args:
        system_prompt: System message to set context
        user_prompt: User's input prompt
        model: Perplexity model to use
        max_tokens: Maximum tokens in response
        temperature: Sampling temperature
        max_retries: Maximum number of retry attempts
    
    Returns:
        Dictionary containing response, usage stats, and metadata
    """
    if not check_perplexity_api_key():
        return {
            'error': 'Perplexity API key not configured',
            'content': None,
            'usage': {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0},
            'cost': 0.0,
            'model': model
        }
    
    api_key = os.getenv('PERPLEXITY_API_KEY')
    url = "https://api.perplexity.ai/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": False
    }
    
    for attempt in range(max_retries):
        try:
            logging.info(f"Calling Perplexity API (attempt {attempt + 1}/{max_retries})")
            
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract response content
                content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
                
                # Extract usage information
                usage = data.get('usage', {})
                input_tokens = usage.get('prompt_tokens', 0)
                output_tokens = usage.get('completion_tokens', 0)
                total_tokens = usage.get('total_tokens', input_tokens + output_tokens)
                
                # Calculate cost based on model pricing
                cost = calculate_perplexity_cost(model, input_tokens, output_tokens)
                
                return {
                    'content': content,
                    'usage': {
                        'input_tokens': input_tokens,
                        'output_tokens': output_tokens,
                        'total_tokens': total_tokens
                    },
                    'cost': cost,
                    'model': model,
                    'provider': 'perplexity'
                }
            
            elif response.status_code == 429:
                # Rate limit exceeded
                retry_after = int(response.headers.get('Retry-After', 60))
                logging.warning(f"Rate limit exceeded. Waiting {retry_after} seconds...")
                if attempt < max_retries - 1:
                    time.sleep(retry_after)
                    continue
                else:
                    return {
                        'error': f'Rate limit exceeded after {max_retries} attempts',
                        'content': None,
                        'usage': {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0},
                        'cost': 0.0,
                        'model': model
                    }
            
            elif response.status_code >= 500:
                # Server error - retry with exponential backoff
                wait_time = (2 ** attempt) * 1  # 1, 2, 4 seconds
                logging.warning(f"Server error {response.status_code}. Retrying in {wait_time}s...")
                if attempt < max_retries - 1:
                    time.sleep(wait_time)
                    continue
                else:
                    return {
                        'error': f'Server error {response.status_code} after {max_retries} attempts',
                        'content': None,
                        'usage': {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0},
                        'cost': 0.0,
                        'model': model
                    }
            
            else:
                # Other client errors
                error_msg = response.text
                logging.error(f"Perplexity API error {response.status_code}: {error_msg}")
                return {
                    'error': f'API error {response.status_code}: {error_msg}',
                    'content': None,
                    'usage': {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0},
                    'cost': 0.0,
                    'model': model
                }
        
        except requests.exceptions.Timeout:
            logging.warning(f"Request timeout (attempt {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            else:
                return {
                    'error': f'Request timeout after {max_retries} attempts',
                    'content': None,
                    'usage': {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0},
                    'cost': 0.0,
                    'model': model
                }
        
        except Exception as e:
            logging.error(f"Unexpected error calling Perplexity API: {str(e)}")
            return {
                'error': f'Unexpected error: {str(e)}',
                'content': None,
                'usage': {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0},
                'cost': 0.0,
                'model': model
            }

def calculate_perplexity_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate cost for Perplexity API usage based on model and token counts."""
    
    # Perplexity pricing (per 1M tokens) as of latest available data
    # Note: These are approximate prices - check Perplexity's current pricing
    pricing = {
        "llama-3.1-sonar-small-128k-online": [0.20, 0.20],  # Same price for input/output
        "llama-3.1-sonar-large-128k-online": [1.00, 1.00],
        "llama-3.1-sonar-huge-128k-online": [5.00, 5.00],
        "llama-3.1-8b-instruct": [0.20, 0.20],
        "llama-3.1-70b-instruct": [1.00, 1.00],
        "mixtral-8x7b-instruct": [0.60, 0.60]
    }
    
    if model not in pricing:
        # Default pricing for unknown models
        input_cost_per_1k = 0.20 / 1000  # $0.20 per 1M tokens = $0.0002 per 1K
        output_cost_per_1k = 0.20 / 1000
    else:
        input_cost_per_1m, output_cost_per_1m = pricing[model]
        input_cost_per_1k = input_cost_per_1m / 1000
        output_cost_per_1k = output_cost_per_1m / 1000
    
    input_cost = (input_tokens / 1000) * input_cost_per_1k
    output_cost = (output_tokens / 1000) * output_cost_per_1k
    
    return input_cost + output_cost