# Operations Analysis Agent

A local, conversational AI agent that analyzes ServiceNow CSV ticket dumps. Built with Streamlit, it supports data cleaning, entity extraction, local sentence-transformers embedding, clustering, and categorization.

## How to Run

1. **Install dependencies:**
   Ensure you have Python 3.10+ installed. Then install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure your environment:**
   Copy the example environment file and fill in your LLM API details:
   ```bash
   cp .env.example .env
   ```
   *Note: Open `.env` and set your `LLM_API_KEY` and any other custom settings.*

3. **Run the Streamlit application:**
   Launch the app using the Streamlit CLI:
   ```bash
   streamlit run app.py
   ```

4. **Interact:**
   - The UI will open automatically in your browser (usually at http://localhost:8501).
   - Upload your ServiceNow CSV export using the sidebar.
   - Use the chat interface to instruct the agent (e.g., "Clean the data and categorize the tickets").

## Project Structure
- `app.py`: Main Streamlit UI entrypoint.
- `core/`: Agent loop, prompt building, token streaming, and session management.
- `tools/`: Implementations of the various analysis tools the agent can invoke.
- `db/`: SQLite database models and setup.
- `storage/`: Artifact and file management.
