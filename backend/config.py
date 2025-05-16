import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Openrouter Config
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Supabase config
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Table names
PAPERS_TABLE = "ICLR_25_papers"

# Logger config
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)