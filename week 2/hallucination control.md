# Hallucination Control

## What is it?
Hallucination is when an AI makes up information that sounds confident but is completely wrong or not in the text. Hallucination control means writing prompts 
in a way that stops the AI from doing this.

## How it Works
We add strict rules in our prompt like:
- Only use the text I give you
- Do not use outside knowledge
- If you do not know, say so

## When to Use it
- When accuracy really matters like in medical, legal or factual tasks
- When we only want answers based on a specific document
- When we want the AI to admit it does not know something

## Examples I Tried

### Example 1
**Prompt:**
Answer the question below using ONLY the text provided.
If the answer is not in the text, say I don't have enough information.
Do NOT use outside knowledge.

Text: The Eiffel Tower is located in Paris, France. It was built in 1889 
and stands 330 meters tall. It was designed by Gustave Eiffel.

Question: When was the Eiffel Tower built and who designed it?

**Output I got:**
The Eiffel Tower was built in 1889 and was designed by Gustave Eiffel.

### Example 2 (Testing if AI Admits it Does Not Know)
**Prompt:**
Answer the question below using ONLY the text provided.
If the answer is not in the text, say I don't have enough information.
Do NOT guess or add anything extra.

Text: Hareem Fatima is a data scientist at TechSoft Solutions. She has 
3 years of experience working with Python and machine learning models.

Question: What university did Hareem Fatima attend?

**Output I got:**
I don't have enough information.

### Example 3 
**Prompt:**
Answer the question below using ONLY the text provided.
After your answer, write Confidence: High, Medium or Low depending on how sure you are.
If the answer is not in the text, say I don't have enough information.

Text: The 2024 Paris Olympics opened on July 26th. Over 10,000 athletes 
from 206 countries participated. The opening ceremony was held along the Seine River.

Question: How many countries participated in the 2024 Paris Olympics?

**Output I got:**
206 countries participated.

Confidence: High

## References
- https://www.parasoft.com/blog/controlling-llm-hallucinations-application-level-best-practices/
- https://aws.amazon.com/blogs/machine-learning/reducing-hallucinations-in-large-language-models-with-custom-intervention-using-amazon-bedrock-agents/
- https://www.getzep.com/ai-agents/reducing-llm-hallucinations/