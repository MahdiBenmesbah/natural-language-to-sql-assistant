# Natural Language to SQL Assistant

A Streamlit application that converts natural language questions into SQL queries using the Gemini API, then executes them on a SQLite e-commerce database.

## Project Goal

The goal is to make database exploration easier by allowing users to ask business questions in natural language instead of writing SQL manually.

**Example question:**

```text
Top 5 best-selling products
```

The app generates a SQL query, executes it on the database, and displays the result as a table and chart.

## Features

- Natural language to SQL generation
- SQLite query execution
- Interactive Streamlit interface
- Automatic table display
- Automatic chart generation when possible
- SQL validation for security
- Query cache to reduce API calls
- Fallback between Gemini models when one model is unavailable
- Realistic e-commerce sample database

## Tech Stack

- Python
- Streamlit
- SQLite
- Pandas
- Google Gemini API

## Database Schema

```text
users(id, name, age, country)
products(id, name, category, price)
orders(id, user_id, date)
order_items(id, order_id, product_id, quantity)
```

## Example Questions

- Top 5 best-selling products
- What is the total revenue?
- Top 5 customers by amount spent
- Number of orders by country
- Category generating the most revenue
- Average user age by country
- Average product price by category

## How to Run Locally

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a local API key file named `API_Key`:

```text
GEMINI_API_KEY=your_api_key_here
```

Run the app:

```bash
streamlit run app.py
```

On Windows, you can also double-click:

```text
launch_app.bat
```

## Security

Only `SELECT` queries are allowed.

The application blocks dangerous SQL keywords such as:

- DELETE
- DROP
- UPDATE
- INSERT
- ALTER
- CREATE
- TRUNCATE
- ATTACH
- DETACH
- PRAGMA

## Screenshots

### Home Page

Main interface with project description, database KPIs, sidebar examples, and the natural language input field.

![Home Page](assets/home.png)

### Generated SQL and Result

The assistant converts a natural language question into SQL and executes it on the SQLite database.

![SQL Result](assets/sql_result.png)

### Automatic Chart

When the result contains a categorical column and a numeric column, the app automatically displays a chart.

![Chart](assets/chart.png)
