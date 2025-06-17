#!/usr/bin/env python3
"""
@author Sid Shaik (@0higgsboson)
Licensed under Apache 2.0

Simple AI prompt comparison tool
Compares responses across Claude, OpenAI, and Gemini with tier-based model selection
"""

import argparse
import sys
import os
import json
import warnings
from datetime import datetime

# Suppress urllib3 OpenSSL warning on macOS
warnings.filterwarnings("ignore", message="urllib3 v2 only supports OpenSSL 1.1.1+.*")

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.ai_clients.claude_client import call_claude_with_prompts, check_api_key
from src.ai_clients.openai_client import call_openai_with_prompts, check_openai_api_key
from src.ai_clients.gemini_client import call_gemini_with_prompts, check_gemini_api_key

# Tier configuration
TIERS = {
    "economy": {
        "description": "Economy tier - cheapest models for cost-effective processing",
        "claude": "claude-3-5-haiku-20241022",
        "openai": "gpt-4o-mini", 
        "gemini": "gemini-1.5-flash",
        "synthesis": "claude-3-5-haiku-20241022"
    },
    "mid": {
        "description": "Mid tier - balanced cost and quality with premium synthesis",
        "claude": "claude-3-5-haiku-20241022",
        "openai": "gpt-4o-mini",
        "gemini": "gemini-1.5-flash", 
        "synthesis": "claude-3-5-sonnet-20241022"
    },
    "luxury": {
        "description": "Luxury tier - premium models for maximum quality",
        "claude": "claude-3-5-sonnet-20241022",
        "openai": "gpt-4",
        "gemini": "gemini-1.5-pro",
        "synthesis": "claude-3-5-sonnet-20241022"
    }
}

# Pricing per 1K tokens (input/output)
PRICING = {
    "claude-3-5-haiku-20241022": (0.25, 1.25),
    "claude-3-5-sonnet-20241022": (3.00, 15.00),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4": (30.00, 60.00),
    "gemini-1.5-flash": (0.075, 0.30),
    "gemini-1.5-pro": (1.25, 5.00)
}

def calculate_cost(usage, model):
    """Calculate cost based on usage and model pricing"""
    if model not in PRICING:
        return 0
    
    input_price, output_price = PRICING[model]
    input_tokens = usage.get("input_tokens", 0)
    output_tokens = usage.get("output_tokens", 0)
    
    cost = (input_tokens * input_price / 1000) + (output_tokens * output_price / 1000)
    return cost

def format_response(response, provider_name, emoji):
    """Format individual provider response"""
    content = response.get("content", "No response")
    usage = response.get("usage", {})
    model = response.get("model", "unknown")
    word_count = len(content.split())
    
    cost = calculate_cost(usage, model)
    
    output = f"\n{'-'*80}\n"
    output += f"{emoji} {provider_name.upper()} RESPONSE:\n"
    output += f"{content}\n"
    output += f"📊 Response Length: {word_count} words\n"
    output += f"💰 Cost: ${cost:.6f} ({usage.get('total_tokens', 0)} tokens)\n"
    
    return output

def synthesize_responses(responses, system_prompt, human_prompt, tier):
    """Create a synthesized response using all provider responses"""
    synthesis_prompt = f"""Based on the following three AI responses to the same question, create a synthesized answer that combines the best insights from all three responses.

Original Question: {human_prompt}

Claude Response: {responses['claude']['content']}

OpenAI Response: {responses['openai']['content']}

Gemini Response: {responses['gemini']['content']}

Synthesize these into one comprehensive response that captures the best elements from all three while maintaining coherence and eliminating redundancy."""

    model = TIERS[tier]["synthesis"]
    synthesis_response = call_claude_with_prompts(
        "You are an expert synthesizer. Combine insights from multiple AI responses into one coherent, comprehensive answer.",
        synthesis_prompt,
        model=model
    )
    
    return synthesis_response

def compare_providers(system_prompt, human_prompt, tier="economy", max_tokens=1024, temperature=0.7, num_calls=1):
    """Compare responses across all three providers"""
    
    tier_config = TIERS[tier]
    responses = {}
    
    print(f"\n🎯 PROMPT COMPARISON")
    print(f"{'='*80}")
    print(f"\n❓ SYSTEM PROMPT:")
    print(f"{system_prompt}")
    print(f"\n❓ HUMAN PROMPT:")
    print(f"{human_prompt}")
    print(f"\n🏷️ TIER: {tier.upper()} - {tier_config['description']}")
    if num_calls > 1:
        print(f"🔄 CALLS PER MODEL: {num_calls}")

    # Call each provider
    providers = [
        ("claude", "🤖 CLAUDE", call_claude_with_prompts, tier_config["claude"]),
        ("openai", "🧠 OPENAI", call_openai_with_prompts, tier_config["openai"]),
        ("gemini", "💎 GEMINI", call_gemini_with_prompts, tier_config["gemini"])
    ]

    for provider_key, provider_name, call_func, model in providers:
        print(f"\nCalling {provider_name} with {model} ({num_calls} time{'s' if num_calls != 1 else ''})...")

        provider_responses = []
        total_usage = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}

        for call_num in range(num_calls):
            if num_calls > 1:
                print(f"  Call {call_num + 1}/{num_calls}...")

            if provider_key == "openai":
                response = call_func(system_prompt, human_prompt, model=model, max_tokens=max_tokens, temperature=temperature)
            elif provider_key == "gemini":
                response = call_func(system_prompt, human_prompt, model=model, max_tokens=max_tokens, temperature=temperature)
            else:  # claude
                response = call_func(system_prompt, human_prompt, model=model, max_tokens=max_tokens)

            provider_responses.append(response)

            # Accumulate usage statistics
            usage = response.get("usage", {})
            total_usage["input_tokens"] += usage.get("input_tokens", 0)
            total_usage["output_tokens"] += usage.get("output_tokens", 0)
            total_usage["total_tokens"] += usage.get("total_tokens", 0)

        # Store aggregated response data
        if num_calls == 1:
            # Single call - use the response as-is
            responses[provider_key] = provider_responses[0]
        else:
            # Multiple calls - create aggregated response
            all_contents = [resp.get("content", "") for resp in provider_responses]
            responses[provider_key] = {
                "content": f"[{num_calls} calls made]\n" + "\n\n---\n\n".join(all_contents),
                "model": model,
                "usage": total_usage,
                "individual_responses": provider_responses
            }

        print(format_response(responses[provider_key], provider_name, provider_name.split()[0]))
    
    return responses

def print_cost_summary(responses, synthesis_response=None):
    """Print detailed cost breakdown"""
    print(f"\n{'*'*80}")
    print(f"📊 COST BREAKDOWN")
    print(f"{'='*80}")
    
    total_cost = 0
    costs = []
    
    provider_emojis = {"claude": "🤖", "openai": "🧠", "gemini": "💎"}
    
    for provider, response in responses.items():
        model = response.get("model", "unknown")
        usage = response.get("usage", {})
        cost = calculate_cost(usage, model)
        total_cost += cost
        
        total_tokens = usage.get("total_tokens", 0)
        cost_per_1k = (cost / max(total_tokens, 1) * 1000) if total_tokens > 0 else 0
        costs.append((provider, cost, cost_per_1k))
        
        emoji = provider_emojis.get(provider, "🔹")
        print(f"{emoji} {provider.upper():<8} {usage.get('total_tokens', 0):>6} tokens    ${cost:>8.6f}    ${cost_per_1k:>7.4f}/1K")
    
    if synthesis_response:
        model = synthesis_response.get("model", "unknown")
        usage = synthesis_response.get("usage", {})
        cost = calculate_cost(usage, model)
        total_cost += cost
        synthesis_tokens = usage.get('total_tokens', 0)
        synthesis_cost_per_1k = (cost / max(synthesis_tokens, 1) * 1000) if synthesis_tokens > 0 else 0
        print(f"⭐ SYNTHESIS  {synthesis_tokens:>6} tokens    ${cost:>8.6f}    ${synthesis_cost_per_1k:>7.4f}/1K")
    
    print(f"{'-'*80}")
    print(f"💰 TOTAL COST: ${total_cost:.6f}")
    
    # Find most/least efficient
    if costs:
        costs.sort(key=lambda x: x[2])  # Sort by cost per 1K tokens
        most_efficient = costs[0]
        least_efficient = costs[-1]
        
        print(f"\n💡 EFFICIENCY INSIGHTS:")
        print(f"🏅 Most Efficient: {provider_emojis.get(most_efficient[0], '🔹')} {most_efficient[0].upper()} (${most_efficient[2]:.4f}/1K tokens)")
        print(f"💸 Least Efficient: {provider_emojis.get(least_efficient[0], '🔹')} {least_efficient[0].upper()} (${least_efficient[2]:.4f}/1K tokens)")
        
        if least_efficient[2] > 0 and most_efficient[2] > 0:
            efficiency_diff = ((least_efficient[2] - most_efficient[2]) / most_efficient[2]) * 100
            print(f"📈 Efficiency Difference: {efficiency_diff:.1f}% more expensive")

def main():
    parser = argparse.ArgumentParser(description="Compare AI responses across Claude, OpenAI, and Gemini")
    parser.add_argument("system_prompt", nargs='?', help="System prompt to set AI behavior")
    parser.add_argument("human_prompt", nargs='?', help="Human prompt/question")
    
    # Provider selection
    parser.add_argument("--provider", choices=["claude", "openai", "gemini"], 
                       help="Use single provider instead of comparison")
    parser.add_argument("--compare", action="store_true",
                       help="Compare all providers (default when no --provider specified)")
    parser.add_argument("--synthesize", action="store_true", 
                       help="Generate synthesized response combining all providers")
    
    # Tier selection
    parser.add_argument("--tier", choices=["economy", "mid", "luxury"], default="economy",
                       help="Quality/cost tier (default: economy)")
    parser.add_argument("--list-tiers", action="store_true", 
                       help="Show available tiers and exit")
    
    # Generation parameters
    parser.add_argument("--max-tokens", type=int, default=1024,
                       help="Maximum tokens per response (default: 1024)")
    parser.add_argument("--temperature", type=float, default=0.7,
                       help="Sampling temperature for OpenAI/Gemini (default: 0.7)")
    parser.add_argument("--num-calls", type=int, default=1,
                       help="Number of calls to make to each model with the same prompt (default: 1)")
    
    # Output options  
    parser.add_argument("--output", help="Save results to file")
    parser.add_argument("--json", action="store_true", 
                       help="Output results in JSON format")
    
    args = parser.parse_args()
    
    # Handle list tiers
    if args.list_tiers:
        print("Available Quality/Cost Tiers:")
        print("="*50)
        for tier_name, tier_config in TIERS.items():
            print(f"\n🏷️ {tier_name.upper()} TIER")
            print(f"   {tier_config['description']}")
            print(f"   Claude: {tier_config['claude']}")
            print(f"   OpenAI: {tier_config['openai']}")
            print(f"   Gemini: {tier_config['gemini']}")
            if tier_config.get('synthesis'):
                print(f"   Synthesis: {tier_config['synthesis']}")
        return

    # Check that required prompts are provided
    if not args.system_prompt or not args.human_prompt:
        parser.error("system_prompt and human_prompt are required unless using --list-tiers")

    # Determine mode: single provider if --provider is specified and --compare is not explicitly set
    use_single_provider = args.provider and not args.compare

    # Check API keys based on what we'll actually use
    if use_single_provider:
        # Single provider mode - only check the specified provider
        if args.provider == "claude":
            if not check_api_key():
                sys.exit(1)
        elif args.provider == "openai":
            if not check_openai_api_key():
                sys.exit(1)
        elif args.provider == "gemini":
            if not check_gemini_api_key():
                sys.exit(1)
    else:
        # Multi-provider mode - check all providers
        if not check_api_key():
            sys.exit(1)
        if not check_openai_api_key():
            sys.exit(1)
        if not check_gemini_api_key():
            sys.exit(1)
    
    # Single provider mode
    if use_single_provider:
        tier_config = TIERS[args.tier]
        model = tier_config[args.provider]

        print(f"\n🎯 SINGLE PROVIDER: {args.provider.upper()}")
        print(f"Model: {model}")
        print(f"Tier: {args.tier}")
        if args.num_calls > 1:
            print(f"🔄 Number of calls: {args.num_calls}")

        responses = []
        total_usage = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
        total_cost = 0

        for call_num in range(args.num_calls):
            if args.num_calls > 1:
                print(f"\nCall {call_num + 1}/{args.num_calls}...")

            if args.provider == "claude":
                response = call_claude_with_prompts(args.system_prompt, args.human_prompt,
                                                  model=model, max_tokens=args.max_tokens)
            elif args.provider == "openai":
                response = call_openai_with_prompts(args.system_prompt, args.human_prompt,
                                                  model=model, max_tokens=args.max_tokens,
                                                  temperature=args.temperature)
            elif args.provider == "gemini":
                response = call_gemini_with_prompts(args.system_prompt, args.human_prompt,
                                                  model=model, max_tokens=args.max_tokens,
                                                  temperature=args.temperature)

            responses.append(response)

            # Accumulate usage and cost
            usage = response.get("usage", {})
            total_usage["input_tokens"] += usage.get("input_tokens", 0)
            total_usage["output_tokens"] += usage.get("output_tokens", 0)
            total_usage["total_tokens"] += usage.get("total_tokens", 0)

            call_cost = calculate_cost(usage, response["model"])
            total_cost += call_cost

            if args.num_calls > 1:
                print(f"Response {call_num + 1}:")
                print(f"{response['content']}")
                print(f"Cost: ${call_cost:.6f}")
                print("-" * 40)

        if args.num_calls == 1:
            print(f"\n{responses[0]['content']}")
        else:
            print(f"\n📊 SUMMARY OF {args.num_calls} CALLS:")
            print(f"Total tokens used: {total_usage['total_tokens']}")
            print(f"Average tokens per call: {total_usage['total_tokens'] / args.num_calls:.1f}")

        print(f"\n💰 Total Cost: ${total_cost:.6f}")
        if args.num_calls > 1:
            print(f"💰 Average Cost per Call: ${total_cost / args.num_calls:.6f}")

        if args.json:
            if args.num_calls == 1:
                print(f"\n{json.dumps(responses[0], indent=2)}")
            else:
                output_data = {
                    "num_calls": args.num_calls,
                    "total_usage": total_usage,
                    "total_cost": total_cost,
                    "individual_responses": responses
                }
                print(f"\n{json.dumps(output_data, indent=2)}")

        return
    
    # Multi-provider comparison mode
    responses = compare_providers(args.system_prompt, args.human_prompt,
                                args.tier, args.max_tokens, args.temperature, args.num_calls)
    
    synthesis_response = None
    if args.synthesize:
        print(f"\n{'*'*80}")
        print("⭐ GENERATING SYNTHESIZED RESPONSE...")
        synthesis_response = synthesize_responses(responses, args.system_prompt, 
                                                args.human_prompt, args.tier)
        
        print(f"\n⭐ MIXTURE-OF-EXPERTS SYNTHESIZED ANSWER:")
        print(f"{synthesis_response['content']}")
        word_count = len(synthesis_response['content'].split())
        print(f"📊 Synthesized Response Length: {word_count} words")
        print(f"💡 This combines the best insights from all three AI providers above!")
    
    # Print cost summary
    print_cost_summary(responses, synthesis_response)
    
    # Save output if requested
    if args.output:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_data = {
            "timestamp": timestamp,
            "system_prompt": args.system_prompt,
            "human_prompt": args.human_prompt,
            "tier": args.tier,
            "num_calls": args.num_calls,
            "responses": responses
        }

        if synthesis_response:
            output_data["synthesis"] = synthesis_response

        with open(args.output, 'w') as f:
            json.dump(output_data, f, indent=2)

        print(f"\n💾 Results saved to: {args.output}")

if __name__ == "__main__":
    main()