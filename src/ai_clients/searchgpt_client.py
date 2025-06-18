import os
import openai
import requests
import json
import time
import logging
from typing import Dict, Any, Optional, List

def check_searchgpt_api_keys() -> bool:
    """Check if required API keys for SearchGPT-like functionality are configured."""
    openai_key = os.getenv('OPENAI_API_KEY')
    serper_key = os.getenv('SERPER_API_KEY')
    
    if not openai_key:
        print("❌ OPENAI_API_KEY environment variable not set")
        print("   Get your API key from: https://platform.openai.com")
        return False
        
    if not serper_key:
        print("❌ SERPER_API_KEY environment variable not set")
        print("   Get your API key from: https://serper.dev")
        print("   Note: SearchGPT functionality requires web search capabilities")
        return False
        
    return True

def search_web(query: str, num_results: int = 5) -> List[Dict[str, Any]]:
    """
    Perform web search using Serper API.
    
    Args:
        query: Search query
        num_results: Number of search results to return
        
    Returns:
        List of search results with title, link, snippet
    """
    serper_key = os.getenv('SERPER_API_KEY')
    url = "https://google.serper.dev/search"
    
    payload = {
        "q": query,
        "num": num_results
    }
    
    headers = {
        "X-API-KEY": serper_key,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            results = []
            organic_results = data.get('organic', [])
            
            for result in organic_results[:num_results]:
                results.append({
                    'title': result.get('title', ''),
                    'link': result.get('link', ''),
                    'snippet': result.get('snippet', '')
                })
                
            return results
        else:
            logging.error(f"Serper API error {response.status_code}: {response.text}")
            return []
            
    except Exception as e:
        logging.error(f"Web search error: {str(e)}")
        return []

def call_searchgpt_with_prompts(
    system_prompt: str,
    user_prompt: str,
    model: str = "gpt-4o-mini",
    max_tokens: int = 1024,
    temperature: float = 0.7,
    max_retries: int = 3,
    search_enabled: bool = True
) -> Dict[str, Any]:
    """
    Call SearchGPT-like functionality using OpenAI API with web search enhancement.
    
    Args:
        system_prompt: System message to set context
        user_prompt: User's input prompt
        model: OpenAI model to use
        max_tokens: Maximum tokens in response
        temperature: Sampling temperature
        max_retries: Maximum number of retry attempts
        search_enabled: Whether to enhance with web search
        
    Returns:
        Dictionary containing response, usage stats, and metadata
    """
    if not check_searchgpt_api_keys():
        return {
            'error': 'SearchGPT API keys not configured',
            'content': None,
            'usage': {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0},
            'cost': 0.0,
            'model': model,
            'search_results': []
        }
    
    openai.api_key = os.getenv('OPENAI_API_KEY')
    
    search_results = []
    enhanced_prompt = user_prompt
    
    # Enhance prompt with web search if enabled
    if search_enabled:
        # Extract search query from user prompt or use it directly
        search_query = user_prompt
        
        # Perform web search
        search_results = search_web(search_query)
        
        if search_results:
            # Format search results for context
            search_context = "Recent web search results:\n\n"
            for i, result in enumerate(search_results, 1):
                search_context += f"{i}. {result['title']}\n"
                search_context += f"   {result['snippet']}\n"
                search_context += f"   Source: {result['link']}\n\n"
            
            # Enhance the prompt with search context
            enhanced_prompt = f"{search_context}\nUser Question: {user_prompt}\n\nPlease provide a comprehensive answer using the above search results and your knowledge. Include relevant sources when appropriate."
    
    # Prepare messages for OpenAI API
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": enhanced_prompt}
    ]
    
    for attempt in range(max_retries):
        try:
            logging.info(f"Calling OpenAI API for SearchGPT (attempt {attempt + 1}/{max_retries})")
            
            response = openai.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            # Extract response content
            content = response.choices[0].message.content
            
            # Extract usage information
            usage = response.usage
            input_tokens = usage.prompt_tokens
            output_tokens = usage.completion_tokens
            total_tokens = usage.total_tokens
            
            # Calculate cost based on model pricing
            cost = calculate_searchgpt_cost(model, input_tokens, output_tokens)
            
            return {
                'content': content,
                'usage': {
                    'input_tokens': input_tokens,
                    'output_tokens': output_tokens,
                    'total_tokens': total_tokens
                },
                'cost': cost,
                'model': model,
                'provider': 'searchgpt',
                'search_results': search_results,
                'search_enhanced': search_enabled and len(search_results) > 0
            }
            
        except openai.RateLimitError as e:
            # Rate limit exceeded
            logging.warning(f"Rate limit exceeded. Waiting 60 seconds...")
            if attempt < max_retries - 1:
                time.sleep(60)
                continue
            else:
                return {
                    'error': f'Rate limit exceeded after {max_retries} attempts',
                    'content': None,
                    'usage': {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0},
                    'cost': 0.0,
                    'model': model,
                    'search_results': search_results
                }
                
        except openai.APIError as e:
            # API error - retry with exponential backoff
            wait_time = (2 ** attempt) * 1  # 1, 2, 4 seconds
            logging.warning(f"OpenAI API error {e.status_code}: {str(e)}. Retrying in {wait_time}s...")
            if attempt < max_retries - 1:
                time.sleep(wait_time)
                continue
            else:
                return {
                    'error': f'OpenAI API error {e.status_code} after {max_retries} attempts: {str(e)}',
                    'content': None,
                    'usage': {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0},
                    'cost': 0.0,
                    'model': model,
                    'search_results': search_results
                }
                
        except Exception as e:
            logging.error(f"Unexpected error calling SearchGPT: {str(e)}")
            return {
                'error': f'Unexpected error: {str(e)}',
                'content': None,
                'usage': {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0},
                'cost': 0.0,
                'model': model,
                'search_results': search_results
            }

def calculate_searchgpt_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate cost for SearchGPT (OpenAI-based) usage based on model and token counts."""
    
    # OpenAI pricing (per 1M tokens) as of latest available data
    pricing = {
        "gpt-4o": [2.50, 10.00],
        "gpt-4o-mini": [0.15, 0.60],
        "gpt-4-turbo": [10.00, 30.00],
        "gpt-4": [30.00, 60.00],
        "gpt-3.5-turbo": [0.50, 1.50]
    }
    
    if model not in pricing:
        # Default to GPT-4o-mini pricing for unknown models
        input_cost_per_1k = 0.15 / 1000  # $0.15 per 1M tokens = $0.00015 per 1K
        output_cost_per_1k = 0.60 / 1000
    else:
        input_cost_per_1m, output_cost_per_1m = pricing[model]
        input_cost_per_1k = input_cost_per_1m / 1000
        output_cost_per_1k = output_cost_per_1m / 1000
    
    input_cost = (input_tokens / 1000) * input_cost_per_1k
    output_cost = (output_tokens / 1000) * output_cost_per_1k
    
    return input_cost + output_cost