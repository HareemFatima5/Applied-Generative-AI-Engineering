# Keyword Extraction

## What is it?
Keyword extraction means asking the AI to read a piece of text and pull out the most important words or topics from it. These keywords tell us what the 
text is mainly about without reading the whole thing.

## How it Works
We give the AI the text and tell it exactly how many keywords we want and what format to return them in. We can also ask it to explain why it chose 
each keyword.

## When to Use it
- When we want to quickly understand what a document is about
- When building a search system or tagging system
- When we need to organize or categorize large amounts of text

## Examples 

### Example 1 
**Prompt:**
Extract exactly 5 keywords from the text below.
These should represent the main topics.
Return them as a numbered list most important first.

Text: Machine learning is a subset of artificial intelligence that enables 
systems to learn from data and improve their performance without being 
explicitly programmed. It is widely used in image recognition, natural 
language processing and recommendation systems.

**Output I got:**
1. Machine learning
2. Artificial intelligence
3. Data
4. Performance
5. Systems

### Example 2
**Prompt:**
Extract exactly 5 keywords from the text below that best describe what it is about.
Return them as a numbered list.

Text: The government of Pakistan has launched a new digital education program 
aimed at providing free online courses to students in rural areas. The initiative 
is funded by the World Bank and will cover subjects like mathematics, science 
and computer skills. Officials hope this will reduce the education gap between 
urban and rural communities.

**Output I got:**
1. Pakistan
2. Education
3. Digital
4. Online
5. Rural

### Example 3 
**Prompt:**
Extract exactly 4 keywords from the text below.
For each keyword also write one short reason why you chose it.
Format:
1. Keyword - Reason

Text: Solar energy is becoming one of the most popular renewable energy sources 
in the world. Countries are investing heavily in solar panels and related 
infrastructure to reduce their dependence on fossil fuels. Experts believe 
solar power could meet 30 percent of the worlds energy needs by 2050.

**Output I got:**
1. Solar - It is the primary subject and energy source discussed in the text.
2. Renewable - It defines the category of energy that solar power belongs to.
3. Infrastructure - It represents the physical investment required to implement solar technology.
4. Fossil fuels - It identifies the traditional energy sources that solar energy is intended to replace.

## References
- https://www.promptingguide.ai/introduction/basics
- https://www.maartengrootendorst.com/blog/keyllm/
- https://aclanthology.org/2025.aisd-main.2.pdf