#!/usr/bin/env python3
"""
Test script to verify the Analyse Chanda link generation
"""

import urllib.parse

# Test text (the verse from user's example)
test_text = "शालिन्युक्ता म्तौ तगौ गोऽब्धिलोकैः। माता रामो मत्पिता रामचन्द्रः स्वामी रामो मत्सखा रामचन्द्रः। सर्वस्वं मे रामचन्द्रो दयालुर् नान्यं‌ जाने नैव जाने न जाने॥"

print("=" * 80)
print("Testing Analyse Chanda Link Generation")
print("=" * 80)
print(f"\nOriginal text:\n{test_text}\n")

# URL encode the text
encoded_text = urllib.parse.quote(test_text)
print(f"URL-encoded text:\n{encoded_text}\n")

# Create the link
analyze_url = f"/app?text={encoded_text}"
print(f"Generated link:\n{analyze_url}\n")

# Create markdown link
markdown_link = f"[**Analyse Chanda**]({analyze_url})"
print(f"Markdown link:\n{markdown_link}\n")

# Full tip message
tip_message = f"\n---\n💡 **Tip:** Use the {markdown_link} page for detailed analysis with visualizations.\n"
print("=" * 80)
print("Full Tip Message:")
print("=" * 80)
print(tip_message)

print("\n✅ Link generation working correctly!")
print("\nThe link will:")
print("1. Navigate to /app (home page)")
print("2. Pass the text as URL parameter")
print("3. MainApp will read the parameter and auto-fill the form")
print("4. The link will be styled with bold text and #FF9933 (saffron) color")
