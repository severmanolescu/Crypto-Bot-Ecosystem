from sdk.DataBase.DataBaseHandler import DataBaseHandler

async def extract_sentiment_from_summary(summary):
    summary_lower = summary.lower()  # Convert to lowercase for easier matching

    if "bullish" in summary_lower and    ("bearish" in summary_lower
                                       or "neutral" in summary_lower):
        return "Unknown"
    if "bullish" in summary_lower:
        return "Positive"
    elif "bearish" in summary_lower:
        return "Negative"
    elif "neutral" in summary_lower:
        return "Neutral"
    else:
        return "Unknown"  # If no sentiment is found

async def calculate_sentiment_trend(news_items, save_data = False):
    sentiment_counts = {"Unknown": 0, "Negative": 0, "Neutral": 0, "Positive": 0}

    for item in news_items:
        if item[4] is not None:
            sentiment = await extract_sentiment_from_summary(item[4])
            sentiment_counts[sentiment] += 1  # Count occurrences
    if save_data:
        db = DataBaseHandler()

        await db.store_market_sentiment(sentiment_counts)
        return ""
    else:
        print("Calculating the sentiment...")

        max_sentiment = max(sentiment_counts, key=sentiment_counts.get)

        # Generate summary message
        trend_message = (
            f"📊 <b>Crypto sentiment for today:</b> 📊\n\n"
            f"{max_sentiment} - The market sentiment is: {max_sentiment.replace('🔴 ', '').replace('🟡 ', '').replace('🟢 ', '')}.\n"
            f"📈 Positive: {sentiment_counts['Positive']}\n"
            f"⚖️ Neutral: {sentiment_counts['Neutral']}\n"
            f"📉 Negative: {sentiment_counts['Negative']}\n"
            f"❓ Unknown: {sentiment_counts['Unknown']}\n"
            f"#Sentiment\n\n"
        )

        print(trend_message)

        return trend_message

async def get_market_sentiment(save_data = False):
    db = DataBaseHandler()

    articles = await db.fetch_todays_news()

    return await calculate_sentiment_trend(articles, save_data)
