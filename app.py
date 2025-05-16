import streamlit as st
from datetime import datetime
from backend.config import SUPABASE_URL, SUPABASE_KEY, PAPERS_TABLE, logger
from backend.supabase_calls import create_supabase_client, get_papers, get_unique_filter_values, get_paper_markdown, insert_generation_to_db
from frontend.fe_components import render_prompt_builder, render_compact_paper_list_pagination, render_save_generation_form
from backend.prompts import generate_prompt
from backend.openrouter_calls import send_ai_request, parse_ai_response

logger.info("Starting ICLR Paper Browser application")

def init_session_state():
    if 'supabase_client' not in st.session_state:
        st.session_state.supabase_client = create_supabase_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Supabase client initialized")
    if 'selected_papers' not in st.session_state:
        st.session_state.selected_papers = []
    if 'filtered_papers' not in st.session_state:
        st.session_state.filtered_papers = []
    if 'list_of_statuses' not in st.session_state or 'list_of_primary_areas' not in st.session_state:
        statuses, areas = get_unique_filter_values(st.session_state.supabase_client, PAPERS_TABLE)
        st.session_state.list_of_statuses = statuses
        st.session_state.list_of_primary_areas = areas
        logger.info("Session state initialized with filter values")
    # Initialize prompt-related session state variables
    if 'prompt_saved' not in st.session_state:
        st.session_state.prompt_saved = False
    if 'prompt_goal' not in st.session_state:
        st.session_state.prompt_goal = ""
    if 'prompt_return_format' not in st.session_state:
        st.session_state.prompt_return_format = ""
    if 'prompt_warnings' not in st.session_state:
        st.session_state.prompt_warnings = ""
    # if 'prompt_context_dump' not in st.session_state:
    #     st.session_state.prompt_context_dump = ""
    if 'generating' not in st.session_state:
        st.session_state.generating = False
    # Add these in your init_session_state function
    if 'has_generated_content' not in st.session_state:
        st.session_state.has_generated_content = False

def main():
    st.set_page_config(layout="wide")
    init_session_state()

    with st.sidebar:
        st.title("ICLR 2025 Paper Browser")

        # Simple run ID field
        run_id_input = st.text_input(
            "Run ID (optional)", 
            value=st.session_state.get('run_id', ''),
            help="Provide a name for this run to group related generations"
        )
        if run_id_input:
            st.session_state.run_id = run_id_input
        
        # Add model selection
        model_options = [
            "anthropic/claude-3.5-sonnet",
            "anthropic/claude-3-opus",
            "anthropic/claude-3-haiku",
            "openai/gpt-4o"
        ]

        selected_model = st.selectbox(
            "AI Model", 
            options=model_options,
            index=0,
            help="Select which AI model to use for generation"
        )
        st.session_state.selected_model = selected_model

        st.header("Search Filters")
        status = st.selectbox("Paper Status", ["All"] + st.session_state.list_of_statuses)
        area = st.selectbox("Research Area", ["All"] + st.session_state.list_of_primary_areas)
        search = st.button("Search Papers")
        


    if search:
        logger.info(f"Search requested - status: {status}, area: {area}")
        st.session_state.filtered_papers = get_papers(
            st.session_state.supabase_client, 
            PAPERS_TABLE,
            paper_status=None if status == "All" else status,
            primary_area=None if area == "All" else area
        )
        logger.info(f"Found {len(st.session_state.filtered_papers)} papers")

    # Create two columns with equal width
    col1, col2 = st.columns([1,1])
    
    with col1:
        # First section: Compact paper list
        render_compact_paper_list_pagination(st.session_state.filtered_papers, "Available Papers")
        
        # Selected papers summary (small, just shows count and titles)
        with st.expander("Selected Papers", expanded=True):
            st.write(f"Total selected: {len(st.session_state.selected_papers)}")
            if len(st.session_state.selected_papers) > 2:
                st.error("Maximum 2 papers allowed")
                logger.warning("Too many papers selected")
            for paper in st.session_state.selected_papers:
                st.write(f"• {paper['title']}")
        
        # Separator
        st.markdown("---")
        
        # Second section: Prompt builder
        render_prompt_builder()
        
        # Buttons for actions
        col1a, col1b = st.columns(2)
        with col1a:
            if st.button("Save Prompt", use_container_width=True):
                saved_prompt = {
                    "goal": st.session_state.prompt_goal,
                    "return_format": st.session_state.prompt_return_format,
                    "directions": st.session_state.prompt_warnings,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                # Store the captured values
                if 'saved_prompts' not in st.session_state:
                    st.session_state.saved_prompts = []
            
                st.session_state.saved_prompts.append(saved_prompt)
                st.session_state.prompt_saved = True
        
                # Success message
                st.success("Prompt saved!")
                logger.info(f"Prompt saved to session state: {saved_prompt}")
                st.session_state.prompt_saved = True
        
        with col1b:
            submit_disabled = len(st.session_state.selected_papers) == 0
            if st.button("Generate", disabled=submit_disabled, use_container_width=True):
                logger.info("Generation requested")
                st.session_state.generating = True

                # Get the content for each selected paper
                papers_with_content = {}

                for paper in st.session_state.selected_papers:
                    paper_data = get_paper_markdown(st.session_state.supabase_client, paper['id'])
                    if paper_data and paper_data.get('markdown_content'):
                        papers_with_content[paper['id']] = {
                            'title': paper['title'],
                            'content': paper_data['markdown_content']
                        }
                
                st.session_state.papers_with_content = papers_with_content
            
    with col2:
        # Full column dedicated to output
        st.subheader("Generation")
        logger.info("Rendering output column")
        
        if 'generating' in st.session_state and st.session_state.generating:
            if not st.session_state.get('content_generated', False):
                logger.info(f"Generating state is True. Session state keys: {list(st.session_state.keys())}")
                st.info("Starting markdown content fetch.")
                if 'papers_with_content' in st.session_state and st.session_state.papers_with_content:
                    logger.info(f"Found papers_with_content with {len(st.session_state.papers_with_content)} papers")
                    st.success(f"Retrieved content for {len(st.session_state.papers_with_content)} papers")

                    # Display a preview of each paper's content
                    for paper_id, paper_data in st.session_state.papers_with_content.items():
                        logger.info(f"Rendering preview for paper: {paper_id}")
                        with st.expander(f"Paper: {paper_data['title']}", expanded=False):
                            content_preview = paper_data['content'][:500] + "..." if len(paper_data['content']) > 500 else paper_data['content']
                            st.markdown(content_preview)

                    with st.spinner(f"Generating prompt with retrieved papers."):
                        logger.info("Starting prompt generation")
                        prompt_generated = generate_prompt(
                            papers_with_content=st.session_state.papers_with_content, 
                            goal=st.session_state.prompt_goal, 
                            return_format=st.session_state.prompt_return_format, 
                            directions=st.session_state.prompt_warnings
                        )
                        st.session_state.prompt_generated = prompt_generated
                        logger.info(f"Prompt generated with length: {len(prompt_generated)}")
                        
                        if st.session_state.prompt_generated:
                            st.success(f"Prompt successfully generated.")
                        else:
                            logger.error("Failed to generate prompt")
                            st.error("Prompt not generated.")
                
                    with st.expander(f"Prompt Generated.", expanded=False):
                        st.text(prompt_generated)
                    
                    with st.spinner(f"Making model call."):
                        logger.info(f"Sending request to model: {st.session_state.selected_model}")
                        raw_model_response = send_ai_request(prompt=prompt_generated, model=st.session_state.selected_model, temperature=0.7)
                        st.session_state.raw_model_response = raw_model_response
                        logger.info("Raw model response received and stored in session state")
                        
                        # Parse the response
                        logger.info("Parsing model response")
                        parsed_response = parse_ai_response(raw_model_response)
                        st.session_state.parsed_response = parsed_response
                        logger.info(f"Response parsing success: {parsed_response['success']}")

                        if parsed_response['success']:
                            st.success("Generation successful!")
                        else:
                            logger.info(f"Generation failed: {parsed_response.get('error', 'Unknown error')}")
                            st.error(f"Generation failed: {parsed_response.get('error', 'Unknown error')}")
                    
                    if 'parsed_response' in st.session_state and st.session_state.parsed_response:
                        logger.info("Checking parsed_response in session state")
                        if st.session_state.parsed_response['success']:
                            logger.info("Parsed response is successful, rendering output")

                            # Show raw response in expander
                            with st.expander("Raw Model Response", expanded=False):
                                st.code(str(st.session_state.raw_model_response), language="json")
                
                            # Show usage information if available
                            if 'usage' in st.session_state.parsed_response:
                                usage = st.session_state.parsed_response['usage'].get('total_tokens', 'unknown')
                                logger.info(f"Token usage: {usage}")
                                st.caption(f"Tokens used: {usage}")
                        
                            # Display the generated research idea
                            logger.info("Rendering research idea expander")
                            with st.expander("Generated Research Idea", expanded=False):
                                st.markdown(st.session_state.parsed_response['content'])
                            
                            st.session_state.content_generated = True
                        else:
                            logger.info("Content already generated, showing save form")
                        
                    if st.session_state.get('content_generated', False) and 'parsed_response' in st.session_state:
                        logger.info("About to render save generation form")
                        # Use the new frontend component
                        save_status = render_save_generation_form(
                            parsed_response=st.session_state.parsed_response,
                            run_id=st.session_state.run_id,
                            selected_papers=st.session_state.selected_papers,
                            prompt_generated=None,
                            selected_model=st.session_state.selected_model,
                            supabase_client=st.session_state.supabase_client
                        )
                        if save_status:
                            logger.info("Save was successful, marking generation as complete")
                            logger.info("Setting generating to False")
                            st.session_state.has_generated_content = True
                            st.session_state.generating = False
                            if not st.session_state.get('save_successful', False):
                                st.session_state.save_successful = True
                        else:
                            logger.info("Save form rendered but no save action taken yet")
        else:
            st.info("Select papers and fill the prompt builder, then click 'Generate' to see responses.")

if __name__ == "__main__":
    main()