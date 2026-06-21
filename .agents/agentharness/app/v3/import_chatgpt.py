#!/usr/bin/env python3
"""
Import ChatGPT conversation history and custom instructions into ArchonHub global memory.

This script parses ChatGPT export JSON files and extracts:
- User preferences and communication patterns
- Project context and technical details
- Ministry/theological interests (for SoulSpeak agent)
- People, deadlines, and workflows
- Custom instructions

Usage:
    python3 import_chatgpt.py /path/to/chatgpt_export.json
"""

import json
import sqlite3
import sys
import uuid
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set

# Path to the database
DB_PATH = Path(__file__).parent.parent.parent / "memory" / "runs_v3.db"


class ChatGPTImporter:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.conn = sqlite3.connect(str(db_path))
        self.conn.row_factory = sqlite3.Row
        self.extracted_facts: List[Dict] = []
        
    def import_export_file(self, json_path: Path):
        """Import ChatGPT export JSON file."""
        print(f"📂 Reading ChatGPT export: {json_path}")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # ChatGPT export structure can vary. Handle common formats:
        if isinstance(data, list):
            # List of conversations
            self._process_conversations(data)
        elif isinstance(data, dict):
            if 'conversations' in data:
                self._process_conversations(data['conversations'])
            elif 'custom_instructions' in data:
                self._process_custom_instructions(data['custom_instructions'])
            elif 'messages' in data:
                # Single conversation
                self._process_conversation(data)
        
        # Deduplicate and score facts
        self._deduplicate_facts()
        
        # Save to database
        self._save_to_database()
        
        print(f"\n✅ Import complete!")
        print(f"📊 Imported {len(self.extracted_facts)} facts")
        
    def _process_conversations(self, conversations: List[Dict]):
        """Process list of conversations."""
        print(f"📊 Processing {len(conversations)} conversations...")
        
        ministry_keywords = {'sermon', 'bible', 'biblical', 'theology', 'spiritual', 'scripture', 'ministry', 'church', 'prayer', 'soul', 'soulspeak'}
        tech_keywords = {'code', 'programming', 'api', 'database', 'wordpress', 'plugin', 'development', 'typescript', 'python', 'react'}
        markets_keywords = {'stock', 'market', 'portfolio', 'investment', 'tesla', 'nvda', 'meta', 'trading'}
        
        for i, conv in enumerate(conversations):
            if i % 10 == 0:
                print(f"  Processing conversation {i+1}/{len(conversations)}...")
            
            title = conv.get('title', '').lower()
            messages = conv.get('messages', conv.get('mapping', {}))
            
            # Detect conversation topics
            is_ministry = any(kw in title for kw in ministry_keywords)
            is_tech = any(kw in title for kw in tech_keywords)
            is_markets = any(kw in title for kw in markets_keywords)
            
            # Extract from messages
            if isinstance(messages, dict):
                # mapping format
                for msg_id, msg_data in messages.items():
                    msg = msg_data.get('message', {})
                    self._extract_from_message(msg, is_ministry, is_tech, is_markets)
            elif isinstance(messages, list):
                # list format
                for msg in messages:
                    self._extract_from_message(msg, is_ministry, is_tech, is_markets)
    
    def _process_conversation(self, conversation: Dict):
        """Process single conversation."""
        messages = conversation.get('messages', [])
        for msg in messages:
            self._extract_from_message(msg, False, False, False)
    
    def _process_custom_instructions(self, instructions: Dict):
        """Process ChatGPT custom instructions."""
        print("📝 Processing custom instructions...")
        
        about_user = instructions.get('about_user', '')
        how_to_respond = instructions.get('how_to_respond', '')
        
        if about_user:
            # Extract key facts from "About you" section
            self._extract_facts_from_text(about_user, 'preferences', importance=10, source='chatgpt_custom_instructions')
        
        if how_to_respond:
            # Extract communication preferences
            self._extract_facts_from_text(how_to_respond, 'preferences', importance=9, source='chatgpt_custom_instructions')
    
    def _extract_from_message(self, message: Dict, is_ministry: bool, is_tech: bool, is_markets: bool):
        """Extract facts from a single message."""
        role = message.get('role', message.get('author', {}).get('role', ''))
        content = message.get('content', {})
        
        if isinstance(content, dict):
            parts = content.get('parts', [])
            text = ' '.join(str(p) for p in parts if isinstance(p, str))
        elif isinstance(content, str):
            text = content
        else:
            return
        
        if not text or role != 'user':
            return
        
        # Detect topic-specific content
        if is_ministry or any(kw in text.lower() for kw in ['sermon', 'bible', 'theology', 'spiritual', 'scripture']):
            self._extract_ministry_context(text)
        
        if is_tech or any(kw in text.lower() for kw in ['code', 'api', 'wordpress', 'development']):
            self._extract_tech_context(text)
        
        if is_markets or any(kw in text.lower() for kw in ['stock', 'portfolio', 'investment', 'market']):
            self._extract_markets_context(text)
        
        # Extract general preferences
        self._extract_preferences(text)
    
    def _extract_ministry_context(self, text: str):
        """Extract ministry and theological context."""
        # Look for sermon styles, theological interests
        patterns = [
            (r'(exploratory|contemplative|questioning|narrative|expository)\s+(style|approach|sermon)', 'ministry_style'),
            (r'(biblical|theological)\s+interest in\s+(.+?)[\.\,]', 'ministry_interest'),
            (r'sermon\s+(series|topic|theme):\s*(.+?)[\.\,]', 'ministry_topic'),
        ]
        
        for pattern, key_prefix in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                value = ' '.join(match) if isinstance(match, tuple) else match
                self.extracted_facts.append({
                    'category': 'ministry',
                    'key': f'{key_prefix}_{uuid.uuid4().hex[:8]}',
                    'value': value.strip(),
                    'source': 'chatgpt_import',
                    'confidence': 0.8,
                    'importance': 8
                })
    
    def _extract_tech_context(self, text: str):
        """Extract technical project context."""
        # Look for project names, technologies
        patterns = [
            (r'(XFTC|PBS\s+Event\s+Commerce|ProfilePress|WordPress\s+plugin)', 'project_name'),
            (r'(TypeScript|Python|React|Vue|PHP|WordPress)\s+(.{0,30})', 'tech_stack'),
        ]
        
        for pattern, key_prefix in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                value = ' '.join(match) if isinstance(match, tuple) else match
                self.extracted_facts.append({
                    'category': 'technical',
                    'key': f'{key_prefix}_{uuid.uuid4().hex[:8]}',
                    'value': value.strip()[:200],  # Truncate long values
                    'source': 'chatgpt_import',
                    'confidence': 0.7,
                    'importance': 7
                })
    
    def _extract_markets_context(self, text: str):
        """Extract markets and investment context."""
        # Look for ticker symbols, investment strategies
        tickers = re.findall(r'\b(TSLA|NVDA|META|AAPL|GOOGL|MSFT|AMZN)\b', text, re.IGNORECASE)
        if tickers:
            unique_tickers = set(t.upper() for t in tickers)
            self.extracted_facts.append({
                'category': 'markets',
                'key': 'tracked_tickers',
                'value': ', '.join(sorted(unique_tickers)),
                'source': 'chatgpt_import',
                'confidence': 0.9,
                'importance': 8
            })
    
    def _extract_preferences(self, text: str):
        """Extract communication and workflow preferences."""
        lower_text = text.lower()
        
        # Communication style indicators
        if 'concise' in lower_text or 'brief' in lower_text:
            self.extracted_facts.append({
                'category': 'preferences',
                'key': 'response_style',
                'value': 'Prefers concise, brief responses',
                'source': 'chatgpt_import',
                'confidence': 0.8,
                'importance': 9
            })
        
        if 'detailed' in lower_text or 'comprehensive' in lower_text:
            self.extracted_facts.append({
                'category': 'preferences',
                'key': 'response_style',
                'value': 'Sometimes prefers detailed, comprehensive responses',
                'source': 'chatgpt_import',
                'confidence': 0.7,
                'importance': 7
            })
    
    def _extract_facts_from_text(self, text: str, category: str, importance: int, source: str):
        """Extract structured facts from free-form text."""
        # Split by sentences/bullets
        sentences = re.split(r'[.\n•\-]', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 20 or len(sentence) > 300:
                continue
            
            self.extracted_facts.append({
                'category': category,
                'key': f'{category}_{uuid.uuid4().hex[:8]}',
                'value': sentence,
                'source': source,
                'confidence': 0.9,
                'importance': importance
            })
    
    def _deduplicate_facts(self):
        """Remove duplicate and low-quality facts."""
        seen_values: Set[str] = set()
        unique_facts = []
        
        # Sort by importance and confidence
        sorted_facts = sorted(
            self.extracted_facts,
            key=lambda x: (x.get('importance', 5), x.get('confidence', 0.5)),
            reverse=True
        )
        
        for fact in sorted_facts:
            value_lower = fact['value'].lower()
            if value_lower not in seen_values:
                seen_values.add(value_lower)
                unique_facts.append(fact)
        
        self.extracted_facts = unique_facts
        print(f"📊 Deduplicated to {len(unique_facts)} unique facts")
    
    def _save_to_database(self):
        """Save extracted facts to database."""
        now = datetime.utcnow().isoformat() + 'Z'
        cursor = self.conn.cursor()
        
        saved_count = 0
        for fact in self.extracted_facts:
            fact_id = str(uuid.uuid4())
            
            try:
                cursor.execute("""
                    INSERT INTO global_memory 
                    (id, category, key, value, source, confidence, importance, last_verified, usage_count, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    fact_id,
                    fact['category'],
                    fact['key'],
                    fact['value'],
                    fact['source'],
                    fact.get('confidence', 0.7),
                    fact.get('importance', 5),
                    now,
                    0,
                    now,
                    now
                ))
                saved_count += 1
            except sqlite3.IntegrityError:
                # Duplicate key, update existing
                cursor.execute("""
                    UPDATE global_memory
                    SET value = ?,
                        confidence = MAX(confidence, ?),
                        importance = MAX(importance, ?),
                        usage_count = usage_count + 1,
                        updated_at = ?
                    WHERE category = ? AND key = ?
                """, (
                    fact['value'],
                    fact.get('confidence', 0.7),
                    fact.get('importance', 5),
                    now,
                    fact['category'],
                    fact['key']
                ))
        
        self.conn.commit()
        print(f"💾 Saved {saved_count} new facts to database")
    
    def close(self):
        """Close database connection."""
        self.conn.close()


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 import_chatgpt.py <path_to_chatgpt_export.json>")
        print("\nHow to get your ChatGPT export:")
        print("1. Go to https://chatgpt.com")
        print("2. Click your profile → Settings → Data Controls")
        print("3. Click 'Export data'")
        print("4. Wait for email with download link")
        print("5. Download and extract the ZIP file")
        print("6. Run: python3 import_chatgpt.py conversations.json")
        sys.exit(1)
    
    json_path = Path(sys.argv[1])
    
    if not json_path.exists():
        print(f"❌ File not found: {json_path}")
        sys.exit(1)
    
    importer = ChatGPTImporter(DB_PATH)
    try:
        importer.import_export_file(json_path)
    finally:
        importer.close()


if __name__ == "__main__":
    main()
