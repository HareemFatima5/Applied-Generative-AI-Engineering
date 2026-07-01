# Prompt Versioning

## What is it?
Prompt versioning means saving and comparing different versions of the same prompt to see which one gives the best output. Just like editing a 
draft, we improve the prompt step by step and track what changed.

## How it Works
We start with a basic prompt, run it, see the output, then improve it by adding more details like audience, format, or role. We compare all versions to find the best one.

## When to Use it
- When we are not happy with the AI output and want to improve it
- When we want to find the most effective way to ask something
- When we are building something serious and need consistent results

## Examples I Tried

### Version 1 — Basic Prompt (Too Vague)
**Prompt:**
Summarize this text.

Text: Climate change is one of the biggest challenges of our time. Rising 
temperatures are causing glaciers to melt, sea levels to rise and extreme 
weather events to become more frequent. Scientists warn that urgent action 
is needed to reduce carbon emissions.

**Output I got:**
Urgent action is required to reduce carbon emissions and combat climate 
change, which is causing rising temperatures, melting glaciers, and more 
frequent extreme weather.

### Version 2 — Added Length and Audience
**Prompt:**
Summarize the text below in exactly 2 sentences for a general audience.

Text: Climate change is one of the biggest challenges of our time. Rising 
temperatures are causing glaciers to melt, sea levels to rise and extreme 
weather events to become more frequent. Scientists warn that urgent action 
is needed to reduce carbon emissions.

**Output I got:**
Climate change is a critical global challenge characterized by rising 
temperatures, melting glaciers, and more frequent extreme weather. Scientists 
emphasize that immediate efforts to reduce carbon emissions are essential 
to addressing this growing crisis.

### Version 3 — Added Role and Simpler Language 
**Prompt:**
You are a science communicator who explains things simply.
Summarize the text below in exactly 2 sentences for a 15 year old student.
Avoid technical words.

Text: Climate change is one of the biggest challenges of our time. Rising 
temperatures are causing glaciers to melt, sea levels to rise and extreme 
weather events to become more frequent. Scientists warn that urgent action 
is needed to reduce carbon emissions.

**Output I got:**
Our planet is heating up, which is causing dangerous weather patterns and 
melting ice around the world. Experts say we must act quickly to stop 
polluting the air if we want to protect our future.

## References
- https://www.promptingguide.ai/introduction/basics
- https://dev.to/kuldeep_paul/mastering-prompt-versioning-best-practices-for-scalable-llm-development-2mgm
- https://launchdarkly.com/blog/prompt-versioning-and-management/