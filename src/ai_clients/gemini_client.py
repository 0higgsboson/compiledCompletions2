#!/usr/bin/env python3
"""
@author Sid Shaik (@0higgsboson) 
Licensed under Apache 2.0

Google Gemini API client for making requests to Google's Gemini API
"""

import google.generativeai as genai
import os

def call_gemini_with_prompts(system_prompt, human_prompt, model="gemini-1.5-pro", max_tokens=1024, temperature=0.7):
    """
    Call Gemini API with system and human prompts
    
    Args:
        system_prompt (str): The system prompt to set model's behavior
        human_prompt (str): The human's message/question
        model (str): Gemini model to use
        max_tokens (int): Maximum tokens in response
        temperature (float): Sampling temperature (0-2)
    
    Returns:
        dict: Response with content and usage information
    """
    try:
        # Configure the API key
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        
        # Initialize the model
        model_instance = genai.GenerativeModel(
            model_name=model,
            system_instruction=system_prompt
        )
        
        # Configure generation parameters
        generation_config = genai.types.GenerationConfig(
            max_output_tokens=max_tokens,
            temperature=temperature
        )
        
        # Generate response
        response = model_instance.generate_content(
            human_prompt,
            generation_config=generation_config
        )
        
        # Extract usage information (Gemini API may not always provide detailed usage)
        usage_metadata = response.usage_metadata if hasattr(response, 'usage_metadata') else None
        
        if usage_metadata:
            input_tokens = usage_metadata.prompt_token_count
            output_tokens = usage_metadata.candidates_token_count
        else:
            # Estimate tokens if not provided (rough approximation: 1 token ≈ 4 characters)
            input_tokens = len(system_prompt + human_prompt) // 4
            output_tokens = len(response.text) // 4
        
        return {
            "content": response.text,
            "usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens
            },
            "model": model,
            "provider": "gemini"
        }
        
    except Exception as e:
        return {
            "content": f"Error calling Gemini: {str(e)}",
            "usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
            "model": model,
            "provider": "gemini"
        }

def check_gemini_api_key():
    """
    Check if GEMINI_API_KEY environment variable is set
    
    Returns:
        bool: True if API key is set, False otherwise
    """
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set")
        print("Set it with: export GEMINI_API_KEY='your-api-key-here'")
        print("Get your key from: https://makersuite.google.com/app/apikey")
        return False
    return True

def get_available_gemini_models():
    """
    Get list of available Gemini models
    
    Returns:
        list: List of available model names
    """
    return [
        "gemini-1.5-pro",
        "gemini-1.5-flash",
        "gemini-1.0-pro",
        "gemini-1.0-pro-vision"
    ]

def list_gemini_models_from_api():
    """
    Get available models directly from Gemini API
    
    Returns:
        list: List of model names from API
    """
    try:
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        models = genai.list_models()
        
        # Filter for generative models that support generateContent
        generative_models = []
        for model in models:
            if 'generateContent' in model.supported_generation_methods:
                generative_models.append(model.name.replace('models/', ''))
        
        return sorted(generative_models)
    except Exception as e:
        print(f"Error fetching models from API: {e}")
        return get_available_gemini_models()

def call_gemini_with_safety_settings(system_prompt, human_prompt, model="gemini-1.5-pro", max_tokens=1024, temperature=0.7):
    """
    Call Gemini API with custom safety settings
    
    Args:
        system_prompt (str): The system prompt to set model's behavior
        human_prompt (str): The human's message/question
        model (str): Gemini model to use
        max_tokens (int): Maximum tokens in response
        temperature (float): Sampling temperature (0-2)
    
    Returns:
        str: Gemini's response or error message
    """
    try:
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        
        # Configure safety settings (more permissive)
        safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            }
        ]
        
        model_instance = genai.GenerativeModel(
            model_name=model,
            system_instruction=system_prompt,
            safety_settings=safety_settings
        )
        
        generation_config = genai.types.GenerationConfig(
            max_output_tokens=max_tokens,
            temperature=temperature
        )
        
        response = model_instance.generate_content(
            human_prompt,
            generation_config=generation_config
        )
        
        return response.text
        
    except Exception as e:
        return f"Error calling Gemini with safety settings: {str(e)}"
