from apps.ai_triage.services import analyze_bug

bugs = [
    (
        "Database crash",
        "Database corruption caused complete system outage."
    ),
    (
        "Login issue",
        "Authentication failure prevents users from logging in."
    ),
    (
        "Form issue",
        "Validation error occurs during registration."
    ),
    (
        "UI issue",
        "Minor alignment issue in the footer."
    ),
    (
        "Payment API failure",
        "Payment service returns a server error."
    )
]

for title, description in bugs:

    result = analyze_bug(title, description)

    print("\nBug:", title)
    print("Prediction:", result)