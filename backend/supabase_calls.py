from typing import Optional, List, Dict
from supabase import create_client, Client
from backend.config import SUPABASE_URL, SUPABASE_KEY, PAPERS_TABLE, logger

def create_supabase_client(supabase_url: str, supabase_key: str):
    """
    Takes in supabase url and key
    Returns a client object
    """
    logger.info("Setting up Supabase client.")
    supabase_client: Client = create_client(supabase_url, supabase_key)
    return supabase_client

def get_papers(
    supabase_client: Client,
    table_name: str,
    paper_status: Optional[str] = None,
    primary_area: Optional[str] = None
) -> List[Dict]:
    """
    Fetch papers with optional status and area filters
    Returns list of paper objects with id, title, status, area
    """
    logger.info(f"Fetching papers with filters - status: {paper_status}, area: {primary_area}")
    logger.info("Setting up the search query.")
    query = supabase_client.table(table_name).select('id', 'title', 'primary_area', 'paper_status')
    
    if paper_status:
        logger.info(f"Adding the paper_status filter: {paper_status}")
        query = query.eq('paper_status', paper_status)
    if primary_area:
        logger.info(f"Adding the primary_area filter: {primary_area}")
        query = query.eq('primary_area', primary_area)
    
    logger.info(f"Executing the search query.")
    try:
        response = query.execute()
        if response:
            logger.info(f"Response received.")
            list_of_papers = response.data
    except Exception as e:
        logger.info(f"Error during Supabase call: {e}")
    return list_of_papers

def get_unique_filter_values(client: Client, table_name: str) -> tuple[list, list]:
    """Get unique status and area values directly from table"""
    status_query = client.table(table_name).select('paper_status').execute()
    area_query = client.table(table_name).select('primary_area').execute()
    
    statuses = sorted(list(set(p['paper_status'] for p in status_query.data)))
    areas = sorted(list(set(p['primary_area'] for p in area_query.data)))
    
    logger.info(f"Retrieved {len(statuses)} statuses and {len(areas)} areas")
    return statuses, areas


def get_paper_markdown(supabase_client, paper_id, table_name="ICLR_25_papers"):
    """
    Retrieve paper markdown content from Supabase storage.
    
    Args:
        supabase_client: Supabase client instance
        paper_id: ID of the paper in the database
        table_name: Name of the table containing paper records
        
    Returns:
        dict: Simple dict with paper_id and markdown_content (or None if unavailable)
    """
    logger.info(f"Retrieving markdown for paper ID: {paper_id}")
    
    # Create basic result structure with just the ID
    result = {"paper_id": paper_id, "markdown_content": None}
    
    try:
        # Get just the markdown path from the paper record
        response = supabase_client.table(table_name).select(
            "md_bucket_path"
        ).eq("id", paper_id).execute()
        
        if not response.data or not response.data[0]:
            logger.warning(f"Paper with ID {paper_id} not found")
            return result
            
        md_path = response.data[0].get("md_bucket_path")
        
        # Get markdown content if path is available
        if md_path:
            try:
                # Split at first slash to get bucket and file path
                md_bucket, md_file_path = md_path.split('/', 1)
                
                # Download the raw content
                md_bytes = supabase_client.storage.from_(md_bucket).download(md_file_path)
                
                # Try to decode the content in a separate try-except block
                try:
                    result["markdown_content"] = md_bytes.decode('utf-8')
                    logger.info(f"Markdown content successfully decoded for paper {paper_id}")
                except UnicodeDecodeError as decode_error:
                    logger.error(f"Failed to decode markdown content for paper {paper_id}: {decode_error}")
                    # Keep markdown_content as None
                
            except Exception as e:
                logger.error(f"Error retrieving markdown content for paper {paper_id}: {e}")
                # markdown_content remains None
        else:
            logger.warning(f"No markdown path found for paper {paper_id}")
            # markdown_content remains None
                    
        return result
        
    except Exception as e:
        logger.error(f"Error in get_paper_markdown for paper {paper_id}: {e}")
        return result


def insert_generation_to_db(
    supabase_client: Client,
    run_id: str,
    content_generated: str,
    tags: list = None,
    score: int = None,
    source_papers: list = None,
    prompt_text: str = None,
    model_used: str = None,
    token_usage: dict = None
) -> dict:
    """
    Insert a generated research idea into the Generations_table.
    
    Args:
        supabase_client: Supabase client instance
        run_id: Unique identifier for the generation session
        content_generated: The full generated research idea text
        tags: Optional list of tags for categorization
        score: Optional user-assigned score (1-5)
        source_papers: Optional list of paper IDs used for generation
        prompt_text: Optional full prompt text sent to the model
        model_used: Optional identifier for the AI model used
        token_usage: Optional token usage statistics
        
    Returns:
        dict: The inserted record from Supabase, or None if insertion failed
    """
    logger.info(f"Inserting new generation with run_id: {run_id}")
    
    # Prepare data for insertion, handling optional fields
    generation_data = {
        "run_id": run_id,
        "content_generated": content_generated
    }
    
    # Add optional fields if provided
    if tags is not None:
        generation_data["tags"] = tags
    
    if score is not None:
        generation_data["score"] = score
    
    if source_papers is not None:
        generation_data["source_papers"] = source_papers
    
    if prompt_text is not None:
        generation_data["prompt_text"] = prompt_text
    
    if model_used is not None:
        generation_data["model_used"] = model_used
    
    if token_usage is not None:
        generation_data["token_usage"] = token_usage
    
    try:
        # Insert the data into the Generations_table
        response = supabase_client.table("Generations_table").insert(generation_data).execute()
        
        if response and response.data:
            logger.info(f"Successfully inserted generation with ID: {response.data[0].get('id')}")
            return response.data[0]
        else:
            logger.error("Insert returned no data")
            return None
            
    except Exception as e:
        logger.error(f"Error inserting generation: {e}")
        return None

# if __name__ == "__main__":
#     client = create_supabase_client(SUPABASE_URL, SUPABASE_KEY)
    # papers = get_papers(client, PAPERS_TABLE, paper_status="Accepted")
    # print(f"Found {len(papers)} papers")
    # print(papers[:2])  # Preview first two
    # for item in papers: 
    #     paper_id = item["id"]
    #     md_content = get_paper_markdown(client, paper_id="fh7GYa7cjO")
    #     print(md_content["id"])
    #     print(md_content["markdown_content"][:30])

    # md_content = get_paper_markdown(client, paper_id="fh7GYa7cjO")
    # print(md_content["paper_id"])
    # print(md_content["markdown_content"][:30])
