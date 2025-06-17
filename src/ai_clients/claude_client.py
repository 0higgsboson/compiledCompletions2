#!/usr/bin/env python3
"""
@author Sid Shaik (@0higgsboson) 
Licensed under Apache 2.0

Claude API client for making requests to Anthropic's API
"""

import anthropic
import os
import time
import random

def call_claude_with_prompts(system_prompt, human_prompt, model="claude-3-5-sonnet-20241022", max_tokens=1024, max_retries=3):
    """
    Call Claude API with system and human prompts, with retry logic for overload errors

    Args:
        system_prompt (str): The system prompt to set Claude's behavior
        human_prompt (str): The human's message/question
        model (str): Claude model to use
        max_tokens (int): Maximum tokens in response
        max_retries (int): Maximum number of retries for overload errors

    Returns:
        dict: Dictionary with content, usage, model, and provider information
    """

    for attempt in range(max_retries + 1):
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
            error_str = str(e)

            # Check if this is an overload error (529) and we have retries left
            if "529" in error_str or "overloaded" in error_str.lower():
                if attempt < max_retries:
                    # Exponential backoff with jitter: 2^attempt + random(0-1) seconds
                    wait_time = (2 ** attempt) + random.random()
                    print(f"  Claude overloaded (attempt {attempt + 1}/{max_retries + 1}), retrying in {wait_time:.1f}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    error_str = f"Claude overloaded after {max_retries + 1} attempts: {error_str}"

            # For non-overload errors or exhausted retries, return error
            return {
                "content": f"Error calling Claude: {error_str}",
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
