# Multi-AI Prompt Comparison Tool

A simple command-line tool for comparing AI responses across Claude, OpenAI, and Gemini with tier-based model selection and cost tracking.

## Features

- **Multi-provider comparison**: Get responses from Claude, OpenAI, and Gemini simultaneously
- **Tier-based pricing**: Choose between Economy, Mid, and Luxury tiers for cost vs quality
- **Response synthesis**: Combine insights from all providers into one comprehensive answer
- **Cost tracking**: Detailed breakdown of usage and costs across providers
- **Single provider mode**: Use just one AI provider if preferred

## Installation

1. **Clone and setup:**
```bash
git clone <repository-url>
cd simplePrompt3Engines
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Set API keys:**
```bash
export ANTHROPIC_API_KEY="your-anthropic-key-here"
export OPENAI_API_KEY="your-openai-key-here"  
export GEMINI_API_KEY="your-gemini-key-here"
```

Get API keys from:
- Claude: [console.anthropic.com](https://console.anthropic.com)
- OpenAI: [platform.openai.com](https://platform.openai.com)
- Gemini: [makersuite.google.com](https://makersuite.google.com/app/apikey)

## Usage

### Basic Comparison (Default)
```bash
# Low-cost test question
python3 main.py "You are a helpful assistant" "What is 1+1?"

# More complex example
python3 main.py "You are a helpful assistant" "Explain quantum computing in simple terms"
```

### With Response Synthesis
```bash
# Low-cost test with synthesis
python3 main.py "You are a helpful assistant" "What is 1+1?" --synthesize

# More complex example with synthesis
python3 main.py "You are a helpful assistant" "Explain quantum computing" --synthesize
```

### Single Provider
```bash
python3 main.py "You are a helpful assistant" "Explain quantum computing" --provider claude
python3 main.py "You are a helpful assistant" "Explain quantum computing" --provider openai
python3 main.py "You are a helpful assistant" "Explain quantum computing" --provider gemini
```

### Different Quality Tiers
```bash
# Economy tier (default) - cheapest models
python3 main.py "You are a helpful assistant" "Explain quantum computing" --tier economy

# Mid tier - balanced cost/quality  
python3 main.py "You are a helpful assistant" "Explain quantum computing" --tier mid

# Luxury tier - premium models
python3 main.py "You are a helpful assistant" "Explain quantum computing" --tier luxury
```

### Multiple Calls for Consistency Testing
```bash
# Make 5 calls to OpenAI to test response consistency
python3 main.py "You are a helpful assistant" "Explain quantum computing" --provider openai --num-calls 5

# Compare all providers with 3 calls each
python3 main.py "You are a helpful assistant" "Explain quantum computing" --num-calls 3

# Luxury tier with multiple calls for high-quality analysis
python3 main.py "You are a helpful assistant" "Explain quantum computing" --tier luxury --num-calls 10
```

### Save Results
```bash
python3 main.py "You are a helpful assistant" "Explain quantum computing" --output results.json
```

## Quality/Cost Tiers

### 🟢 Economy (Default)
**Maximum cost savings** - Uses cheapest models
- Claude: Haiku ($0.25/$1.25 per 1M tokens)
- OpenAI: GPT-4o-mini ($0.15/$0.60 per 1M tokens)
- Gemini: Flash ($0.075/$0.30 per 1M tokens)
- **Est. cost per comparison: ~$0.0001-0.001**

### 🟡 Mid Tier  
**Balanced approach** - Cheap individual responses, premium synthesis
- Individual responses: Same as Economy
- Synthesis: Claude Sonnet (premium)
- **Est. cost per comparison: ~$0.001-0.005**

### 🟣 Luxury Tier
**Maximum quality** - Premium models everywhere
- Claude: Sonnet ($3.00/$15.00 per 1M tokens)
- OpenAI: GPT-4 ($30.00/$60.00 per 1M tokens)  
- Gemini: Pro ($1.25/$5.00 per 1M tokens)
- **Est. cost per comparison: ~$0.01-0.05**

## Command Line Options

### Basic Options
- `system_prompt`: System prompt to set AI behavior (required)
- `human_prompt`: Your question or prompt (required)

### Provider Selection
- `--provider claude|openai|gemini`: Use single provider
- `--compare`: Compare all providers (default behavior)
- `--synthesize`: Generate combined response from all providers

### Quality/Cost Control
- `--tier economy|mid|luxury`: Select quality tier (default: economy)
- `--list-tiers`: Show available tiers and pricing

### Generation Parameters
- `--max-tokens INT`: Maximum tokens per response (default: 1024)
- `--temperature FLOAT`: Sampling temperature for OpenAI/Gemini (default: 0.7)
- `--num-calls INT`: Number of calls to make to each model with the same prompt (default: 1)

### Output Options
- `--output FILE`: Save results to JSON file
- `--json`: Output raw JSON response data

## Example Output

```
🎯 PROMPT COMPARISON
================================================================================

❓ SYSTEM PROMPT:
You are a helpful assistant

❓ HUMAN PROMPT:
Explain quantum computing in simple terms

🏷️ TIER: ECONOMY - Economy tier - cheapest models for cost-effective processing

--------------------------------------------------------------------------------
🤖 CLAUDE RESPONSE:
Quantum computing is like having a super-powered calculator that works completely differently from regular computers...
📊 Response Length: 247 words
💰 Cost: $0.000856 (1,234 tokens)

--------------------------------------------------------------------------------
🧠 OPENAI RESPONSE:
Think of quantum computing as a fundamentally different way of processing information...
📊 Response Length: 312 words  
💰 Cost: $0.000234 (1,567 tokens)

--------------------------------------------------------------------------------
💎 GEMINI RESPONSE:
Quantum computers represent a revolutionary approach to computation...
📊 Response Length: 289 words
💰 Cost: $0.000167 (890 tokens)

********************************************************************************
📊 COST BREAKDOWN
================================================================================
🤖 CLAUDE     1,234 tokens    $0.000856    $0.6938/1K
🧠 OPENAI     1,567 tokens    $0.000234    $0.1494/1K  
💎 GEMINI       890 tokens    $0.000167    $0.1876/1K
--------------------------------------------------------------------------------
💰 TOTAL COST: $0.001257

💡 EFFICIENCY INSIGHTS:
🏅 Most Efficient: 🧠 OPENAI ($0.1494/1K tokens)
💸 Least Efficient: 🤖 CLAUDE ($0.6938/1K tokens)
📈 Efficiency Difference: 364.4% more expensive
```

## File Structure

```
├── main.py                    # Main CLI script
├── src/
│   ├── ai_clients/           # AI API integrations
│   │   ├── claude_client.py  # Claude API client
│   │   ├── openai_client.py  # OpenAI API client
│   │   └── gemini_client.py  # Gemini API client
│   └── config/
│       └── config.json       # Configuration and system prompts
├── requirements.txt          # Python dependencies
└── README.md                # This file
```

## Requirements

See `requirements.txt` for full dependencies. Main requirements:
- `anthropic` - Claude API client
- `openai` - OpenAI API client  
- `google-generativeai` - Gemini API client

## Error Handling

The tool includes comprehensive error handling for:
- Missing API keys with helpful setup instructions
- API authentication issues
- Network errors and timeouts
- Rate limiting and server overload (with automatic retry)
- Invalid parameters
- Provider-specific errors

### Automatic Retry Logic
All providers now include intelligent retry logic for temporary failures:
- **Exponential backoff**: 1s → 2s → 4s wait times
- **Smart error detection**: Only retries on temporary errors (rate limits, server overload)
- **User feedback**: Shows retry attempts in real-time
- **Graceful fallback**: Returns error message if all retries fail

## Cost Tracking

The tool provides detailed cost analysis:
- Per-provider token usage and costs
- Cost per 1K tokens comparison
- Efficiency rankings
- Total cost breakdown
- Real-time cost estimation

Perfect for budget-conscious AI experimentation and finding the most cost-effective provider for your use case.