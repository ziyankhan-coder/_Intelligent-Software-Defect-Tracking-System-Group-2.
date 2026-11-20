from .rules import CATEGORY_RULES, SEVERITY_RULES
from .utils import preprocess_text


def predict_category(title, description):

    # Combine title and description
    raw_text = f"{title} {description}"

    # Preprocess bug report
    cleaned_text = preprocess_text(raw_text)

    # Check category keywords
    category_scores = {}

    for category, keywords in CATEGORY_RULES.items():

        score = 0

        for keyword in keywords:

            cleaned_keyword = preprocess_text(keyword)

            if cleaned_keyword in cleaned_text:
                score += 1

        category_scores[category] = score

    # Find category with highest score
    best_category = max(category_scores, key=category_scores.get)

    # Return Unknown if no keywords match
    if category_scores[best_category] == 0:
        return "Unknown"

    return best_category


def predict_severity(title, description):

    # Combine title and description
    raw_text = f"{title} {description}"

    # Preprocess bug report
    cleaned_text = preprocess_text(raw_text)

    # Check severity from highest to lowest
    severity_order = [
        "Critical",
        "High",
        "Medium",
        "Low"
    ]

    for severity in severity_order:

        for keyword in SEVERITY_RULES[severity]:

            cleaned_keyword = preprocess_text(keyword)

            if cleaned_keyword in cleaned_text:
                return severity

    # Default severity
    return "Medium"


def analyze_bug(title, description):

    category = predict_category(title, description)

    severity = predict_severity(title, description)

    return {
        "category": category,
        "severity": severity
    }