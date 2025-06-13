# Create virtual environment
python3 -m venv ai-env

# Activate it
source ai-env/bin/activate

# Install packages
pip install openai anthropic google-generativeai

# Now run your script
python main.py
