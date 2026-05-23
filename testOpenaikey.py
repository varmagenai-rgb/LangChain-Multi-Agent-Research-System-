from openai import OpenAI
import os

# Option 1: Key from environment variable
#client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Option 2: Hardcoded (quick test only, not for production)
client = OpenAI(
    api_key="",
    base_url="https://openrouter.ai/api/v1",
)

try:
    response = client.chat.completions.create(
        model="openai/gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Say 'Hello, API is working!'"}],
        max_tokens=20
    )
    print("✅ API Key is working!")
    print("Response:", response.choices[0].message.content)
    print("Model used:", response.model)

except Exception as e:
    print("❌ Error:", e)