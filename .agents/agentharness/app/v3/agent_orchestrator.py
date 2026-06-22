"""
Agent Collaboration Orchestrator for ArchonHub.

Enables agents to work together on complex tasks:
- Analyzes user query to determine which agents are needed
- Sends requests to agents in parallel or sequence
- Collects and synthesizes responses
- Tracks conversation state
"""

import asyncio
import json
import logging
import sqlite3
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

# Setup paths
HERE = Path(__file__).parent
HARNESS = HERE.parent.parent
DB_PATH = HARNESS / "memory" / "runs_v3.db"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Orchestrates multi-agent collaborations."""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
    
    def get_agent_capabilities(self, agent_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get agent capabilities."""
        
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        
        try:
            cursor = conn.cursor()
            
            if agent_name:
                cursor.execute("""
                    SELECT * FROM agent_capabilities WHERE agent_name = ? AND active = 1
                """, (agent_name,))
            else:
                cursor.execute("""
                    SELECT * FROM agent_capabilities WHERE active = 1
                """)
            
            agents = []
            for row in cursor.fetchall():
                agent = dict(row)
                agent['capabilities'] = json.loads(agent['capabilities_json'])
                agent['dependencies'] = json.loads(agent.get('dependencies') or '[]')
                agents.append(agent)
            
            return agents
        
        finally:
            conn.close()
    
    def analyze_query_for_agents(self, query: str) -> List[str]:
        """Analyze query to determine which agents are needed."""
        
        # Simple keyword-based routing (can be enhanced with LLM)
        query_lower = query.lower()
        agents_needed = []
        
        # Markets agent keywords
        if any(word in query_lower for word in [
            'stock', 'market', 'portfolio', 'invest', 'price', 'ticker',
            'nasdaq', 'dow', 'spy', 'trade', 'dividend'
        ]):
            agents_needed.append('markets')
        
        # Finance agent keywords
        if any(word in query_lower for word in [
            'budget', 'spending', 'expense', 'income', 'balance',
            'financial', 'accounting', 'cash flow', 'revenue'
        ]):
            agents_needed.append('finance')
        
        # Legal agent keywords
        if any(word in query_lower for word in [
            'contract', 'legal', 'compliance', 'terms', 'agreement',
            'liability', 'intellectual property', 'trademark'
        ]):
            agents_needed.append('legal')
        
        # Research agent keywords
        if any(word in query_lower for word in [
            'research', 'search', 'find information', 'lookup',
            'investigate', 'study', 'analyze data'
        ]):
            agents_needed.append('research')
        
        # Grants agent keywords
        if any(word in query_lower for word in [
            'grant', 'funding', 'proposal', 'rfp', 'foundation',
            'donation', 'nonprofit', 'charity'
        ]):
            agents_needed.append('grants')
        
        # Ministry agent keywords
        if any(word in query_lower for word in [
            'sermon', 'biblical', 'theology', 'scripture', 'ministry',
            'church', 'pastor', 'spiritual', 'gospel'
        ]):
            agents_needed.append('ministry')
        
        # Default to Inez if no specific agent
        if not agents_needed:
            agents_needed.append('inez')
        
        logger.info(f"Query analysis: {len(agents_needed)} agents needed: {agents_needed}")
        
        return list(set(agents_needed))  # Deduplicate
    
    async def create_conversation(
        self,
        user_id: str,
        goal: str,
        participant_agents: List[str]
    ) -> str:
        """Create a new agent conversation."""
        
        conversation_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(str(self.db_path))
        try:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO agent_conversations (
                    conversation_id, user_id, initiator_agent, participant_agents,
                    goal, status, created_at, message_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 0)
            """, (
                conversation_id,
                user_id,
                participant_agents[0] if participant_agents else 'inez',
                json.dumps(participant_agents),
                goal,
                'active',
                datetime.utcnow().isoformat()
            ))
            
            conn.commit()
            logger.info(f"Created conversation {conversation_id} with agents: {participant_agents}")
            
            return conversation_id
        
        finally:
            conn.close()
    
    async def send_message(
        self,
        conversation_id: str,
        sender_agent: str,
        recipient_agent: str,
        message_type: str,
        payload: Dict[str, Any],
        timeout_seconds: int = 30
    ) -> str:
        """Send a message between agents."""
        
        message_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(str(self.db_path))
        try:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO agent_messages (
                    message_id, conversation_id, sender_agent, recipient_agent,
                    message_type, payload_json, status, created_at, timeout_seconds
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                message_id,
                conversation_id,
                sender_agent,
                recipient_agent,
                message_type,
                json.dumps(payload),
                'pending',
                datetime.utcnow().isoformat(),
                timeout_seconds
            ))
            
            # Update conversation message count
            cursor.execute("""
                UPDATE agent_conversations
                SET message_count = message_count + 1
                WHERE conversation_id = ?
            """, (conversation_id,))
            
            conn.commit()
            logger.info(f"Sent {message_type} from {sender_agent} to {recipient_agent}: {message_id}")
            
            return message_id
        
        finally:
            conn.close()
    
    async def process_message(self, message_id: str) -> Dict[str, Any]:
        """Process an agent message (simulated - would integrate with actual agents)."""
        
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        
        try:
            cursor = conn.cursor()
            
            # Get message
            cursor.execute("""
                SELECT * FROM agent_messages WHERE message_id = ?
            """, (message_id,))
            
            message = dict(cursor.fetchone())
            payload = json.loads(message['payload_json'])
            
            # Update status to processing
            cursor.execute("""
                UPDATE agent_messages
                SET status = 'processing', delivered_at = ?
                WHERE message_id = ?
            """, (datetime.utcnow().isoformat(), message_id))
            conn.commit()
            
            # Simulate agent processing
            logger.info(f"Processing message for {message['recipient_agent']}: {payload.get('query', 'N/A')}")
            
            # This is where actual agent execution would happen
            # For now, return a simulated response
            response_payload = {
                "status": "success",
                "agent": message['recipient_agent'],
                "query": payload.get('query'),
                "response": f"{message['recipient_agent'].title()} agent processed the request.",
                "confidence": 0.85,
                "metadata": {
                    "processing_time_ms": 150,
                    "sources_consulted": 3
                }
            }
            
            # Update status to completed
            cursor.execute("""
                UPDATE agent_messages
                SET status = 'completed', completed_at = ?
                WHERE message_id = ?
            """, (datetime.utcnow().isoformat(), message_id))
            conn.commit()
            
            logger.info(f"Completed message {message_id}")
            
            return response_payload
        
        finally:
            conn.close()
    
    async def orchestrate_collaboration(
        self,
        user_id: str,
        query: str,
        explicit_agents: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Orchestrate a multi-agent collaboration."""
        
        logger.info(f"Starting orchestration for query: {query[:100]}...")
        
        # Determine which agents to involve
        if explicit_agents:
            agents_needed = explicit_agents
        else:
            agents_needed = self.analyze_query_for_agents(query)
        
        # Create conversation
        conversation_id = await self.create_conversation(
            user_id=user_id,
            goal=query,
            participant_agents=agents_needed
        )
        
        # Send requests to agents in parallel
        message_ids = []
        for agent in agents_needed:
            message_id = await self.send_message(
                conversation_id=conversation_id,
                sender_agent='inez',
                recipient_agent=agent,
                message_type='request',
                payload={
                    "query": query,
                    "context": "user_request",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            message_ids.append(message_id)
        
        # Process messages in parallel
        responses = []
        for message_id in message_ids:
            try:
                response = await self.process_message(message_id)
                responses.append(response)
            except Exception as e:
                logger.error(f"Error processing message {message_id}: {e}")
                responses.append({
                    "status": "error",
                    "error": str(e)
                })
        
        # Synthesize final response
        synthesis = self._synthesize_responses(query, agents_needed, responses)
        
        # Mark conversation as completed
        conn = sqlite3.connect(str(self.db_path))
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE agent_conversations
                SET status = 'completed', completed_at = ?, result_json = ?
                WHERE conversation_id = ?
            """, (
                datetime.utcnow().isoformat(),
                json.dumps(synthesis),
                conversation_id
            ))
            conn.commit()
        finally:
            conn.close()
        
        logger.info(f"Orchestration complete: {conversation_id}")
        
        return {
            "conversation_id": conversation_id,
            "agents_involved": agents_needed,
            "message_count": len(message_ids),
            "responses": responses,
            "synthesis": synthesis
        }
    
    def _synthesize_responses(
        self,
        query: str,
        agents: List[str],
        responses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Synthesize multiple agent responses into a cohesive answer."""
        
        # Simple synthesis - concatenate responses
        # In production, this would use an LLM to intelligently combine insights
        
        synthesis_parts = []
        for agent, response in zip(agents, responses):
            if response.get('status') == 'success':
                synthesis_parts.append(f"**{agent.title()} Agent:** {response.get('response', 'N/A')}")
        
        return {
            "synthesized_response": "\n\n".join(synthesis_parts),
            "agents_consulted": len(agents),
            "successful_responses": sum(1 for r in responses if r.get('status') == 'success'),
            "confidence": sum(r.get('confidence', 0) for r in responses if r.get('status') == 'success') / max(len(responses), 1)
        }
    
    def get_conversation_history(self, conversation_id: str) -> Dict[str, Any]:
        """Get full conversation history."""
        
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        
        try:
            cursor = conn.cursor()
            
            # Get conversation
            cursor.execute("""
                SELECT * FROM agent_conversations WHERE conversation_id = ?
            """, (conversation_id,))
            
            conv = dict(cursor.fetchone())
            conv['participant_agents'] = json.loads(conv['participant_agents'])
            if conv.get('result_json'):
                conv['result'] = json.loads(conv['result_json'])
            
            # Get messages
            cursor.execute("""
                SELECT * FROM agent_messages
                WHERE conversation_id = ?
                ORDER BY created_at
            """, (conversation_id,))
            
            messages = []
            for row in cursor.fetchall():
                msg = dict(row)
                msg['payload'] = json.loads(msg['payload_json'])
                messages.append(msg)
            
            conv['messages'] = messages
            
            return conv
        
        finally:
            conn.close()


async def main():
    """Test agent orchestration."""
    
    orchestrator = AgentOrchestrator(DB_PATH)
    
    # Example 1: Investment decision (Markets + Finance + Legal)
    print("\n" + "="*80)
    print("Example 1: Investment Decision")
    print("="*80)
    
    result = await orchestrator.orchestrate_collaboration(
        user_id="default_user",
        query="Should I invest $10,000 in NVDA stock? Analyze market conditions, check my available balance, and review any legal restrictions."
    )
    
    print(f"\nConversation ID: {result['conversation_id']}")
    print(f"Agents Involved: {', '.join(result['agents_involved'])}")
    print(f"Messages Exchanged: {result['message_count']}")
    print(f"\nSynthesized Response:")
    print(result['synthesis']['synthesized_response'])
    print(f"\nConfidence: {result['synthesis']['confidence']:.0%}")
    
    # Example 2: Grant proposal
    print("\n\n" + "="*80)
    print("Example 2: Grant Proposal")
    print("="*80)
    
    result2 = await orchestrator.orchestrate_collaboration(
        user_id="default_user",
        query="Find grant opportunities for youth sports programs and help draft a proposal for $50k funding."
    )
    
    print(f"\nConversation ID: {result2['conversation_id']}")
    print(f"Agents Involved: {', '.join(result2['agents_involved'])}")
    print(f"Messages Exchanged: {result2['message_count']}")
    print(f"\nSynthesized Response:")
    print(result2['synthesis']['synthesized_response'])


if __name__ == "__main__":
    asyncio.run(main())
