#!/usr/bin/env python3
"""
@author Sid Shaik (@0higgsboson) 
Licensed under Apache 2.0

OpenAI API client for making requests to OpenAI's API
"""

import openai
import os

def call_openai_with_prompts(system_prompt, human_prompt, model="gpt-4", max_tokens=1024, temperature=0.7):
    """
    Call OpenAI API with system and human prompts
    
    Args:
        system_prompt (str): The system prompt to set assistant's behavior
        human_prompt (str): The human's message/question
        model (str): OpenAI model to use
        max_tokens (int): Maximum tokens in response
        temperature (float): Sampling temperature (0-2)
    
    Returns:
        dict: Dictionary with content, usage, model, and provider information
    """
    try:
        # Initialize the client (will use OPENAI_API_KEY from environment)
        client = openai.OpenAI()
        
        # Create the chat completion
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": human_prompt}
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        # Extract usage information
        usage = response.usage
        input_tokens = usage.prompt_tokens if usage else 0
        output_tokens = usage.completion_tokens if usage else 0
        
        return {
            "content": response.choices[0].message.content,
            "usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens
            },
            "model": model,
            "provider": "openai"
        }
        
    except Exception as e:
        return {
            "content": f"Error calling OpenAI: {str(e)}",
            "usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
            "model": model,
            "provider": "openai"
        }

def check_openai_api_key():
    """
    Check if OPENAI_API_KEY environment variable is set
    
    Returns:
        bool: True if API key is set, False otherwise
    """
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set")
        print("Set it with: export OPENAI_API_KEY='your-api-key-here'")
        return False
    return True

def get_available_openai_models():
    """
    Get list of available OpenAI models
    
    Returns:
        list: List of available model names
    """
    return [
        "gpt-4-turbo",
        "gpt-4", 
        "gpt-4-32k",
        "gpt-3.5-turbo",
        "gpt-3.5-turbo-16k",
        "gpt-3.5-turbo-instruct"
    ]
