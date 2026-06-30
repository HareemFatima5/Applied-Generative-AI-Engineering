# Extraction Prompts

## What is it?
Extraction prompting means asking the AI to pull out specific pieces of information from a block of text, like names, dates, emails, or keywords, 
instead of summarizing or classifying the whole thing.

## When to Use it
- When we need to pull contact details from messages
- When we want to identify key entities like people, companies, or dates
- When we need the main keywords or topics from a paragraph

## Examples I Tried

### Example 1
**Prompt:**
Extract the following from the text below:
- Person Names
- Company Names
- Locations
- Dates

Present each as a separate bullet list.

Text: Elon Musk announced on Monday that Tesla will open a new factory in 
Berlin by March 2026.

**Output I got:**
Person Names
- Elon Musk

Company Names
- Tesla

Locations
- Berlin

Dates
- Monday
- March 2026

### Example 2
**Prompt:**
Extract the following from the text below:
- Name
- Email
- Phone Number
- Company Name

Present each as a separate line.

Text: My name is Sara Ahmed. You can reach me at sara.ahmed@email.com or 
call me at 0300-1234567. I work at TechSoft Solutions.

**Output I got:**
Name: Sara Ahmed
Email: sara.ahmed@email.com
Phone Number: 0300-1234567
Company Name: TechSoft Solutions

### Example 3 
**Prompt:**
Extract exactly 5 keywords from the text below. These should represent 
the main topics. Return them as a numbered list, most important first.

Text: Machine learning is a subset of artificial intelligence that enables 
systems to learn from data and improve their performance without being 
explicitly programmed. It is widely used in image recognition, natural 
language processing, and recommendation systems.

**Output I got:**
1. Machine learning
2. Artificial intelligence
3. Data
4. Image recognition
5. Natural language processing

## References
- https://www.promptingguide.ai/prompts/information-extraction
- https://www.promptingguide.ai/introduction/basics
- https://learnprompting.org/docs/basics/instructions
- https://ai.google.dev/gemini-api/docs/prompting-strategies