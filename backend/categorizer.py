
def categorize_transaction(description: str, transaction_type: str) -> str:
    """Assign a category using simple, editable keyword rules."""

    if transaction_type == "income":
        return "Income"

    text = description.lower()

    rules = {
        "Food": [
            "canteen", "restaurant", "swiggy",
            "zomato", "grocery", "food", "cafe",
        ],
        "Transport": [
            "bus", "metro", "train", "uber",
            "ola", "fuel", "petrol", "taxi",
        ],
        "Shopping": [
            "amazon", "flipkart", "shopping",
            "clothing", "mall",
        ],
        "Subscriptions": [
            "spotify", "netflix", "subscription",
            "prime video",
        ],
        "Bills": [
            "electricity", "water bill", "internet",
            "mobile recharge", "broadband",
        ],
        "Healthcare": [
            "pharmacy", "hospital", "medical",
            "clinic",
        ],
    }

    for category, keywords in rules.items():
        if any(keyword in text for keyword in keywords):
            return category

    return "Other"
