# Classification Prompts

## What is it?
Classification prompting means asking the AI to sort or label pieces of text into categories that we define. We tell the AI what categories exist 
and ask it to assign the correct one to each item.

## When to Use it
- When we need to sort customer feedback, emails or complaints
- When we want consistent labeling across many items
- When building something like a support ticket system or content filter

## Examples I Tried

### Example 1 
**Prompt:**
Classify each customer complaint into one of these categories:
Delivery, Customer Service, Billing

Complaints:
1. "My order arrived 2 weeks late."
2. "I was charged twice for one order."
3. "The support agent was very rude."

Format:
Complaint 1: [Category]
Complaint 2: [Category]
Complaint 3: [Category]

**Output I got:**
Complaint 1: Delivery
Complaint 2: Billing
Complaint 3: Customer Service

### Example 2 
**Prompt:**
Classify each movie description into one genre:
Action, Comedy, Horror, Romance

Descriptions:
1. "A group of friends fight off zombies in an abandoned mall."
2. "A clumsy office worker keeps causing hilarious chaos at work."
3. "A spy must stop a bomb from going off in the city."

Format:
Description 1: [Genre]
Description 2: [Genre]
Description 3: [Genre]

**Output I got:**
Description 1: Horror
Description 2: Comedy
Description 3: Action

### Example 3
**Prompt:**
Classify each piece of student feedback as Positive, Negative, or Mixed.

Feedback:
1. "The teacher explained everything so clearly, I loved this class."
2. "The lectures were too fast and I could not keep up."
3. "Good content but the assignments were way too difficult."

Format:
Feedback 1: [Classification]
Feedback 2: [Classification]
Feedback 3: [Classification]

**Output I got:**
Feedback 1: Positive
Feedback 2: Negative
Feedback 3: Mixed

## References
- https://www.promptingguide.ai/prompts/classification
- https://www.promptingguide.ai/introduction/basics
- https://learnprompting.org/docs/basics/instructions
- https://ai.google.dev/gemini-api/docs/prompting-strategies