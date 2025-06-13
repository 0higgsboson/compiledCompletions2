#!/usr/bin/env python3
"""
Claude API client for making requests to Anthropic's API
"""

import anthropic
import os

def call_claude_with_prompts(system_prompt, human_prompt, model="claude-3-5-sonnet-20241022", max_tokens=1024):
    """
    Call Claude API with system and human prompts
    
    Args:
        system_prompt (str): The system prompt to set Claude's behavior
        human_prompt (str): The human's message/question
        model (str): Claude model to use
        max_tokens (int): Maximum tokens in response
    
    Returns:
        dict: Dictionary with content, usage, model, and provider information
    """
    try:
        # Initialize the client (will use ANTHROPIC_API_KEY from environment)
        client = anthropic.Anthropic()
        
        # Create the message
        message = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system_prompt,  # System prompt goes here
            messages=[
                {"role": "user", "content": human_prompt}
            ]
        )
        
        # Extract usage information
        usage = message.usage
        input_tokens = usage.input_tokens if usage else 0
        output_tokens = usage.output_tokens if usage else 0
        
        return {
            "content": message.content[0].text,
            "usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens
            },
            "model": model,
            "provider": "claude"
        }
        
    except Exception as e:
        return {
            "content": f"Error calling Claude: {str(e)}",
            "usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
            "model": model,
            "provider": "claude"
        }

def check_api_key():
    """
    Check if ANTHROPIC_API_KEY environment variable is set
    
    Returns:
        bool: True if API key is set, False otherwise
    """
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        print("Set it with: export ANTHROPIC_API_KEY='your-api-key-here'")
        return False
    return True

def get_available_models():
    """
    Get list of available Claude models
    
    Returns:
        list: List of available model names
    """
    return [
        "claude-3-5-sonnet-20241022",
        "claude-3-5-haiku-20241022", 
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307"
    ]
