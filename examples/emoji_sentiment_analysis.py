"""
Emoji Sentiment Analysis Example
=================================

This example demonstrates how to use Durak's emoji sentiment mapping
for social media NLP tasks.

Key features:
- Extract emoji sentiment data for analysis
- Replace emojis with sentiment tokens for model training
- Calculate aggregate sentiment scores from emojis
"""

from durak import clean_text, extract_emoji_sentiment

# ==============================================================================
# Example 1: Basic Sentiment Token Replacement
# ==============================================================================

print("=" * 70)
print("Example 1: Replace Emojis with Sentiment Tokens")
print("=" * 70)

tweets = [
    "Harika bir gün! 😊🌞",
    "Çok üzgünüm 😢💔",
    "Ne düşünüyorsun? 🤔",
    "Mükemmel! 💯🔥",
]

for tweet in tweets:
    # Replace emojis with label tokens
    cleaned_label = clean_text(tweet, emoji_mode="sentiment", sentiment_format="label")
    print(f"Original:  {tweet}")
    print(f"Labels:    {cleaned_label}")
    
    # Replace with polarity tokens
    cleaned_polarity = clean_text(
        tweet, emoji_mode="sentiment", sentiment_format="polarity"
    )
    print(f"Polarity:  {cleaned_polarity}")
    print()

# ==============================================================================
# Example 2: Extract Sentiment Data for Aggregation
# ==============================================================================

print("=" * 70)
print("Example 2: Aggregate Emoji Sentiment Scores")
print("=" * 70)

social_media_posts = [
    "Bugün muhteşem bir gün! 🌞😍🔥 Her şey harika!",
    "Biraz üzgünüm ama iyiyim 😢😊",
    "Kafam karışık 🤔🤷",
    "Çok kızgınım! 😡😤🤬",
]

for post in social_media_posts:
    # Extract emoji sentiment data
    cleaned_text_result, sentiment_data = clean_text(
        post, emoji_mode="sentiment_extract"
    )
    
    # Calculate sentiment scores
    positive_score = sum(
        s["intensity"] for s in sentiment_data if s["polarity"] == "positive"
    )
    negative_score = sum(
        s["intensity"] for s in sentiment_data if s["polarity"] == "negative"
    )
    neutral_score = sum(
        s["intensity"] for s in sentiment_data if s["polarity"] == "neutral"
    )
    
    net_sentiment = positive_score - negative_score
    
    # Determine overall sentiment
    if net_sentiment > 0.5:
        overall = "POSITIVE 😊"
    elif net_sentiment < -0.5:
        overall = "NEGATIVE 😢"
    else:
        overall = "NEUTRAL 😐"
    
    print(f"Post:      {post}")
    print(f"Cleaned:   {cleaned_text_result}")
    print(f"Positive:  {positive_score:.2f}")
    print(f"Negative:  {negative_score:.2f}")
    print(f"Neutral:   {neutral_score:.2f}")
    print(f"Net:       {net_sentiment:+.2f}")
    print(f"Overall:   {overall}")
    print()

# ==============================================================================
# Example 3: Training Data Augmentation
# ==============================================================================

print("=" * 70)
print("Example 3: Prepare Training Data with Emoji Sentiment Tokens")
print("=" * 70)

# Simulate a social media corpus
corpus = [
    "Bu ürünü sevdim! 😍 Çok kaliteli 👍",
    "Berbat bir deneyim 😡 Asla tavsiye etmem 👎",
    "İdare eder, orta seviye 😐",
    "Harika! 🔥💯 En iyisi!",
]

print("Original Corpus vs. Augmented Corpus (with sentiment tokens):")
print()

for i, text in enumerate(corpus, 1):
    # Replace emojis with sentiment tokens for model training
    augmented = clean_text(text, emoji_mode="sentiment", sentiment_format="label")
    
    print(f"{i}. Original:   {text}")
    print(f"   Augmented:  {augmented}")
    print()

print("Use augmented corpus for training sentiment classifiers!")
print("Sentiment tokens preserve emoji signals while normalizing text.")

# ==============================================================================
# Example 4: Handle Unknown Emojis
# ==============================================================================

print("=" * 70)
print("Example 4: Handle Unknown/Rare Emojis")
print("=" * 70)

text_with_unknown = "Harika 😊 ve garip 🦄 ve şaşırtıcı 🤯"

# Preserve unknown emojis
result_preserve = clean_text(
    text_with_unknown,
    emoji_mode="sentiment",
    sentiment_unknown="preserve",
)
print(f"Preserve unknown: {result_preserve}")

# Remove unknown emojis
result_remove = clean_text(
    text_with_unknown,
    emoji_mode="sentiment",
    sentiment_unknown="remove",
)
print(f"Remove unknown:   {result_remove}")

# Replace unknown with [NEUTRAL]
result_neutral = clean_text(
    text_with_unknown,
    emoji_mode="sentiment",
    sentiment_unknown="neutral",
)
print(f"Neutral unknown:  {result_neutral}")

# ==============================================================================
# Example 5: Detailed Emoji Analysis
# ==============================================================================

print()
print("=" * 70)
print("Example 5: Detailed Emoji Sentiment Analysis")
print("=" * 70)

tweet = "Süper bir gün! 😊🔥💯 Ama biraz yorgunum 😴"

emojis, sentiments = extract_emoji_sentiment(tweet)

print(f"Tweet: {tweet}")
print()
print("Emoji Breakdown:")
print(f"{'Emoji':<10} {'Label':<15} {'Polarity':<12} {'Intensity':<10}")
print("-" * 50)

for emoji, sentiment in zip(emojis, sentiments):
    print(
        f"{emoji:<10} {sentiment['label']:<15} "
        f"{sentiment['polarity']:<12} {sentiment['intensity']:<10.2f}"
    )

print()
print("Summary:")
print(f"Total emojis: {len(emojis)}")
print(
    f"Positive: {sum(1 for s in sentiments if s['polarity'] == 'positive')}"
)
print(
    f"Negative: {sum(1 for s in sentiments if s['polarity'] == 'negative')}"
)
print(
    f"Neutral:  {sum(1 for s in sentiments if s['polarity'] == 'neutral')}"
)
