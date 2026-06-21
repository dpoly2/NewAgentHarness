# Web Search Integration for ArchonHub — Setup Guide

**Status:** ✅ Core infrastructure complete  
**Phase:** Database ready, API client built, awaiting SerpAPI API key

---

## 📦 What's Been Implemented

### 1. **Web Search Module** (`web_search.py`)
- ✅ SerpAPI API client
- ✅ Search result parsing & formatting
- ✅ Citation tracking (SearchSource, SearchResult classes)
- ✅ Query analyzer (determines when search is needed)
- ✅ Citation formatter (adds [1][2] inline citations)

### 2. **Database Schema** (migrations applied)
- ✅ Added `has_citations` column to messages table
- ✅ Added `citations` JSON column (stores sources)
- ✅ Added `search_query` column (original query if web search used)

### 3. **Ready to Use**
- ✅ All dependencies installed (bcrypt, passlib)
- ✅ Database schema migrated
- ✅ Test script included in web_search.py

---

## 🔑 Getting Your SerpAPI API Key

### Step 1: Sign Up for SerpAPI API
1. Go to: https://brave.com/search/api/
2. Click "Get Started" or "Sign Up"
3. Choose a plan:
   - **Free Trial**: 2,000 queries/month (perfect for testing)
   - **Basic**: $5/month for 1,000 queries ($5 per 1,000 after)
   - **Pro**: Custom pricing for high volume

### Step 2: Get Your API Key
1. After signing up, go to your dashboard
2. Copy your **Subscription Token** (API key)
3. Keep it secret! This is your personal key.

### Step 3: Add to Environment
```bash
# Option A: Add to .env file (recommended)
cd /Users/polysqa/Documents/GitHub/NewAgentHarness/.agents/agentharness
echo "SERPAPI_API_KEY=your_key_here" >> .env

# Option B: Export temporarily (for testing)
export SERPAPI_API_KEY="your_key_here"
```

---

## 🧪 Testing the Integration

### Quick Test
```bash
cd /Users/polysqa/Documents/GitHub/NewAgentHarness/.agents/agentharness/app/v3

# Make sure your API key is set
export SERPAPI_API_KEY="your_key_here"

# Run the test script
python3 web_search.py
```

**Expected Output:**
```
🌐 Searching SerpAPI: 'Tesla stock price today' (limit=3)
✅ Found 3 results for 'Tesla stock price today'

Query: Tesla stock price today
Found 3 results:

[1] Tesla Stock Price Today - TSLA Quote
    Tesla Inc. (TSLA) stock is trading at $242.50, down 3.2% today...
    https://finance.yahoo.com/quote/TSLA

[2] TSLA - Tesla Inc Stock Quote
    Real-time price and analysis for Tesla stock...
    https://www.bloomberg.com/quote/TSLA:US

[3] Tesla Stock News and Updates
    Latest news and market analysis for Tesla shares...
    https://www.reuters.com/companies/TSLA.O

Search analysis:
  'Tesla stock today' -> True
  'What is 2+2?' -> False
  'Latest news about AI' -> True
```

---

## 🚀 Next Steps: Integrating with Inez

The infrastructure is ready! Here's what needs to be done next:

### Phase 1: Basic Integration (Week 1)
1. **Modify Inez message handler** to:
   - Analyze incoming query with `SearchAnalyzer.should_search()`
   - If needed, call `SerpAPISearchClient.search()`
   - Format search results as LLM context
   - Generate response with citations
   - Save citations to database

2. **Update iOS app** to:
   - Display "🌐 Searching..." indicator
   - Show clickable citation numbers [1][2]
   - Add "View Sources" modal

### Phase 2: Advanced Features (Week 2-3)
1. **Focus Modes**
   - Markets focus → financial sources only
   - Academic focus → scholarly papers
   - Code focus → GitHub, Stack Overflow

2. **Citation UI**
   - Tap [1] → show source modal
   - "View All Sources" button
   - Source badges (🌐 web, 📚 academic, 💻 code)

3. **Follow-Up Suggestions**
   - Generate 3-5 related questions after each response

---

## 💰 Cost Estimate

### Personal Use (Monthly)
- **500 searches/month**: $2.50
- **1,000 searches/month**: $5.00
- **2,000 searches/month**: $10.00
- **5,000 searches/month**: $25.00

### Your likely usage:
- ~50 searches/day = 1,500/month = **$7.50/month**
- **Very affordable** for the value added!

---

## 📊 Query Analysis Examples

The `SearchAnalyzer` automatically detects queries that need web search:

### ✅ Will Search (Fresh Data Needed)
- "What's the latest news about XFTC?"
- "Tesla stock price today"
- "Current weather in Austin"
- "How much does a WordPress plugin cost?"
- "What happened with the PBS foundation this week?"
- "Find grants for youth athletics"
- "Compare Austin vs Dallas real estate"

### ❌ Won't Search (LLM Can Answer)
- "What is 2+2?"
- "Explain Python decorators"
- "Write a function to sort an array"
- "What's a good name for my app?"
- "How do I feel better?"

---

## 🔧 Configuration Options

### Search Settings
```python
# In web_search.py, you can customize:

# Number of results per query
search_result = client.search(query, num_results=5)  # Default: 5, Max: 20

# Search language
search_result = client.search(query, search_lang="en")  # en, es, fr, de, etc.

# Country-specific results
search_result = client.search(query, country="us")  # us, uk, ca, etc.
```

### Query Analysis Tuning
```python
# Add custom patterns to SearchAnalyzer.SEARCH_PATTERNS
# Add custom topics to SearchAnalyzer.FRESH_DATA_TOPICS
```

---

## 📝 Citation Format

### In LLM Prompt:
```
Web search results for: "Tesla stock price"

[1] Tesla Stock Quote - Yahoo Finance
    Tesla Inc. (TSLA) is trading at $242...
    Source: https://finance.yahoo.com/quote/TSLA

[2] TSLA Stock Analysis - Bloomberg
    Recent analysis shows Tesla's valuation...
    Source: https://www.bloomberg.com/quote/TSLA:US

Instructions:
- Use these sources to provide accurate info
- Cite sources inline using [cite:N]
- If sources don't answer fully, supplement with knowledge
```

### In Response:
```
Tesla (TSLA) is currently trading at $242.50, down 3.2% today [cite:1].
Analysts at Bloomberg note that the decline follows disappointing Q2
delivery numbers announced this morning [cite:2].

**Sources:**
[1] Tesla Stock Quote - Yahoo Finance
    https://finance.yahoo.com/quote/TSLA
[2] TSLA Stock Analysis - Bloomberg
    https://www.bloomberg.com/quote/TSLA:US
```

---

## 🐛 Troubleshooting

### "Invalid API key" Error
```bash
# Check your key is set
echo $SERPAPI_API_KEY

# If empty, export it
export SERPAPI_API_KEY="your_key_here"

# Or add to .env permanently
echo "SERPAPI_API_KEY=your_key_here" >> .env
```

### "Rate limit exceeded" Error
- You've hit your monthly quota
- Wait until next billing cycle OR upgrade plan
- Check usage at: https://brave.com/search/api/dashboard

### "requests library not available"
```bash
pip3 install requests
```

---

## 📚 API Documentation

### SerpAPISearchClient Methods
```python
client = SerpAPISearchClient(api_key="your_key")

# Basic search
result = client.search("Tesla stock", num_results=5)

# Access results
for source in result.sources:
    print(f"[{source.id}] {source.title}")
    print(f"    {source.snippet}")
    print(f"    {source.url}")
```

### SearchAnalyzer Methods
```python
# Check if query needs search
needs_search = SearchAnalyzer.should_search("Tesla stock today")  # True
needs_search = SearchAnalyzer.should_search("What is 2+2?")      # False
```

### CitationFormatter Methods
```python
# Format response with citations
formatted = CitationFormatter.format_with_citations(
    text="Tesla is at $242 [cite:1]",
    sources=result.sources
)

# Extract metadata
metadata = CitationFormatter.extract_citations_metadata(formatted)
# Returns: {"has_citations": True, "citation_ids": [1]}
```

---

## 🎯 Success Metrics

After integration, track:
1. **Search Usage**: Queries per day/week
2. **Cost**: Actual monthly spend
3. **Quality**: User feedback on results
4. **Coverage**: % of queries that trigger search

---

## 📞 Support

- **SerpAPI API Docs**: https://brave.com/search/api/docs
- **API Status**: https://status.brave.com
- **Pricing**: https://brave.com/search/api/#pricing

---

## ✅ Checklist

- [x] Install dependencies (bcrypt, passlib, requests)
- [x] Run database migration (add_citations_schema.py)
- [x] Create web_search.py module
- [ ] Get SerpAPI API key
- [ ] Test with: `python3 web_search.py`
- [ ] Integrate with Inez message handler
- [ ] Update iOS app UI for citations
- [ ] Deploy and test end-to-end

---

**Ready to add your API key and test!** 🚀
