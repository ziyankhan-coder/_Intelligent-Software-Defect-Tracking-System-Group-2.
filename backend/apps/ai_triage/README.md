# BugFlow – AI Triage Module

## 1. Overview

The AI Triage module is a component of BugFlow, a Software Issue Tracking and Resolution Platform.

Its primary purpose is to automatically analyze bug reports and predict their categories and severity levels. This helps streamline bug classification, reduce manual effort, and support faster issue management.

The current implementation uses a rule-based approach with NLP text preprocessing.

## 2. Implemented Features

### 2.1 Automatic Bug Categorization

Automatically classifies bug reports into four categories:

- **UI:** User interface and visual-related issues.
- **API:** API, endpoint, server, and request-related issues.
- **DB:** Database, SQL, and data-related issues.
- **Auth:** Authentication, authorization, login, and permission-related issues.

### 2.2 Severity Prediction

Predicts the severity of reported bugs using predefined keyword rules.

Supported severity levels:

- **Critical:** Major system failures, data loss, database corruption, and complete outages.
- **High:** Login failures, payment failures, server errors, and authentication failures.
- **Medium:** Validation errors, incorrect responses, and general functionality issues.
- **Low:** Minor visual defects, spelling mistakes, and cosmetic issues.

### 2.3 NLP Text Preprocessing

The module uses NLTK for basic text preprocessing, including:

- Lowercase conversion.
- Tokenization.
- Stopword removal.
- Lemmatization.
- Preservation of negation words such as "not" and "no".

## 3. Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core implementation |
| Django | Backend framework |
| Django REST Framework | API development |
| NLTK | NLP preprocessing |
| PostgreSQL | Project database |
| Postman | API testing |

## 4. Module Structure

```text
ai_triage/
│
├── __init__.py
├── apps.py
├── models.py
├── rules.py
├── utils.py
├── services.py
├── serializers.py
├── views.py
├── urls.py
├── tests.py
├── README.md
│
└── data/
    └── bugflow_sample_bug_dataset_200.csv
```

### File Responsibilities

| File | Description |
|---|---|
| `apps.py` | Django application configuration. |
| `models.py` | Database models for the module. |
| `rules.py` | Predefined category and severity keyword rules. |
| `utils.py` | NLP text preprocessing functions. |
| `services.py` | Core bug analysis and prediction logic. |
| `serializers.py` | Validates incoming API request data. |
| `views.py` | Handles API requests and returns predictions. |
| `urls.py` | Defines AI triage API routes. |
| `tests.py` | Test cases for the module. |
| `data/` | Contains the sample bug dataset. |

## 5. API Documentation

### Analyze Bug Draft

**Endpoint:**

`POST /api/v1/ai/analyze-draft/`

**Description:**

Accepts a bug title and description, analyzes the provided text, and returns the predicted category and severity.

**Request Body:**

```json
{
    "title": "Database crash",
    "description": "Database corruption caused complete system outage."
}
```

**Expected Response:**

```json
{
    "success": true,
    "message": "Bug analysis completed",
    "data": {
        "category": "DB",
        "severity": "Critical"
    }
}
```

### Response Status Codes

| Status Code | Description |
|---|---|
| 200 | Bug analysis completed successfully. |
| 400 | Invalid or missing request data. |
| 401 | Authentication credentials are missing or invalid. |
| 500 | Internal server error. |

**Authentication:** The endpoint currently requires an authenticated user.

## 6. Prediction Workflow

The current bug analysis workflow follows these steps:

1. Receive the bug title and description through the API.
2. Validate the incoming request using the serializer.
3. Combine the title and description.
4. Preprocess the text using NLP techniques.
5. Compare the processed text against predefined category keywords.
6. Predict severity using the severity keyword rules.
7. Return the predicted category and severity as a JSON response.

## 7. Dataset

A synthetic sample dataset containing 200 bug reports has been prepared for initial development and testing.

The dataset includes:

- UI-related bugs.
- API-related bugs.
- Database-related bugs.
- Authentication-related bugs.

Each record contains a bug ID, title, description, category, and severity.

The dataset is intended for development, validation, and future enhancements.

## 8. Setup Instructions

Install the required dependencies from the backend directory:

```bash
pip install -r requirements.txt
```

Download the required NLTK resources:

```bash
python -m nltk.downloader stopwords wordnet omw-1.4
```

Start the Django development server:

```bash
python manage.py runserver
```

The API can then be tested using Postman.

## 9. Testing

The API has been tested using Postman with sample bug reports covering the supported categories.

| Test Scenario | Predicted Category | Predicted Severity |
|---|---|---|
| Database crash | DB | Critical |
| Login issue | Auth | High |
| UI issue | UI | Low |
| Payment API failure | API | High |

All four test scenarios returned successful API responses with the expected predictions.

## 10. Current Limitations

- Predictions currently rely on predefined keyword-based rules.
- The system does not yet use a trained machine learning classification model.
- Prediction accuracy depends on the keywords and rules defined in the module.
- More extensive testing is required to handle ambiguous and complex bug descriptions.

## 11. Future Enhancements

The following features are planned for subsequent development:

- TF-IDF and cosine similarity-based duplicate bug detection.
- Intelligent developer recommendation based on skills and workload.
- Automated bug priority scoring.
- Release risk analysis.
- Improved NLP-based classification and prediction accuracy.

---

**Module:** AI Triage & Smart Resolution  
**Project:** BugFlow – Software Issue Tracking & Resolution Platform