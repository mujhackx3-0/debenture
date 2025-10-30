"""
Simplified Loan Sales Agent with Groq LLM integration.
"""
import asyncio
import random
from typing import Dict, Any, AsyncGenerator
from langchain_groq import ChatGroq
from langchain.schema import HumanMessage, AIMessage, SystemMessage

from app.config import settings
from app.utils.logger import logger
from app.core.rag import RAGSystem


class LoanSalesAgent:
    """
    AI-powered loan sales assistant using Groq LLM.
    """
    
    def __init__(self, rag_system: RAGSystem):
        self.rag_system = rag_system
        self.llm = ChatGroq(
            groq_api_key=settings.GROQ_API_KEY,
            model_name=settings.GROQ_MODEL_NAME,
            temperature=settings.GROQ_TEMPERATURE,
            max_tokens=settings.GROQ_MAX_TOKENS,
            timeout=settings.GROQ_TIMEOUT
        )
        
        # Import session manager at runtime to avoid circular imports
        from app.core.session import SessionManager
        self.session_manager: SessionManager = None
    
    def set_session_manager(self, session_manager):
        """Set session manager reference."""
        self.session_manager = session_manager
    
    def get_initial_greeting(self) -> str:
        """Get initial greeting message."""
        return "Hello! I'm your AI Loan Sales Assistant from NBFC. I can help you find the right personal loan. What kind of loan are you interested in, or how much do you need?"
    
    async def process_message(self, session_id: str, user_message: str) -> Dict[str, Any]:
        """
        Process user message and return response.
        
        Args:
            session_id: Session identifier
            user_message: User's message
            
        Returns:
            Dict with message and loan application state
        """
        try:
            # Get session
            session = self.session_manager.get_session(session_id) if self.session_manager else None
            if not session:
                raise ValueError(f"Session not found: {session_id}")
            
            # Add user message to history
            self.session_manager.add_message(session_id, "user", user_message)
            
            # Build system prompt
            system_prompt = self._build_system_prompt(session)
            
            # Build message history
            messages = self._build_messages(session, system_prompt, user_message)
            
            # Call LLM
            try:
                response = await asyncio.wait_for(
                    asyncio.to_thread(self.llm.invoke, messages),
                    timeout=settings.GROQ_TIMEOUT
                )
                ai_message = response.content
            except asyncio.TimeoutError:
                logger.error(f"LLM timeout for session {session_id}")
                ai_message = "I apologize, but I'm taking longer than expected. Could you please try again?"
            except Exception as e:
                logger.error(f"LLM error: {e}")
                ai_message = "I apologize, but I encountered an error. Please try again."
            
            # Add AI response to history
            self.session_manager.add_message(session_id, "assistant", ai_message)
            
            # Process any business logic (KYC, credit check, etc.)
            await self._process_business_logic(session_id, user_message, ai_message)
            
            # Get updated session
            updated_session = self.session_manager.get_session(session_id)
            
            return {
                "message": ai_message,
                "loan_application": updated_session["loan_application"]
            }
            
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            raise
    
    async def stream_response(self, session_id: str, user_message: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream response chunks for WebSocket.
        
        Args:
            session_id: Session identifier
            user_message: User's message
            
        Yields:
            Response chunks
        """
        try:
            # Process message
            result = await self.process_message(session_id, user_message)
            
            # Simulate streaming by chunking the response
            message = result["message"]
            words = message.split()
            
            for i, word in enumerate(words):
                chunk = word + " "
                is_final = (i == len(words) - 1)
                
                yield {
                    "type": "message" if not is_final else "end",
                    "content": chunk,
                    "session_id": session_id,
                    "loan_application": result["loan_application"] if is_final else None
                }
                
                # Small delay for realistic streaming
                await asyncio.sleep(0.05)
                
        except Exception as e:
            logger.error(f"Error streaming response: {e}")
            yield {
                "type": "error",
                "content": str(e),
                "session_id": session_id
            }
    
    def _build_system_prompt(self, session: Dict[str, Any]) -> str:
        """Build system prompt with current state."""
        loan_app = session["loan_application"]
        
        prompt = f"""You are an Agentic AI Loan Sales Assistant for a Non-Banking Financial Company (NBFC).
Your goal is to guide users through the personal loan application process, answer questions about loan products, and facilitate loan sanction.

Current Loan Application Status:
- Applicant Name: {loan_app['applicant_name'] or 'Not provided'}
- Desired Amount: ₹{loan_app['desired_amount']:,} if loan_app['desired_amount'] else 'Not provided'}
- Loan Term: {loan_app['loan_term_months'] or 'Not provided'} months
- Purpose: {loan_app['purpose'] or 'Not provided'}
- KYC Verified: {'Yes' if loan_app['kyc_verified'] else 'No'}
- Credit Score: {loan_app['credit_score'] or 'Not assessed'}
- Credit Eligibility: {loan_app['credit_eligibility']}
- Status: {loan_app['status']}

Guide the user through these steps:
1. Gather: name, loan amount, purpose, preferred term
2. Verify KYC details
3. Evaluate creditworthiness
4. Present loan offer if eligible
5. Generate sanction letter if user accepts

Always be helpful, professional, and proactive."""
        
        return prompt
    
    def _build_messages(self, session: Dict[str, Any], system_prompt: str, user_message: str) -> list:
        """Build message list for LLM."""
        messages = [SystemMessage(content=system_prompt)]
        
        # Add recent conversation history
        for msg in session["messages"][-10:]:  # Last 10 messages
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))
        
        return messages
    
    async def _process_business_logic(self, session_id: str, user_message: str, ai_response: str):
        """
        Process business logic like KYC, credit checks, etc.
        """
        session = self.session_manager.get_session(session_id)
        loan_app = session["loan_application"]
        
        # Extract information from user message
        user_lower = user_message.lower()
        
        # Extract name
        if not loan_app["applicant_name"] and ("name is" in user_lower or "i am" in user_lower or "i'm" in user_lower):
            # Simple name extraction (in production, use NER)
            words = user_message.split()
            if "is" in words:
                idx = words.index("is") + 1
                if idx < len(words):
                    loan_app["applicant_name"] = " ".join(words[idx:idx+2]).strip(".,!?")
        
        # Extract amount
        if not loan_app["desired_amount"]:
            import re
            amount_match = re.search(r'(\d+)\s*(lakh|lakhs|thousand|k)', user_lower)
            if amount_match:
                num = int(amount_match.group(1))
                unit = amount_match.group(2)
                if 'lakh' in unit:
                    loan_app["desired_amount"] = num * 100000
                elif 'k' in unit or 'thousand' in unit:
                    loan_app["desired_amount"] = num * 1000
        
        # Extract purpose
        if not loan_app["purpose"]:
            purposes = ["home", "car", "education", "medical", "wedding", "business", "renovation"]
            for purpose in purposes:
                if purpose in user_lower:
                    loan_app["purpose"] = purpose.capitalize()
                    break
        
        # Auto KYC if name is provided
        if loan_app["applicant_name"] and not loan_app["kyc_verified"]:
            loan_app["kyc_verified"] = True
            loan_app["status"] = "credit_check_pending"
            logger.info(f"KYC verified for {loan_app['applicant_name']}")
        
        # Auto credit check if amount and KYC done
        if (loan_app["desired_amount"] and loan_app["kyc_verified"] and 
            loan_app["credit_eligibility"] == "pending"):
            
            # Mock credit score
            credit_score = random.randint(600, 850)
            loan_app["credit_score"] = credit_score
            
            if credit_score >= settings.MIN_CREDIT_SCORE and loan_app["desired_amount"] <= settings.MAX_PERSONAL_LOAN:
                loan_app["credit_eligibility"] = "eligible"
                loan_app["offered_amount"] = min(loan_app["desired_amount"], random.randint(300000, 500000))
                loan_app["offered_interest_rate"] = round(random.uniform(10.0, 12.5), 2)
                loan_app["status"] = "offer_made"
                logger.info(f"Loan offer made: ₹{loan_app['offered_amount']} at {loan_app['offered_interest_rate']}%")
            else:
                loan_app["credit_eligibility"] = "not_eligible"
                loan_app["status"] = "rejected"
                logger.info(f"Loan application rejected: credit score {credit_score}")
        
        # Generate sanction letter if user accepts
        if (loan_app["status"] == "offer_made" and 
            any(word in user_lower for word in ["yes", "accept", "agree", "proceed"])):
            
            loan_app["sanction_letter_generated"] = True
            loan_app["status"] = "sanctioned"
            loan_app["sanction_letter_url"] = f"https://mock-bank.com/sanction_letters/{loan_app['applicant_name'].replace(' ', '_')}_{random.randint(1000,9999)}.pdf"
            logger.info(f"Sanction letter generated: {loan_app['sanction_letter_url']}")
        
        # Update session
        self.session_manager.update_session(session_id, {"loan_application": loan_app})

