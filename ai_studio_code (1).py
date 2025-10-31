

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Dict, Any
from langchain_community.chat_message_histories import SQLChatMessageHistory
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import pandas as pd
from langchain_core.tools import tool
import random
import os

# --- Configuration ---
# The API key has been placed directly here as requested.
GROQ_API_KEY = "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"
GROQ_MODEL_NAME = "mixtral-8x7b-32768" # Example model, check Groq website for current options
SQLITE_DB_PATH = 'chat_memory_loan_sales.db' # Dedicated DB for loan sales
CHROMA_DB_PERSIST_DIR = "loan_sales_rag.db" # Dedicated ChromaDB for loan sales


llm = ChatGroq(
    groq_api_key=GROQ_API_KEY,
    model_name=GROQ_MODEL_NAME,
    temperature=0.5, # Slightly higher temperature for more conversational feel
    max_tokens=1024, # Increased max tokens for more detailed responses
)

# --- State Space Redefinition ---
class LoanApplication(BaseModel):
    """Represents a single loan application."""
    applicant_name: Optional[str] = None
    desired_amount: Optional[int] = None
    loan_term_months: Optional[int] = None
    purpose: Optional[str] = None
    kyc_verified: bool = False
    credit_score: Optional[int] = None
    credit_eligibility: Optional[Literal["eligible", "not_eligible", "pending"]] = "pending"
    offered_amount: Optional[int] = None
    offered_interest_rate: Optional[float] = None
    sanction_letter_generated: bool = False
    status: Literal["initiated", "kyc_pending", "credit_check_pending", "offer_made", "sanctioned", "rejected", "completed"] = "initiated"

class State(BaseModel):
    """Represents the state of the conversation and loan application process."""
    messages: List[BaseMessage] = Field(default_factory=list)
    current_loan_application: LoanApplication = Field(default_factory=LoanApplication)
    # Add a route for better graph understanding, though LangGraph can infer
    route: str = ""
    # Store relevant facts extracted for context or decision making
    extracted_info: Dict[str, Any] = Field(default_factory=dict)


def get_message_history(session_id: str):
    return SQLChatMessageHistory(session_id=session_id, connection=f'sqlite:///{SQLITE_DB_PATH}')

# --- RAG Setup (Updated for Loan Product Info) ---
# Replace student expenses with mock loan product data
LOAN_PRODUCTS_DATA = [
    "Personal Loan: Max ₹5,00,000, Interest Rate: 10-15%, Term: 12-60 months, Eligibility: Salaried employees, good credit score (650+).",
    "Home Loan: Max ₹50,00,000, Interest Rate: 7-9%, Term: 60-360 months, Eligibility: Property owners, stable income.",
    "Education Loan: Max ₹20,00,000, Interest Rate: 8-12%, Term: 12-120 months, Eligibility: Students admitted to recognized institutions.",
    "Car Loan: Max ₹15,00,000, Interest Rate: 9-14%, Term: 12-84 months, Eligibility: Salaried/Self-employed, new or used car purchase.",
    "Eligibility Criteria: All applicants must be 21-60 years old, Indian citizens, with a minimum monthly income of ₹25,000 for personal loans.",
    "KYC Documents: Valid ID proof (Aadhaar, Passport, Driving License), Address proof (Utility Bill, Bank Statement), PAN Card.",
    "Credit Score Impact: A higher credit score (700+) usually results in better interest rates. Scores below 600 might lead to rejection.",
    "Loan Sanction Process: Once approved, a digital sanction letter is issued. Physical documents might be required for final disbursement."
]

chroma_c = chromadb.Client(Settings(persist_directory=CHROMA_DB_PERSIST_DIR, anonymized_telemetry=False))
collection = chroma_c.get_or_create_collection(name="loan_sales_rag_collection")
embedder = SentenceTransformer("all-MiniLM-L6-v2")

def index_loan_products(data_chunks):
    """Indexes loan product information into ChromaDB."""
    print("Indexing loan product information...")
    embeddings = embedder.encode(data_chunks).tolist() # Ensure embeddings are lists
    ids = [f"loan_product_{i}" for i in range(len(data_chunks))]
    collection.add(
        documents=data_chunks,
        embeddings=embeddings,
        ids=ids,
        metadatas=[{"source": "internal_loan_data"}] * len(data_chunks)
    )
    print(f"Indexed {len(data_chunks)} loan product chunks.")

# Re-index with loan product data
# Clear existing collection if re-running frequently for development
try:
    chroma_c.delete_collection(name="loan_sales_rag_collection")
    collection = chroma_c.get_or_create_collection(name="loan_sales_rag_collection")
except Exception as e:
    print(f"Could not delete collection (might not exist): {e}")
index_loan_products(LOAN_PRODUCTS_DATA)


prompt_template = ChatPromptTemplate.from_messages([
    ("system", "{system_message}"),
    MessagesPlaceholder("message_history")
])
llm_p = prompt_template | llm

# --- New Tools for Loan Sales Assistant ---

@tool
def update_loan_application_details(
    state: State,
    applicant_name: Optional[str] = None,
    desired_amount: Optional[int] = None,
    loan_term_months: Optional[int] = None,
    purpose: Optional[str] = None
) -> State:
    """
    Updates the current loan application with details provided by the user.
    Use this to capture applicant's name, desired loan amount, term, and purpose.
    """
    if applicant_name:
        state.current_loan_application.applicant_name = applicant_name
    if desired_amount:
        state.current_loan_application.desired_amount = desired_amount
    if loan_term_months:
        state.current_loan_application.loan_term_months = loan_term_months
    if purpose:
        state.current_loan_application.purpose = purpose
    state.messages.append(SystemMessage(content=f"Updated loan application: {state.current_loan_application.json()}"))
    return state


@tool
def retrieve_context(state: State, query: str = None, top_k: int = 3) -> str:
    """
    Retrieves relevant information from the loan product knowledge base based on a query.
    Use this to answer questions about loan eligibility, available products, required documents, etc.
    If no query is provided, it uses the last user message.
    """
    actual_query = query if query else (state.messages[-1].content if state.messages else "")
    if not actual_query:
        return "No specific query provided for context retrieval."

    query_embedding = embedder.encode([actual_query])[0].tolist() # Ensure embedding is a list

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )
    docs = results["documents"][0] if results["documents"] else []
    
    if docs:
        retrieved_content = "\n".join(docs)
        # Store context in state for potential use by other nodes/LLM
        state.extracted_info["rag_context"] = retrieved_content
        return retrieved_content
    else:
        return "No relevant information found in the knowledge base."

@tool
def verify_kyc(state: State, applicant_name: str) -> State:
    """
    Simulates the KYC verification process. In a real system, this would
    involve external API calls and document verification. For this simulation,
    it always succeeds.
    """
    print(f"Simulating KYC verification for {applicant_name}...")
    # In a real scenario, this would be an API call to a KYC service
    state.current_loan_application.kyc_verified = True
    state.current_loan_application.status = "credit_check_pending"
    state.messages.append(SystemMessage(content=f"KYC for {applicant_name} successfully verified."))
    return state

@tool
def evaluate_creditworthiness(state: State, desired_amount: int) -> State:
    """
    Simulates evaluating creditworthiness and determining loan eligibility and offer.
    This is a mock implementation.
    """
    print(f"Simulating creditworthiness evaluation for loan amount {desired_amount}...")
    # Mock logic: Generate a random credit score and determine eligibility
    mock_credit_score = random.randint(500, 850)
    state.current_loan_application.credit_score = mock_credit_score

    # Simple mock eligibility logic
    if mock_credit_score >= 650 and desired_amount <= 500000: # Personal Loan max from RAG
        state.current_loan_application.credit_eligibility = "eligible"
        state.current_loan_application.offered_amount = min(desired_amount, random.randint(300000, 500000))
        state.current_loan_application.offered_interest_rate = round(random.uniform(10.0, 12.5), 2)
        state.current_loan_application.status = "offer_made"
        state.messages.append(SystemMessage(content=f"Credit check passed. Score: {mock_credit_score}. Offer made."))
    else:
        state.current_loan_application.credit_eligibility = "not_eligible"
        state.current_loan_application.offered_amount = 0
        state.current_loan_application.offered_interest_rate = 0.0
        state.current_loan_application.status = "rejected"
        state.messages.append(SystemMessage(content=f"Credit check failed. Score: {mock_credit_score}. Not eligible."))
    return state

@tool
def generate_loan_sanction_letter(state: State) -> State:
    """
    Simulates the generation of a digital loan sanction letter.
    In a real system, this would create a PDF document.
    """
    if not state.current_loan_application.offered_amount or state.current_loan_application.offered_amount <= 0:
        state.messages.append(SystemMessage(content="Cannot generate sanction letter: No valid offer made."))
        return state

    print(f"Generating sanction letter for {state.current_loan_application.applicant_name} for ₹{state.current_loan_application.offered_amount}...")
    # Mock: Just set the flag and provide a URL
    state.current_loan_application.sanction_letter_generated = True
    state.current_loan_application.status = "sanctioned"
    letter_url = f"https://mock-bank.com/sanction_letters/{state.current_loan_application.applicant_name.replace(' ', '_')}_{random.randint(1000,9999)}.pdf"
    state.messages.append(SystemMessage(content=f"Loan sanction letter generated and sent. Access it at: {letter_url}"))
    state.extracted_info["sanction_letter_url"] = letter_url
    return state


# --- LLM with Tools Binding ---
llm_with_loan_tools = llm.bind_tools([
    update_loan_application_details,
    retrieve_context,
    verify_kyc,
    evaluate_creditworthiness,
    generate_loan_sanction_letter,
])


# --- LangGraph Nodes ---

def initial_greeting(state: State) -> State:
    """Initial greeting and sets the stage for loan application."""
    if not state.messages: # Only greet if starting fresh
        greeting_message = AIMessage(content="Hello! I'm your AI Loan Sales Assistant from NBFC. I can help you find the right personal loan. What kind of loan are you interested in, or how much do you need?")
        state.messages.append(greeting_message)
    return state

def conversational_agent(state: State):
    """
    The main conversational node. It uses tools based on user input and the current state
    of the loan application, and also leverages RAG for product info.
    """
    # Ensure current state is passed to the LLM for context, especially the loan application
    system_prompt_content = f"""You are an Agentic AI Loan Sales Assistant for a Non-Banking Financial Company (NBFC).
Your goal is to guide users through the personal loan application process, answer questions about loan products, and facilitate loan sanction.
Use the provided tools to gather information, perform checks (KYC, credit), and generate sanction letters.
Always be helpful, professional, and proactive in guiding the user.

Current Loan Application Status:
Applicant Name: {state.current_loan_application.applicant_name if state.current_loan_application.applicant_name else 'N/A'}
Desired Amount: {state.current_loan_application.desired_amount if state.current_loan_application.desired_amount else 'N/A'}
Loan Term: {state.current_loan_application.loan_term_months if state.current_loan_application.loan_term_months else 'N/A'} months
Purpose: {state.current_loan_application.purpose if state.current_loan_application.purpose else 'N/A'}
KYC Verified: {'Yes' if state.current_loan_application.kyc_verified else 'No'}
Credit Eligibility: {state.current_loan_application.credit_eligibility}
Current Status: {state.current_loan_application.status}

Context from RAG (if any):
{state.extracted_info.get('rag_context', 'No external context retrieved yet.')}

Guide the user through these steps:
1. **Initial Information Gathering:** Ask for name, desired loan amount, purpose, and preferred term. Use `update_loan_application_details`.
2. **KYC Verification:** Once name is known, suggest/perform `verify_kyc`.
3. **Credit Evaluation:** Once amount is known and KYC is done, suggest/perform `evaluate_creditworthiness`.
4. **Offer Presentation:** If eligible, present the loan offer (amount, rate, term).
5. **Sanction Letter:** If the user accepts the offer, `generate_loan_sanction_letter`.
6. **Answer Questions:** Use `retrieve_context` tool to answer questions about loan products, eligibility, documents, etc.
7. **Handle Rejection:** If not eligible, explain why and suggest alternatives if possible.
8. **Always be polite and clear.**
"""

    result = llm_with_loan_tools.invoke({
        'system_message': system_prompt_content,
        'message_history': state.messages,
    })

    # Append the AI's response to the message history
    state.messages.append(result)
    print(f"AI Assistant: {result.content}") # Print AI's direct response

    return state


def decide_next_step(state: State) -> str:
    """
    Decides the next action based on the current state of the loan application.
    This acts as the router for the agentic behavior.
    """
    app = state.current_loan_application
    last_msg = state.messages[-1]
    
    # Check if a tool call was just made and if so, if it changed the status
    if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
        # If the LLM decided to call a tool, we process the tool call's effect in the conversational_agent
        # Then we come back here to decide the next step based on the *updated* state.
        # This is implicitly handled as the tool execution updates the state before we reach this node.
        pass # No explicit "tool_called" state, just evaluate the new application status.


    if app.status == "initiated":
        # Need to gather basic info
        if not app.applicant_name or not app.desired_amount or not app.purpose:
            return "conversational_agent" # Continue gathering info

        # If all initial info is gathered, move to KYC
        app.status = "kyc_pending"
        return "conversational_agent" # The agent will now prompt for KYC or call verify_kyc


    if app.status == "kyc_pending":
        if not app.kyc_verified:
            # The agent should call verify_kyc. If it hasn't, keep prompting.
            # If the last message was a tool call to verify_kyc, the status would have changed
            return "conversational_agent"
        else:
            app.status = "credit_check_pending" # KYC verified, move to credit check
            return "conversational_agent"

    if app.status == "credit_check_pending":
        if app.credit_eligibility == "pending":
            # The agent should call evaluate_creditworthiness.
            return "conversational_agent"
        elif app.credit_eligibility == "eligible":
            app.status = "offer_made"
            return "conversational_agent" # Present offer
        else: # not_eligible
            return "conversational_agent" # Explain rejection

    if app.status == "offer_made":
        # Check for user acceptance or further questions
        # This requires more advanced intent recognition, for now, just keep conversing
        # until generate_loan_sanction_letter is called
        return "conversational_agent"

    if app.status == "sanctioned":
        # Sanction letter generated, the process is largely complete for this loan.
        return "end_process" # Or could offer further assistance

    if app.status == "rejected":
        # Loan rejected, agent should explain. User might have further questions.
        return "conversational_agent" # Allow for follow-up questions

    # Default to conversational agent if no specific action is mandated by status
    return "conversational_agent"


# --- LangGraph Definition ---
def loan_sales_agent_graph():
    builder = StateGraph(State)

    # Nodes
    builder.add_node("initial_greeting", initial_greeting)
    builder.add_node("conversational_agent", conversational_agent)
    # The tools are used by the 'conversational_agent' node, so we don't add them as separate nodes directly.

    # Entry point
    builder.set_entry_point("initial_greeting")

    # Edges (Workflow)
    # After greeting, always go to the conversational agent
    builder.add_edge("initial_greeting", "conversational_agent")

    # The conversational agent might call tools and update the state.
    # After the conversational agent, we decide the next step.
    builder.add_conditional_edges(
        "conversational_agent",
        decide_next_step,
        {
            "conversational_agent": "conversational_agent", # Continue conversation/tool use
            "end_process": END # End the graph execution
        }
    )

    memory = InMemorySaver()
    graph = builder.compile(checkpointer=memory)
    return graph


# --- Main Session Loop ---
def start_loan_sales_session():
    chatbot = loan_sales_agent_graph()
    config = {"configurable": {"thread_id": "_loan_sales_session_1"}}

    # Initialize state with a greeting message to kick off
    initial_state = State()
    # The initial_greeting node will add the first message

    print("\n=== NBFC AI Loan Sales Assistant ===")
    print("I'm here to help you with your personal loan application.")

    # Call the graph once to get the initial greeting
    result = chatbot.invoke(initial_state, config=config)
    # The initial_greeting node will populate state.messages with the greeting.
    # The subsequent decide_next_step will likely return "conversational_agent"
    # and the loop will then use the latest state.

    # Update current_state for the loop with the initial state from the graph
    current_state = result


    while True:
        user_input = input("\nCustomer: ")

        if user_input.lower() in ['quit', 'exit', 'bye', 'end']:
            print("\nThank you for considering our loans. Have a great day!")
            break

        if not user_input.strip():
            print("Please tell me how I can assist you with a loan today.")
            continue

        # Add user message to the current state's messages
        current_state.messages.append(HumanMessage(content=user_input))
        
        # Invoke the chatbot with the updated state
        current_state = chatbot.invoke(current_state, config=config)

        # After invoke, the AIMessage (LLM response or tool call output) will be in state.messages[-1]
        # The conversational_agent node also prints the AI's direct response.

# Entry point for execution
if __name__ == "__main__":
    start_loan_sales_session()

