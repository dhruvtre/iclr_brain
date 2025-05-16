import streamlit as st
from backend.config import logger
from backend.supabase_calls import insert_generation_to_db

def render_prompt_builder():
    """
    Renders the prompt builder UI component with text fields for Goal, Return Format, 
    Additional Directions, and Context Dump. Values are stored directly in session state.
    """
    st.subheader("Prompt Builder")
    
    # Initialize session state variables if they don't exist
    if 'prompt_goal' not in st.session_state:
        st.session_state.prompt_goal = ""
    if 'prompt_return_format' not in st.session_state:
        st.session_state.prompt_return_format = ""
    if 'prompt_warnings' not in st.session_state:
        st.session_state.prompt_warnings = ""
    if 'prompt_context_dump' not in st.session_state:
        st.session_state.prompt_context_dump = ""
    
    # Goal section
    st.markdown("#### Goal")
    st.text_area(
        "Define the research goal or approach (e.g., combine papers, find gaps, build upon)",
        value=st.session_state.prompt_goal,
        height=100,
        key="prompt_goal"
    )
    
    # Return Format section
    st.markdown("#### Return Format")
    st.text_area(
        "Specify the format for the generated research idea",
        value=st.session_state.prompt_return_format,
        height=150,
        key="prompt_return_format"
    )
    
    # Warnings section
    st.markdown("#### Directions")
    st.text_area(
        "Add any directions, warnings or constraints for the generation process",
        value=st.session_state.prompt_warnings,
        height=100,
        key="prompt_warnings"
    )
    
    # # Context Dump section
    # st.markdown("#### Context Dump")
    # st.text_area(
    #     "Additional context to include in the prompt",
    #     value=st.session_state.prompt_context_dump,
    #     height=150,
    #     key="prompt_context_dump"
    # )

def render_compact_paper_list(papers, title="Papers"):
    """
    Renders a compact, scrollable list of papers with checkboxes.
    """
    st.subheader(title)
    
    # Create a container with fixed height and scrolling
    paper_container = st.container()
    
    # Set a fixed height for the paper list with scrolling
    with paper_container:
        # Use a scrollable container with CSS
        st.markdown("""
            <style>
            .paper-list {
                height: 300px;
                overflow-y: auto;
                padding-right: 10px;
                border: 1px solid rgba(49, 51, 63, 0.2);
                border-radius: 4px;
                padding: 10px;
            }
            </style>
            """, unsafe_allow_html=True)
        
        # Open the scrollable div
        st.markdown('<div class="paper-list">', unsafe_allow_html=True)
        
        # Display papers with checkboxes
        for paper in papers:
            if st.checkbox(f"{paper['title']}", key=paper['id']):
                if paper not in st.session_state.selected_papers:
                    st.session_state.selected_papers.append(paper)
                    # logger.info(f"Selected: {paper['id']}")
            elif paper in st.session_state.selected_papers:
                st.session_state.selected_papers.remove(paper)
                # logger.info(f"Deselected: {paper['id']}")
        
        # Close the scrollable div
        st.markdown('</div>', unsafe_allow_html=True)


def render_compact_paper_list_dropdown(papers, title="Papers"):
    """
    Renders papers using a multiselect instead of checkboxes for more compact display.
    """
    st.subheader(title)
    
    if not papers:
        st.info("No papers available. Use the search filters to find papers.")
        return
    
    # Create a dict mapping paper titles to paper objects for easy lookup
    paper_dict = {paper['title']: paper for paper in papers}
    
    # Get currently selected paper titles
    selected_titles = [paper['title'] for paper in st.session_state.selected_papers]
    
    # Show multiselect with current selections
    new_selections = st.multiselect(
        "Select papers (max 2):",
        options=list(paper_dict.keys()),
        default=selected_titles
    )
    
    # Update selected_papers based on multiselect
    st.session_state.selected_papers = [paper_dict[title] for title in new_selections]
    
    # Show warning if too many papers selected
    if len(st.session_state.selected_papers) > 2:
        st.warning("Maximum 2 papers allowed")

def render_compact_paper_list_pagination(papers, title="Papers"):
    """
    Renders papers in a paginated format with more compact paper cards.
    """
    st.subheader(title)
    
    if not papers:
        st.info("No papers available. Use the search filters to find papers.")
        return
    
    # Initialize pagination state if not exists
    if 'page_number' not in st.session_state:
        st.session_state.page_number = 0
    
    # Set papers per page - increase this number for more papers per page
    papers_per_page = 5  # Increased from 5 to 10
    
    # Calculate total pages
    total_pages = len(papers) // papers_per_page
    if len(papers) % papers_per_page > 0:
        total_pages += 1
    
    # Show papers count and pagination info
    st.caption(f"Found {len(papers)} papers | Page {st.session_state.page_number + 1} of {total_pages}")
    
    # Get current page of papers
    start_idx = st.session_state.page_number * papers_per_page
    end_idx = min(start_idx + papers_per_page, len(papers))
    current_page_papers = papers[start_idx:end_idx]
    
    # Add CSS to make elements more compact
    st.markdown("""
        <style>
        /* Reduce vertical padding in paper containers */
        .paper-card {
            margin: 0px 0px !important;
            padding: 0px 0px !important;
        }
        /* Make dividers thinner */
        .thin-divider {
            margin: 0px 0px !important;
            padding: 0px !important;
        }
        /* Smaller text for titles */
        .paper-title {
            margin: 0px !important;
            font-size: 18px !important;
            line-height: 1.2 !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Display current page of papers
    for paper in current_page_papers:
        # Create a container for each paper with custom class
        st.markdown('<div class="paper-card">', unsafe_allow_html=True)
        
        # Use columns for paper info and selection
        col1, col2 = st.columns([5, 1])
        
        with col1:
            # Use custom styled title
            st.markdown(f'<div class="paper-title">{paper["title"]}</div>', unsafe_allow_html=True)
        
        with col2:
            # Checkbox for selection
            is_selected = paper in st.session_state.selected_papers
            if st.checkbox("Select Paper", value=is_selected, key=f"select_{paper['id']}", label_visibility="collapsed"):
                if paper not in st.session_state.selected_papers:
                    st.session_state.selected_papers.append(paper)
                    logger.info(f"Paper with title {paper['title']} selected.")
            elif paper in st.session_state.selected_papers:
                st.session_state.selected_papers.remove(paper)
                logger.info(f"Paper with title {paper['title']} removed from selection.")
        
        # Close the paper card div
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Add a thin divider between papers
        st.markdown('<hr class="thin-divider">', unsafe_allow_html=True)
    
    # Pagination controls - more compact layout
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button("← Prev", disabled=st.session_state.page_number <= 0, use_container_width=True):
            st.session_state.page_number -= 1
            st.rerun()
    
    with col2:
        st.caption(f"Page {st.session_state.page_number + 1} of {total_pages}", unsafe_allow_html=True)
    
    with col3:
        if st.button("Next →", disabled=st.session_state.page_number >= total_pages - 1, use_container_width=True):
            st.session_state.page_number += 1
            st.rerun()

def render_save_generation_form(parsed_response, run_id, selected_papers, prompt_generated, selected_model, supabase_client):
    # Use a simple callback function to handle the save
    def save_to_db():
        try:
            content = parsed_response['content']
            tags = [tag.strip() for tag in st.session_state.tags_input.split(',')] if st.session_state.tags_input else []
            source_papers = [paper['id'] for paper in selected_papers]
            
            result = insert_generation_to_db(
                supabase_client=supabase_client,
                run_id=run_id,
                content_generated=content,
                tags=tags,
                source_papers=source_papers,
                prompt_text=prompt_generated,
                model_used=selected_model,
                token_usage=parsed_response.get('usage', None),
                score=None
            )
            
            if result:
                st.session_state.save_successful = True
                st.session_state.generating = True 
                st.session_state.content_generated = True
            
        except Exception as e:
            st.session_state.save_error = str(e)
    
    # Already saved?
    if st.session_state.get('save_successful', False):
        st.success("Generation saved successfully!")
        return True
    
    # Show any previous errors
    if 'save_error' in st.session_state and st.session_state.save_error:
        st.error(f"Error: {st.session_state.save_error}")
    
    # Simple text input with callback on button click
    st.text_input("Tags (comma-separated)", key="tags_input")
    st.button("Save Generation", on_click=save_to_db)
    
    return st.session_state.get('save_successful', False)