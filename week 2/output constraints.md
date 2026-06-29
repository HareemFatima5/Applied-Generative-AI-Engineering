# Output Constraints

## What is it?
Output constraints mean giving the AI strict rules about how to format or structure its answer. Instead of letting the AI answer however it wants, 
we tell it exactly what to do.

## How it Works
We add rules at the end or beginning of your prompt like:
- Use bullet points only
- Answer in exactly 50 words
- Do not write any introduction
- Follow this exact format

## When to Use it
- When we need answers in a specific format
- When we want short and to the point answers
- When we are going to use the output somewhere specific like a report or table

## Examples 

### Example 1 
**Prompt:**
"""List 5 benefits of drinking water daily.
Rules you must follow:
1) Use bullet points only
2) Each point must be under 10 words
3) Do not number the points"""

**Output I got:**
* Improves physical performance
* Boosts brain function and focus
* Aids in healthy digestion
* Helps maintain skin health
* Regulates body temperature effectively

### Example 2 
**Prompt:**
"""Explain artificial intelligence in exactly 50 words not more, not less.
Use simple language that a 10 year old can understand.Do not use any technical terms."""

**Output I got:**
Output: Artificial intelligence is when computers learn to think and act like people. By looking at lots of information, they figure out how to solve problems, recognize pictures, or answer your questions. It is like teaching a machine to use its brain to help you do things faster and much better.

### Example 3 
**Prompt:**
"""Give me information about Python programming language.
You must follow this exact format and no other:
Name:
Created In:
Created By:
Main Use:
Do not add anything outside this format."""

**Output I got:**
Output: Name: Python
Created In: 1991
Created By: Guido van Rossum
Main Use: Data science, web development, and automation

## References
- https://www.promptingguide.ai/introduction/basics
- https://learnprompting.org/docs/basics/instructions
- https://docs.helicone.ai/guides/prompt-engineering/use-constrained-outputs