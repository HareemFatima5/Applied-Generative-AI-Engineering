# Few-Shot Prompting

## What is it?
Few-shot prompting means giving the AI a few examples first and then asking 
it to do the same thing with new input. The AI learns the pattern from our examples and follows it.


## When to Use it
- When we want the AI to follow a specific pattern
- When the task needs a specific format
- When zero-shot gives wrong or inconsistent results

## Examples I tried

### Example 1 
**Prompt:**
"""Here are some examples of sentiment classification:

Review: "The food was delicious and the staff was so friendly!" = Positive
Review: "Waited 2 hours and the food was cold. Never again." = Negative
Review: "It was fine, nothing too special about it." = Neutral

Now classify this:
Review: "Honestly the best coffee I have ever had in my life!" ="""

**Output I got:**
Positive

### Example 2 
**Prompt:**
"""Look at these emails and their categories:

Email: "URGENT: Server is down, please fix immediately!" = Urgent
Email: "Hey, are we still on for lunch tomorrow?" = Normal
Email: "Congratulations! You won a free iPhone. Click here." = Spam

Now classify this:
Email: "Please review and approve the report before 5pm today." ="""

**Output I got:**
Urgent


### Example 3 
**Prompt:**
"""Here are some job titles and their departments:

Job Title: "Surgeon" = Department: Healthcare
Job Title: "Software Engineer" = Department: Technology
Job Title: "Chartered Accountant" = Department: Finance

Now classify this:
Job Title: "Data Scientist" ="""

**Output I got:**
Department: Technology

## References
- https://www.promptingguide.ai/techniques/fewshot
- https://learnprompting.org/docs/basics/few_shot
- https://ai.google.dev/gemini-api/docs/prompting-strategies