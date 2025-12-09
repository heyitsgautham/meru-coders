# Google Gemini 2.5 Pro and Flash Python SDK Documentation

This document provides a comprehensive guide and code snippets for using the Google Gemini 2.5 Pro and Gemini 2.5 Flash models with the official Python SDK (`google-genai`). This documentation is structured to be easily digestible and useful for integration with tools like GitHub Copilot.

## 1. Setup and Authentication

### 1.1 Installation

The official library for interacting with the Gemini API is the `google-genai` SDK.

```bash
pip install -q -U google-genai
```

### 1.2 Authentication

The recommended way to authenticate is by setting your API key as an environment variable. The client will automatically pick it up.

**Environment Variable:** `GEMINI_API_KEY`

```python
import os
from google import genai

# Set the environment variable before running your script:
# export GEMINI_API_KEY="YOUR_API_KEY"

# The client will automatically use the GEMINI_API_KEY environment variable.
client = genai.Client()
```

## 2. Model Selection

The Gemini 2.5 family offers two primary models for general use:

| Model Name | Description | Use Case |
| :--- | :--- | :--- |
| `gemini-2.5-flash` | **Fastest and most cost-effective.** Excellent for high-volume, low-latency tasks like chat, summarization, and quick content generation. | Default choice for most tasks. |
| `gemini-2.5-pro` | **Most capable model.** Best for complex reasoning, coding, and tasks requiring deep understanding and high-quality output. | Advanced reasoning, complex problem-solving. |

## 3. Content Generation (Basic)

The core method for generating content is `client.models.generate_content()`.

### 3.1 Simple Text Generation

This is the standard way to ask a question or generate a piece of content.

```python
from google import genai

client = genai.Client()

# Use Gemini 2.5 Flash for a quick response
response_flash = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Explain the concept of quantum entanglement in simple terms."
)
print("--- Gemini 2.5 Flash Response ---")
print(response_flash.text)

# Use Gemini 2.5 Pro for more detailed, high-quality content
response_pro = client.models.generate_content(
    model="gemini-2.5-pro",
    contents="Write a 5-paragraph short story about a detective who can read minds."
)
print("\n--- Gemini 2.5 Pro Response ---")
print(response_pro.text)
```

### 3.2 Streaming Responses

For a better user experience in interactive applications, use `client.models.generate_content_stream()` to receive the response piece-by-piece.

```python
from google import genai

client = genai.Client()

print("--- Streaming Response from Gemini 2.5 Flash ---")
response_stream = client.models.generate_content_stream(
    model="gemini-2.5-flash",
    contents="Write a short, dramatic monologue about a forgotten hero."
)

for chunk in response_stream:
    # Print each chunk as it arrives
    print(chunk.text, end="", flush=True)

print("\n--- End of Stream ---")
```

## 4. Advanced Configuration

You can control the model's behavior using the `config` parameter with a `types.GenerateContentConfig` object.

### 4.1 System Instructions and Temperature

System instructions guide the model's persona and behavior. Temperature controls the randomness of the output (lower is more deterministic, higher is more creative).

```python
from google import genai
from google.genai import types

client = genai.Client()

config = types.GenerateContentConfig(
    # Set a system instruction to define the model's role
    system_instruction="You are a helpful, enthusiastic, and friendly coding assistant.",
    # Set a low temperature for more predictable, factual output
    temperature=0.2,
    # Set max output tokens to limit response length
    max_output_tokens=500
)

response = client.models.generate_content(
    model="gemini-2.5-pro",
    contents="How do I write a Python function to calculate the factorial of a number?",
    config=config
)

print(response.text)
```

### 4.2 Disabling "Thinking" (Gemini 2.5 Flash)

Gemini 2.5 Flash and Pro use an internal "thinking" process by default to improve quality. For the Flash model, you can disable this for maximum speed and lower token usage by setting the `thinking_budget` to 0.

```python
from google import genai
from google.genai import types

client = genai.Client()

config_no_thinking = types.GenerateContentConfig(
    thinking_config=types.ThinkingConfig(thinking_budget=0) # Disables thinking
)

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="What is the capital of France?",
    config=config_no_thinking
)

print(response.text)
```

## 5. Multi-turn Conversations (Chat)

For back-and-forth interactions, use the `client.chats.create()` method to maintain conversation history.

### 5.1 Basic Chat

```python
from google import genai

client = genai.Client()

# Create a chat session with a specific model
chat = client.chats.create(model="gemini-2.5-flash")

# First message
response1 = chat.send_message("I have three cats: one black, one white, and one orange.")
print(f"User: I have three cats: one black, one white, and one orange.")
print(f"Gemini: {response1.text}\n")

# Second message (context is maintained)
response2 = chat.send_message("What color is the least common?")
print(f"User: What color is the least common?")
print(f"Gemini: {response2.text}\n")

# View the entire conversation history
print("--- Conversation History ---")
for message in chat.get_history():
    # The history is stored as Content objects
    role = message.role
    text = message.parts[0].text
    print(f"**{role.capitalize()}**: {text}")
```

## 6. Multimodal Input (Question Answering with Images)

Gemini 2.5 models are inherently multimodal, allowing you to pass images, audio, and other files along with text prompts.

### 6.1 Image and Text Prompt

This requires the `Pillow` library (`pip install Pillow`).

```python
from google import genai
from PIL import Image
import io

client = genai.Client()

# --- Placeholder for loading an image ---
# In a real application, you would load an image from a file path.
# For this example, we'll create a dummy image in memory.
try:
    # Replace this with your actual image loading:
    # image = Image.open("/path/to/your/image.jpg")
    
    # Dummy image creation for demonstration purposes
    dummy_image = Image.new('RGB', (100, 100), color = 'red')
    img_byte_arr = io.BytesIO()
    dummy_image.save(img_byte_arr, format='PNG')
    image = Image.open(io.BytesIO(img_byte_arr.getvalue()))
    
    prompt = "Describe this image in a single, creative sentence."
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        # Pass the image object and the text prompt in a list
        contents=[image, prompt]
    )
    
    print(f"Prompt: {prompt}")
    print(f"Gemini Response: {response.text}")

except ImportError:
    print("Pillow (PIL) is not installed. Please run 'pip install Pillow' to use multimodal examples.")
except Exception as e:
    print(f"An error occurred: {e}")
```

## 7. Function Calling (Tool Use)

Function calling allows the model to decide when to call a function you define, and with what arguments. This is crucial for connecting the model to external systems or data.

### 7.1 Example: Weather Tool

```python
from google import genai
from google.genai import types
import json

client = genai.Client()

# 1. Define the function the model can call
def get_current_weather(city: str) -> str:
    """
    Returns the current weather in a given city.
    In a real application, this would call a weather API.
    """
    if "boston" in city.lower():
        return json.dumps({"city": "Boston", "temperature": "15°C", "condition": "Cloudy"})
    elif "tokyo" in city.lower():
        return json.dumps({"city": "Tokyo", "temperature": "22°C", "condition": "Sunny"})
    else:
        return json.dumps({"city": city, "temperature": "N/A", "condition": "Unknown"})

# 2. Define the tool configuration
tool_config = types.GenerateContentConfig(
    tools=[get_current_weather]
)

# 3. Send the prompt to the model
prompt = "What is the weather like in Boston and Tokyo?"
response = client.models.generate_content(
    model="gemini-2.5-pro", # Pro is generally better for function calling
    contents=prompt,
    config=tool_config
)

# 4. Check if the model requested a function call
if response.function_calls:
    print("--- Model requested function calls ---")
    
    # Prepare the list of function responses
    function_responses = []
    
    for call in response.function_calls:
        # Execute the function with the arguments provided by the model
        function_name = call.name
        function_args = dict(call.args)
        
        print(f"Calling function: {function_name} with args: {function_args}")
        
        # Execute the actual Python function
        result = get_current_weather(**function_args)
        
        # Add the result to the list of function responses
        function_responses.append(
            types.Part.from_function_response(
                name=function_name,
                response={"content": result}
            )
        )
    
    # 5. Send the function results back to the model
    print("\n--- Sending function results back to model ---")
    final_response = client.models.generate_content(
        model="gemini-2.5-pro",
        contents=[prompt] + function_responses, # Include original prompt and function results
        config=tool_config
    )
    
    print("\n--- Final Gemini Response ---")
    print(final_response.text)

else:
    print("--- No function call requested ---")
    print(response.text)
```
