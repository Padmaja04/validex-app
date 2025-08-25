def get_greeting(now):
    hour = now.hour
    if hour < 5:
        return "🌙 Working late? Good night!"
    elif hour < 12:
        return "🌞 Good morning! Wishing you a fresh start."
    elif hour < 17:
        return "☀️ Good afternoon! Keep up the great work."
    elif hour < 21:
        return "🌇 Good evening! Hope your day’s been productive."
    else:
        return "🌙 Wrapping up strong? Good night!"