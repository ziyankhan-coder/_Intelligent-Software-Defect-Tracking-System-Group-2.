# BugFlow AI Triage Rules

# Bug category identification rules
CATEGORY_RULES = {
    "UI": [
        "button",
        "layout",
        "alignment",
        "font",
        "color",
        "display",
        "screen",
        "css",
        "responsive",
        "interface",
        "visual",
        "dropdown"
    ],

    "API": [
        "api",
        "endpoint",
        "server error",
        "http request",
        "response code",
        "request failed",
        "500 error",
        "404 error",
        "timeout",
        "json response"
    ],

    "DB": [
        "database",
        "sql",
        "query",
        "data loss",
        "data corruption",
        "record missing",
        "connection failed",
        "table",
        "postgresql",
        "mysql"
    ],

    "Auth": [
        "login",
        "logout",
        "authentication",
        "authorization",
        "password",
        "jwt",
        "token",
        "access denied",
        "permission",
        "unauthorized"
    ]
}


# Bug severity identification rules
SEVERITY_RULES = {
    "Critical": [
        "data loss",
        "database corruption",
        "system crash",
        "complete outage",
        "system down",
        "data breach",
        "critical failure",
        "entire application unavailable"
    ],

    "High": [
        "login failure",
        "authentication failure",
        "api failure",
        "payment failure",
        "server error",
        "unauthorized access",
        "service unavailable",
        "application crash"
    ],

    "Medium": [
        "validation error",
        "incorrect response",
        "functionality issue",
        "page not loading",
        "request timeout",
        "broken functionality",
        "feature not working"
    ],

    "Low": [
        "spelling mistake",
        "alignment issue",
        "minor display issue",
        "font issue",
        "color mismatch",
        "cosmetic issue"
    ]
}