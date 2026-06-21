#!/usr/bin/env python3
"""
Email Cleanup Analyzer - AI-powered email categorization and cleanup suggestions.

Integrates with existing email_connectors OAuth system.
"""

import imaplib
import email
import json
import sqlite3
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
from email.header import decode_header
from email.utils import parsedate_to_datetime

# Database path
DB_PATH = Path(__file__).parent.parent.parent / "memory" / "runs_v3.db"


class EmailAnalyzer:
    """Analyzes emails and generates cleanup suggestions."""
    
    def __init__(self):
        self.db_path = DB_PATH
        
        # Category patterns for quick classification
        self.patterns = {
            'newsletter': [
                'unsubscribe', 'newsletter', 'mailing list', 'update', 'digest'
            ],
            'promotion': [
                'sale', 'deal', '% off', 'discount', 'promo', 'offer', 'limited time',
                'buy now', 'shop', 'save', 'free shipping'
            ],
            'social': [
                'facebook', 'twitter', 'linkedin', 'instagram', 'notification',
                'connection request', 'friend request', 'you have', 'new message'
            ],
            'spam': [
                'viagra', 'casino', 'lottery', 'winner', 'claim', 'inheritance',
                'congratulations', 'click here', 'act now'
            ]
        }
        
        # Known newsletter domains
        self.newsletter_domains = {
            'substack.com', 'mailchimp.com', 'sendgrid.net', 'constantcontact.com',
            'createsend.com', 'newsletter', 'bounce', 'noreply'
        }
    
    def fetch_emails_from_connector(self, connector_id: str, limit: int = 500) -> List[Dict]:
        """Fetch emails from an email connector using IMAP."""
        import hub_db
        import oauth_connector
        
        # Get connector details
        connector = hub_db.get_connector(connector_id)
        if not connector:
            raise ValueError(f"Connector {connector_id} not found")
        
        provider = connector.get('provider', 'imap')
        auth_type = connector.get('auth_type', 'password')
        email_address = connector.get('email_address', '')
        imap_host = connector.get('imap_host', '')
        imap_port = int(connector.get('imap_port', 993))
        
        # Get credentials
        if auth_type == 'oauth2':
            # Get valid OAuth token
            access_token = oauth_connector.get_valid_access_token(connector_id)
            auth_string = oauth_connector._xoauth2_string(email_address, access_token)
        else:
            # Password auth
            creds = connector.get('credentials', {})
            if isinstance(creds, str):
                creds = json.loads(creds)
            password = creds.get('password', '')
            auth_string = None
        
        # Connect to IMAP
        print(f"📧 Connecting to {imap_host}:{imap_port}...")
        
        if imap_port == 993:
            imap = imaplib.IMAP4_SSL(imap_host, imap_port)
        else:
            imap = imaplib.IMAP4(imap_host, imap_port)
        
        # Authenticate
        if auth_string:
            imap.authenticate('XOAUTH2', lambda x: auth_string.encode())
        else:
            username = connector.get('username', email_address)
            imap.login(username, password)
        
        # Select INBOX
        imap.select('INBOX')
        
        # Search for all emails (we'll limit later)
        _, message_numbers = imap.search(None, 'ALL')
        
        if not message_numbers[0]:
            print("No emails found")
            imap.logout()
            return []
        
        msg_nums = message_numbers[0].split()
        total = len(msg_nums)
        
        print(f"Found {total} emails, fetching last {limit}...")
        
        # Get last N emails (most recent)
        emails_to_fetch = msg_nums[-limit:] if len(msg_nums) > limit else msg_nums
        
        emails = []
        for i, num in enumerate(emails_to_fetch):
            if i % 50 == 0:
                print(f"Fetching {i}/{len(emails_to_fetch)}...")
            
            try:
                # Fetch email headers and body structure
                _, msg_data = imap.fetch(num, '(RFC822.HEADER BODY.PEEK[])')
                
                if not msg_data or not msg_data[0]:
                    continue
                
                # Parse email
                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)
                
                # Extract fields
                subject = self._decode_header(msg.get('Subject', ''))
                from_addr = self._decode_header(msg.get('From', ''))
                date_str = msg.get('Date', '')
                
                # Parse date
                try:
                    email_date = parsedate_to_datetime(date_str)
                except:
                    email_date = datetime.now()
                
                # Get email size
                size = len(raw_email) if raw_email else 0
                
                # Get snippet (first 200 chars of body)
                snippet = self._get_email_snippet(msg)
                
                emails.append({
                    'id': num.decode() if isinstance(num, bytes) else str(num),
                    'subject': subject,
                    'from': from_addr,
                    'date': email_date.isoformat(),
                    'size': size,
                    'snippet': snippet,
                    'has_unsubscribe': 'unsubscribe' in msg.as_string().lower()
                })
                
            except Exception as e:
                print(f"Error fetching email {num}: {e}")
                continue
        
        imap.logout()
        print(f"✅ Fetched {len(emails)} emails")
        
        return emails
    
    def _decode_header(self, header: str) -> str:
        """Decode email header."""
        if not header:
            return ''
        
        decoded = decode_header(header)
        parts = []
        
        for content, encoding in decoded:
            if isinstance(content, bytes):
                try:
                    parts.append(content.decode(encoding or 'utf-8', errors='replace'))
                except:
                    parts.append(content.decode('utf-8', errors='replace'))
            else:
                parts.append(content)
        
        return ''.join(parts)
    
    def _get_email_snippet(self, msg) -> str:
        """Extract text snippet from email."""
        body = ''
        
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == 'text/plain':
                    try:
                        body = part.get_payload(decode=True).decode('utf-8', errors='replace')
                        break
                    except:
                        pass
        else:
            try:
                body = msg.get_payload(decode=True).decode('utf-8', errors='replace')
            except:
                body = str(msg.get_payload())
        
        # Return first 200 chars
        return body[:200].replace('\n', ' ').strip()
    
    def categorize_email(self, email_data: Dict) -> tuple[str, float, str]:
        """
        Categorize an email and return (category, confidence, reason).
        
        Categories: newsletter, promotion, social, old_thread, spam, important
        """
        subject = email_data.get('subject', '').lower()
        from_addr = email_data.get('from', '').lower()
        snippet = email_data.get('snippet', '').lower()
        date_str = email_data.get('date', '')
        has_unsubscribe = email_data.get('has_unsubscribe', False)
        
        # Parse date
        try:
            email_date = datetime.fromisoformat(date_str)
            age_days = (datetime.now() - email_date).days
        except:
            age_days = 0
        
        # Extract domain from from_addr
        try:
            domain = from_addr.split('@')[-1].split('>')[0].strip()
        except:
            domain = ''
        
        confidence = 0.5
        category = 'important'  # Default
        reason = ''
        
        # Check for old threads (6+ months)
        if age_days > 180:
            confidence = 0.8
            category = 'old_thread'
            reason = f"Email is {age_days} days old with no recent activity"
            return category, confidence, reason
        
        # Check for newsletters
        if has_unsubscribe:
            confidence += 0.3
        
        if any(kw in subject or kw in snippet or kw in from_addr for kw in self.patterns['newsletter']):
            confidence += 0.2
            category = 'newsletter'
            reason = f"Newsletter from {from_addr[:50]}"
        
        if any(nd in domain for nd in self.newsletter_domains):
            confidence += 0.3
            category = 'newsletter'
            reason = f"Known newsletter domain: {domain}"
        
        # Check for promotions
        if any(kw in subject for kw in self.patterns['promotion']):
            confidence = max(confidence, 0.7)
            category = 'promotion'
            reason = f"Promotional content: '{subject[:60]}...'"
        
        # Check for social
        if any(kw in subject or kw in from_addr for kw in self.patterns['social']):
            confidence = max(confidence, 0.75)
            category = 'social'
            reason = f"Social media notification from {from_addr[:50]}"
        
        # Check for spam
        if any(kw in subject or kw in snippet for kw in self.patterns['spam']):
            confidence = 0.9
            category = 'spam'
            reason = "Spam indicators detected"
        
        # Cap confidence
        confidence = min(confidence, 1.0)
        
        # If confidence too low, mark as important
        if confidence < 0.6:
            category = 'important'
            reason = "Low confidence - requires manual review"
        
        return category, confidence, reason
    
    def analyze_inbox(self, connector_id: str, limit: int = 500) -> Dict:
        """
        Analyze inbox and generate cleanup plan.
        
        Returns cleanup plan with categorized emails.
        """
        print(f"\n🔍 Analyzing inbox for connector {connector_id}...")
        
        # Fetch emails
        emails = self.fetch_emails_from_connector(connector_id, limit)
        
        if not emails:
            return {
                'connector_id': connector_id,
                'total_emails': 0,
                'categories': {},
                'summary': {
                    'total_suggested': 0,
                    'estimated_space_mb': 0
                }
            }
        
        # Categorize each email
        categorized = {
            'newsletter': [],
            'promotion': [],
            'social': [],
            'old_thread': [],
            'spam': [],
            'important': []
        }
        
        print(f"📊 Categorizing {len(emails)} emails...")
        
        for email_data in emails:
            category, confidence, reason = self.categorize_email(email_data)
            
            # Only suggest cleanup for high-confidence non-important emails
            if category != 'important' and confidence >= 0.7:
                categorized[category].append({
                    'email_id': email_data['id'],
                    'subject': email_data['subject'],
                    'from': email_data['from'],
                    'date': email_data['date'],
                    'size': email_data['size'],
                    'confidence': confidence,
                    'reason': reason
                })
        
        # Calculate statistics
        total_suggested = sum(len(items) for cat, items in categorized.items() if cat != 'important')
        total_size_bytes = sum(
            item['size'] 
            for items in categorized.values() 
            for item in items
        )
        
        result = {
            'connector_id': connector_id,
            'total_emails': len(emails),
            'categories': categorized,
            'summary': {
                'total_suggested': total_suggested,
                'estimated_space_mb': round(total_size_bytes / (1024 * 1024), 2),
                'breakdown': {
                    cat: len(items) 
                    for cat, items in categorized.items()
                    if cat != 'important' and items
                }
            }
        }
        
        print(f"\n✅ Analysis complete:")
        print(f"   Total emails: {len(emails)}")
        print(f"   Suggested for cleanup: {total_suggested}")
        print(f"   Estimated space: {result['summary']['estimated_space_mb']} MB")
        print(f"   Breakdown: {result['summary']['breakdown']}")
        
        return result
    
    def save_cleanup_plan(self, analysis: Dict) -> str:
        """Save cleanup plan to database."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        try:
            plan_id = secrets.token_urlsafe(16)
            now = datetime.utcnow().isoformat()
            
            # Create cleanup plan
            cursor.execute("""
                INSERT INTO email_cleanup_plans (
                    id, account_id, status, total_emails, 
                    suggested_cleanup_count, estimated_space_mb, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                plan_id,
                analysis['connector_id'],
                'pending',
                analysis['total_emails'],
                analysis['summary']['total_suggested'],
                int(analysis['summary']['estimated_space_mb']),
                now
            ))
            
            # Create cleanup items
            for category, items in analysis['categories'].items():
                if category == 'important':
                    continue
                
                for item in items:
                    item_id = secrets.token_urlsafe(12)
                    cursor.execute("""
                        INSERT INTO email_cleanup_items (
                            id, plan_id, email_id, category, subject,
                            from_address, email_date, size_bytes,
                            confidence, reason, action
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        item_id, plan_id, item['email_id'], category,
                        item['subject'], item['from'], item['date'],
                        item['size'], item['confidence'], item['reason'],
                        'archive'  # Default action
                    ))
            
            conn.commit()
            print(f"✅ Saved cleanup plan: {plan_id}")
            
            return plan_id
            
        finally:
            conn.close()
    
    def get_cleanup_plan(self, plan_id: str) -> Optional[Dict]:
        """Get cleanup plan by ID."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            # Get plan
            cursor.execute("SELECT * FROM email_cleanup_plans WHERE id = ?", (plan_id,))
            plan_row = cursor.fetchone()
            
            if not plan_row:
                return None
            
            plan = dict(plan_row)
            
            # Get items grouped by category
            cursor.execute("""
                SELECT * FROM email_cleanup_items 
                WHERE plan_id = ?
                ORDER BY category, confidence DESC
            """, (plan_id,))
            
            items = [dict(row) for row in cursor.fetchall()]
            
            # Group by category
            categories = {}
            for item in items:
                cat = item['category']
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(item)
            
            plan['categories'] = categories
            plan['items'] = items
            
            return plan
            
        finally:
            conn.close()


if __name__ == "__main__":
    # Test analyzer
    analyzer = EmailAnalyzer()
    
    # List available connectors
    import hub_db
    connectors = hub_db.list_connectors()
    
    print(f"📧 Available email connectors: {len(connectors)}")
    for conn in connectors:
        print(f"  - {conn['label']} ({conn['email_address']}) - {conn['provider']}")
    
    if connectors:
        # Analyze first connector
        first_conn = connectors[0]
        print(f"\n🔍 Analyzing: {first_conn['label']}...")
        
        try:
            analysis = analyzer.analyze_inbox(first_conn['id'], limit=100)
            plan_id = analyzer.save_cleanup_plan(analysis)
            
            print(f"\n✅ Cleanup plan saved: {plan_id}")
            print(f"   Run: SELECT * FROM email_cleanup_plans WHERE id = '{plan_id}'")
            
        except Exception as e:
            print(f"❌ Analysis failed: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("No email connectors found. Add one first!")
