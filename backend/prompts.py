def generate_prompt(
    papers_with_content,
    goal,
    return_format,
    directions
):
    """
    Generate a minimal, straightforward prompt for research idea generation.
    
    Args:
        papers_with_content (dict): Dictionary of paper_id -> {title, content}
        goal (str): The research goal/approach from the prompt builder
        return_format (str): The desired output format
        directions (str): Additional directions/warnings for generation
        
    Returns:
        str: The complete prompt ready to send to OpenRouter
    """
    prompt = ""
    
    # Add goal if provided
    if goal:
        prompt += f"{goal}\n\n"
    
    # Add return format if provided
    if return_format:
        prompt += f"{return_format}\n\n"
    
    # Add directions if provided
    if directions:
        prompt += f"{directions}\n\n"
    
    # Add papers with minimal formatting
    prompt += "Here are the papers to work on.\n\n"
    for i, (paper_id, paper_data) in enumerate(papers_with_content.items()):
        prompt += f"### Paper {i+1}: {paper_data['title']}\n"
        prompt += f"{paper_data['content']}\n\n"
        
    return prompt.strip()