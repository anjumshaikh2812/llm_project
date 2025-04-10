import streamlit as st
import ollama
import asyncio
import re

# Custom CSS
custom_css = """
<style>
    /* General Styles */
    body {
        font-family: 'Arial', sans-serif;
        color: #333;
        background-color: #f8f9fa;
    }
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
        padding: 20px;
    }

    /* Header Styles */
    h1 {
        color: #007bff;
        text-align: center;
        margin-bottom: 30px;
    }
    h3 {
        color: #495057;
        margin-top: 25px;
    }

    /* Sidebar Styles */
    .sidebar .sidebar-content {
        background-color: #e9ecef;
        padding: 20px;
        border-radius: 10px;
    }
    .sidebar h2 {
        color: #007bff;
        margin-bottom: 20px;
    }

    /* Text Area Styles */
    .stTextArea textarea {
        border: 1px solid #ced4da;
        border-radius: 5px;
        padding: 10px;
        font-size: 16px;
        color: #495057;
    }

    /* Button Styles */
    .stButton>button {
        background-color: #007bff;
        color: white;
        border: none;
        border-radius: 5px;
        padding: 10px 20px;
        font-size: 16px;
        cursor: pointer;
        transition: background-color 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #0056b3;
    }

    /* Results Styles */
    .results {
        margin-top: 30px;
        padding: 20px;
        background-color: #fff;
        border-radius: 10px;
        box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
    }
    .results h4 {
        color: #28a745;
    }
    .results p {
        color: #495057;
    }

    /* Classification Levels */
    .level-L1 { color: green; }
    .level-L2 { color: orange; }
    .level-L3 { color: red; }
    .level-Unknown { color: gray; }
</style>
"""

# Function to classify SAP ticket
async def classify_sap_ticket_async(ticket_text, model_name):
    prompt = f"""
    You are an AI assistant trained for SAP Support Ticket Classification.
    Classify the following ticket into one of three levels:
    - L1 (Basic): Simple issues like password reset, user access.
    - L2 (Intermediate): Issues needing some configuration changes.
    - L3 (Complex): Deep technical issues, system errors, performance issues.

    Ticket: "{ticket_text}"

    Output the classification as "L1", "L2", or "L3" followed by reasoning.
    """
    response = await asyncio.to_thread(ollama.chat, model=model_name, messages=[{"role": "user", "content": prompt}])
    return response["message"]["content"]

def extract_classification_level(text, model_name):
    if model_name == "deepseek-r1:32b":
        # Split the text into statements
        statements = text.split('.')
        # Get the last 7 statements
        last_statements = statements[-7:]
        # Concatenate the last statements
        last_text = '. '.join(last_statements).lower()
        
        # Check for level indicators in the last statements
        if "level 1" in last_text or "l1" in last_text:
            return "L1"
        elif "level 2" in last_text or "l2" in last_text:
            return "L2"
        elif "level 3" in last_text or "l3" in last_text:
            return "L3"
        else:
            return "Unknown"
    else:
        # General extraction for other models
        match = re.search(r"(L[1-3]|Level\s*[1-3]|L\s*[-]\s*[1-3])", text, re.IGNORECASE)
        if match:
            return match.group(1).replace(" ", "").replace("-", "").upper()
        else:
            return "Unknown"

# Main Streamlit app
def main():
    st.set_page_config(
        page_title="SAP Support Ticket Classifier",
        page_icon="🔧",
        layout="wide"
    )

    # Inject custom CSS
    st.markdown(custom_css, unsafe_allow_html=True)

    # Sidebar for configuration
    with st.sidebar:
        st.markdown('<div class="sidebar"><div class="sidebar-content">', unsafe_allow_html=True)
        st.title("⚙️ Configuration")
        model_choice = st.selectbox(
            "Select AI Model",
            ["llama3.3", "mistral", "deepseek-r1:32b"],
            index=0,
            help="Choose a model to classify SAP tickets."
        )
        st.markdown("</div></div>", unsafe_allow_html=True)

        st.markdown("### Instructions:")
        st.markdown("""
            1. Select the AI model from the dropdown above.
            2. Enter or select a ticket description in the main area.
            3. Click **Classify Ticket** to see results.
            4. Compare results across models by switching models.
        """)

    # Main app title and description
    st.markdown("<h1>🔧 SAP Support Ticket Classifier</h1>", unsafe_allow_html=True)
    st.markdown("This app demonstrates how different AI models classify SAP support tickets into L1, L2, or L3 categories.")

    # Input section for ticket description
    st.markdown("<h3>📝 Enter or Select a Ticket Description</h3>", unsafe_allow_html=True)
    ticket_input = st.text_area(
        "Input your SAP support ticket description below:",
        placeholder="E.g., 'User unable to log in to SAP Fiori. Password reset did not help.'",
        height=150
    )

    # Example tickets
    example_tickets = [
        "User unable to log in to SAP Fiori. Password reset did not help.",
        "Sales order processing is failing due to missing condition records in pricing.",
        "SAP system crashes when running large data extraction jobs in BW.",
        "Unable to create production order due to missing BOM components.",
    ]

    st.markdown("Or select an example ticket:")
    selected_example = st.selectbox("Example Tickets", [""] + example_tickets)

    if selected_example:
        ticket_input = selected_example

    # Button to classify the ticket
    if st.button("🚀 Classify Ticket"):
        if ticket_input.strip():
            with st.spinner("Classifying ticket..."):
                try:
                    result = asyncio.run(classify_sap_ticket_async(ticket_input, model_choice))
                    classification_level = extract_classification_level(result, model_choice)
                    reasoning = result

                    # Display Results
                    st.markdown("<h3>📋 Classification Results</h3>", unsafe_allow_html=True)
                    st.markdown(f"""
                        <div class="results">
                            <h4>Classification: <span class="level-{classification_level.replace(' ', '')}">{classification_level}</span></h4>
                            <p><strong>Reasoning:</strong> {reasoning}</p>
                        </div>
                    """, unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"⚠️ Error during classification: {str(e)}")
        else:
            st.warning("⚠️ Please enter a valid ticket description.")

    # History Section (Optional)
    if "classification_history" not in st.session_state:
        st.session_state.classification_history = []

    if ticket_input and 'result' in locals():
        st.session_state.classification_history.append({
            "model": model_choice,
            "ticket": ticket_input,
            "result": result,
        })

    if st.session_state.classification_history:
        st.markdown("<h3>🕒 Classification History</h3>", unsafe_allow_html=True)
        for entry in reversed(st.session_state.classification_history):
            with st.expander(f"Model: {entry['model']} | Ticket: {entry['ticket'][:50]}..."):
                classification_level = extract_classification_level(entry["result"], entry["model"])
                reasoning = entry["result"]
                st.markdown(f"""
                    <div class="results">
                        <h4>Classification: <span class="level-{classification_level.replace(' ', '')}">{classification_level}</span></h4>
                        <p><strong>Reasoning:</strong> {reasoning}</p>
                    </div>
                """, unsafe_allow_html=True)

    # Footer Instructions
    st.markdown("---")
    st.markdown("### 🚀 How to Run This App Locally")
    st.code("""
    pip install streamlit ollama
    streamlit run sap_ticket_classifier_app.py
    """)

if __name__ == "__main__":
    main()
