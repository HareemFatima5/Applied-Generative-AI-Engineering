# JSON Generation

## What is it?
JSON generation means asking the AI to extract information from text and return it in JSON format. JSON is a structured way of organizing data that 
is used in programming and databases. Instead of getting a plain text answer, we get clean organized data we can directly use in code.

## How it Works
We tell the AI exactly which fields we want extracted, give it the text and tell it to return ONLY the JSON with no extra explanation. This keeps 
the output clean and ready to use.

## When to Use it
- When we want to extract data and store it in a database
- When building apps that need structured input
- When processing large amounts of text automatically

## Examples

### Example 1 
**Prompt:**
Extract information from the text and return ONLY a valid JSON object with these fields:
- name
- email
- phone
- company

If any field is missing use null.
Return ONLY the JSON. No explanation.

Text: My name is Hareem Fatima. You can reach me at hareem.fatima@email.com 
or call me at 0300-1234567. I work at TechSoft Solutions.

**Output I got:**
```json
{
  "name": "Hareem Fatima",
  "email": "hareem.fatima@email.com",
  "phone": "0300-1234567",
  "company": "TechSoft Solutions"
}
```

### Example 2
**Prompt:**
Extract information from the text and return ONLY a valid JSON object with these fields:
- product_name
- price
- original_price
- colors
- battery_life

If any field is missing use null.
Return ONLY the JSON. No explanation.

Text: Introducing the UltraSound X200 wireless headphones. Now available for 
just Rs. 8500, down from the original price of Rs. 12000. Comes in black and 
white colors. Battery life up to 30 hours.

**Output I got:**
```json
{
  "product_name": "UltraSound X200",
  "price": "Rs. 8500",
  "original_price": "Rs. 12000",
  "colors": ["black", "white"],
  "battery_life": "30 hours"
}
```

### Example 3 
**Prompt:**
Extract information from the text and return ONLY a valid JSON object with these fields:
- job_title
- company
- location
- experience_required
- skills
- salary_range
- deadline

If any field is missing use null.
Return ONLY the JSON. No explanation.

Text: We are hiring a Senior Data Analyst at DataBridge Pvt Ltd located in 
Lahore. The position requires 3 years of experience in Python and SQL. 
Salary range is Rs. 150,000 to Rs. 200,000 per month. Apply before August 15, 2025.

**Output I got:**
```json
{
  "job_title": "Senior Data Analyst",
  "company": "DataBridge Pvt Ltd",
  "location": "Lahore",
  "experience_required": "3 years",
  "skills": ["Python", "SQL"],
  "salary_range": "Rs. 150,000 to Rs. 200,000 per month",
  "deadline": "August 15, 2025"
}
```

## References
- https://www.promptingguide.ai/introduction/basics
- https://medium.com/@kimdoil1211/structured-output-with-guided-json-a-practical-guide-for-llm-developers-6577b2eee98a
- https://glaforge.dev/posts/2024/11/18/data-extraction-the-many-ways-to-get-llms-to-spit-json-content/