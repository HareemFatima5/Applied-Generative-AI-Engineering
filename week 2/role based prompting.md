# Role-Based Prompting

## What is it?
Role based prompting means telling the AI to act as a specific person or expert. When we give the AI a role, it changes how it speaks and what kind of 
answer it gives.

## When to Use it
- When we need expert level answers
- When we want a specific tone like friendly, professional or simple
- When we want the AI to teach, interview or advise

## Examples I Tried

### Example 1 
**Prompt:**
"""You are a Python teacher who has been teaching beginners for 10 years.One of your students does not understand what a loop is.
Explain what a for loop is in Python using a very simple real life example. Then show a basic code example."""

**Output I got:**
Output: Hello there! It’s great to see you. Don’t worry at all—most of my students struggle with the concept of a "loop" at first. But once you see it in the real world, it’s actually quite simple.

### The Real-Life Example: The Mailbox
Imagine you have a stack of 10 envelopes on your desk that need to be mailed. 

If you were a computer without a loop, you would have to write out instructions for every single one:
1. Pick up envelope #1, stamp it, and put it in the bag.
2. Pick up envelope #2, stamp it, and put it in the bag.
3. Pick up envelope #3, stamp it, and put it in the bag... 
...and so on until #10. That is tedious and repetitive!

**A loop** is like giving yourself one simple instruction:
*"For every envelope in this stack, stamp it and put it in the bag."*

You don't care if there are 10 envelopes or 100; you just repeat that same action until the stack is empty. You’ve just performed a loop!

***

### The Python Code
In Python, we use the `for` keyword to do exactly that. We take a collection of items (like our stack of envelopes) and tell Python to perform an action for each one.

Here is how you would write that in code:

```python
# Here is our "stack" of envelopes
envelopes = ["Envelope 1", "Envelope 2", "Envelope 3", "Envelope 4", "Envelope 5"]

# This is the loop:
# "for every item in the stack, do this action"
for envelope in envelopes:
    print("I am stamping " + envelope)

print("All done!")
```

### What is happening here?
1. **`envelopes`**: This is our list (the stack on your desk).
2. **`for envelope in envelopes:`**: This tells Python to look at the list, grab the first item, and call it `envelope`. It then runs the code inside the loop.
3. **The indented code (`print...`)**: This is the action you perform on each item. 
4. **Repeating**: Once Python finishes that line, it goes back to the top, grabs the *next* item from the list, and runs the same code again. It does this automatically until there are no items left.

Does that help make the concept feel a little less "robotic"? Think of the loop as your way of being efficient—you’re telling the computer to handle the repetition so you don't have to!

## References
- https://www.geeksforgeeks.org/artificial-intelligence/role-based-prompting/
- https://learnprompting.org/docs/basics/roles
- https://ai.google.dev/gemini-api/docs/prompting-strategies