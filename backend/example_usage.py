"""
Example usage of the relevance filter for generating LLM prompts.
"""

from relevance_filter import generate_llm_prompt_from_file, generate_llm_prompt
import json

# Example 1: Generate prompt from JSON file
if __name__ == "__main__":
    print("=" * 80)
    print("Example: Generating LLM prompt from mock_data.json")
    print("=" * 80)
    print()
    
    prompt = generate_llm_prompt_from_file('mock_data.json')
    print(prompt)
    
    print()
    print("=" * 80)
    print("Example: Generating prompt with custom tone")
    print("=" * 80)
    print()
    
    # Example 2: Generate prompt with custom tone
    prompt_custom = generate_llm_prompt_from_file(
        'mock_data.json', 
        tone="excited, highlight-reel style"
    )
    print(prompt_custom)
    
    print()
    print("=" * 80)
    print("Example: Using with in-memory data")
    print("=" * 80)
    print()
    
    # Example 3: Using with in-memory data
    with open('mock_data.json', 'r') as f:
        game_data = json.load(f)
    
    prompt_memory = generate_llm_prompt(game_data, tone="analytical, data-driven")
    print(prompt_memory)
