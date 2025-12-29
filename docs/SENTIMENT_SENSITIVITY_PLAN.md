# Sentiment & Risk Sensitivity Improvement Plan

## Current Problems

1. **Too many neutral classifications** - FinBERT marks most articles as neutral
2. **High thresholds** - Need 0.05+ to show "Slightly Positive" (too strict)
3. **Weighted averaging dilutes signals** - One positive article gets averaged with neutrals
4. **Risk calculation too conservative** - Only triggers on extreme sentiment

## Improvement Strategy

### Phase 1: Make Sentiment More Granular (IMMEDIATE)

**Problem:** FinBERT only gives +1.0, -1.0, or 0.0

**Solution:** Use confidence scores to create nuanced sentiment

```python
# Current (BROKEN):
if label == "positive":
    score = 1.0
elif label == "negative":
    score = -1.0
else:
    score = 0.0

# Improved:
if label == "positive":
    score = 0.5 + (confidence * 0.5)  # Range: 0.5 to 1.0
elif label == "negative":
    score = -0.5 - (confidence * 0.5)  # Range: -0.5 to -1.0
else:
    # Neutral can still have slight bias
    positive_score = scores_dict.get("positive", 0)
    negative_score = scores_dict.get("negative", 0)
    if positive_score > negative_score:
        score = positive_score * 0.3  # Slight positive
    elif negative_score > positive_score:
        score = -negative_score * 0.3  # Slight negative
    else:
        score = 0.0
```

**Result:** Sentiment scores will range from -1.0 to +1.0 with more granularity

---

### Phase 2: Lower Sentiment Label Thresholds (IMMEDIATE)

**Current thresholds:**
- Very Positive: ≥ 0.5
- Positive: ≥ 0.2
- Slightly Positive: ≥ 0.05
- Neutral: -0.05 to 0.05
- Slightly Negative: ≤ -0.05
- Negative: ≤ -0.2
- Very Negative: ≤ -0.5

**New thresholds (more sensitive):**
- Very Positive: ≥ 0.3
- Positive: ≥ 0.1
- Slightly Positive: ≥ 0.02
- Neutral: -0.02 to 0.02
- Slightly Negative: ≤ -0.02
- Negative: ≤ -0.1
- Very Negative: ≤ -0.3

**Result:** More articles will show as positive/negative instead of neutral

---

### Phase 3: Improve Aggregation (MEDIUM PRIORITY)

**Problem:** One strong positive article gets diluted by neutrals

**Solution:** Use weighted median or percentile-based aggregation

```python
# Current: Weighted average (dilutes signals)
weighted_sentiment = weighted_sum / weight_sum

# Improved: Weighted median (preserves strong signals)
sentiment_scores = [s.score * w for s, w in zip(sentiments, weights)]
weighted_sentiment = weighted_median(sentiment_scores)
```

**Alternative:** Count-based approach
```python
# Count positive vs negative articles
positive_count = sum(1 for s in sentiments if s.score > 0.1)
negative_count = sum(1 for s in sentiments if s.score < -0.1)

if positive_count > negative_count * 1.5:
    sentiment = 0.3  # Slightly positive
elif negative_count > positive_count * 1.5:
    sentiment = -0.3  # Slightly negative
```

---

### Phase 4: Make Risk More Sensitive (MEDIUM PRIORITY)

**Current risk formula:**
```python
risk_score = |sentiment| × weight × (1 - confidence)
```

**Problem:** Only triggers on extreme sentiment

**Improved formula:**
```python
# Add volatility component
sentiment_volatility = std_dev(sentiment_scores)
risk_score = (|sentiment| * 0.6 + sentiment_volatility * 0.4) * weight * (1 - confidence)
```

**Lower risk thresholds:**
- Low: < 0.15 (was 0.3)
- Medium: 0.15 - 0.5 (was 0.3-0.8)
- High: > 0.5 (was 0.8)

---

### Phase 5: Article Quality Filtering (LOW PRIORITY)

**Problem:** Generic articles (like "Show HN" posts) dilute sentiment

**Solution:** Filter out low-quality articles before aggregation

```python
def is_relevant_article(article: Article) -> bool:
    """Check if article is relevant for sentiment analysis."""
    # Filter out generic tech news
    generic_keywords = ["show hn", "hacker news", "options chain data"]
    if any(kw in article.headline.lower() for kw in generic_keywords):
        return False
    
    # Require company name or ticker in headline/content
    if ticker not in article.headline.lower() and company_name not in article.content.lower():
        return False
    
    return True
```

---

## Implementation Priority

1. ✅ **Phase 1** - Granular sentiment scores (HIGHEST IMPACT)
2. ✅ **Phase 2** - Lower thresholds (IMMEDIATE)
3. ⚠️ **Phase 3** - Better aggregation (MEDIUM)
4. ⚠️ **Phase 4** - Risk sensitivity (MEDIUM)
5. ⚪ **Phase 5** - Article filtering (LOW)

## Expected Results

**Before:**
- 90% of stocks show "Neutral"
- Risk always "LOW"
- No actionable signals

**After:**
- 40-50% show positive/negative sentiment
- Risk varies (LOW/MEDIUM/HIGH)
- Clear actionable signals

