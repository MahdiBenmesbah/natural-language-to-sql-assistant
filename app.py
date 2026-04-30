
import os
import time
import sqlite3
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from google import genai


# =========================
# PAGE CONFIG
# =========================

st.set_page_config(
    page_title="NL to SQL Assistant",
    page_icon="🧠",
    layout="wide"
)


# =========================
# HEADER
# =========================

st.markdown("""
# 🧠 Natural Language to SQL Assistant

Ask business questions in natural language and get SQL queries automatically generated and executed on an e-commerce SQLite database.
""")

st.info(
    "Example: `Top 5 best-selling products` → the app generates SQL, executes it, and displays the result."
)


# =========================
# LOAD API KEY
# =========================

load_dotenv(r"C:\Users\ASUS\projet_llm_sql\API_Key", override=True)

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("Clé API introuvable. Vérifie ton fichier API_Key.")
    st.stop()

client = genai.Client(api_key=api_key)


# =========================
# DATABASE CONFIG
# =========================

DB_PATH = r"C:\Users\ASUS\projet_llm_sql\ecommerce.db"

if not os.path.exists(DB_PATH):
    st.error("Base de données ecommerce.db introuvable.")
    st.stop()


SCHEMA = """
TABLE users(id, name, age, country)
TABLE products(id, name, category, price)
TABLE orders(id, user_id, date)
TABLE order_items(id, order_id, product_id, quantity)
"""


# =========================
# SESSION STATE
# =========================

if "sql_cache" not in st.session_state:
    st.session_state.sql_cache = {}

if "history" not in st.session_state:
    st.session_state.history = []


# =========================
# SQL VALIDATION
# =========================

def validate_sql(sql):
    sql_clean = sql.strip().lower()

    if not sql_clean.startswith("select"):
        raise ValueError("Only SELECT queries are allowed.")

    forbidden_words = [
        "delete", "insert", "update", "drop", "alter", "create",
        "replace", "truncate", "attach", "detach", "pragma"
    ]

    for word in forbidden_words:
        if word in sql_clean:
            raise ValueError(f"Dangerous SQL keyword detected: {word}")

    return True


# =========================
# DATABASE FUNCTIONS
# =========================

def run_sql(sql):
    conn = sqlite3.connect(DB_PATH)

    try:
        df = pd.read_sql_query(sql, conn)
        return df
    finally:
        conn.close()


def get_database_stats():
    conn = sqlite3.connect(DB_PATH)

    try:
        users_count = pd.read_sql_query(
            "SELECT COUNT(*) AS count FROM users",
            conn
        )["count"][0]

        products_count = pd.read_sql_query(
            "SELECT COUNT(*) AS count FROM products",
            conn
        )["count"][0]

        orders_count = pd.read_sql_query(
            "SELECT COUNT(*) AS count FROM orders",
            conn
        )["count"][0]

        revenue = pd.read_sql_query(
            """
            SELECT SUM(products.price * order_items.quantity) AS revenue
            FROM order_items
            JOIN products ON order_items.product_id = products.id
            """,
            conn
        )["revenue"][0]

        return users_count, products_count, orders_count, revenue

    finally:
        conn.close()


# =========================
# GEMINI NL TO SQL
# =========================

def nl_to_sql(question):
    question_key = question.strip().lower()

    if question_key in st.session_state.sql_cache:
        return st.session_state.sql_cache[question_key], "cache"

    prompt = f"""
You are a senior SQL expert.

Your task is to convert a natural language question into a valid SQLite SELECT query.

Rules:
- Output only SQL.
- No markdown.
- No explanation.
- Only SELECT queries are allowed.
- Never use INSERT, UPDATE, DELETE, DROP, ALTER, CREATE.
- Use explicit column aliases when aggregating.
- Use JOINs when needed.
- When the user asks for top products, best products, or most sold products, include product name and total quantity sold.
- When the user asks for revenue, calculate revenue as products.price * order_items.quantity.
- When the user asks for customers or clients, use the users table.
- When the user asks for countries, use users.country.
- When the user asks for categories, use products.category.
- Always make the result useful for analysis, not just IDs.

Database schema:
{SCHEMA}

Question:
{question}

SQL:
"""

    models_to_try = [
        "gemini-flash-latest",
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite"
    ]

    last_error = None

    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )

            sql = response.text.strip()
            sql = sql.replace("```sql", "").replace("```", "").strip()

            validate_sql(sql)

            st.session_state.sql_cache[question_key] = sql

            return sql, model_name

        except Exception as e:
            last_error = e
            time.sleep(2)

    raise RuntimeError(f"Aucun modèle n'a fonctionné. Dernière erreur : {last_error}")


def ask_database(question):
    sql, source = nl_to_sql(question)
    df = run_sql(sql)

    return {
        "question": question,
        "sql": sql,
        "dataframe": df,
        "source": source
    }


# =========================
# CHART FUNCTION
# =========================

def show_chart_if_possible(df):
    if df.empty:
        return

    if df.shape[1] < 2:
        return

    first_col = df.columns[0]
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()

    if not numeric_cols:
        return

    y_col = numeric_cols[0]

    st.subheader("📊 Visualisation")

    chart_df = df[[first_col, y_col]].set_index(first_col)
    st.bar_chart(chart_df)


# =========================
# KPI DASHBOARD
# =========================

users_count, products_count, orders_count, revenue = get_database_stats()

col1, col2, col3, col4 = st.columns(4)

col1.metric("Users", users_count)
col2.metric("Products", products_count)
col3.metric("Orders", orders_count)
col4.metric("Revenue", f"{revenue:,.2f} €")

st.divider()


# =========================
# SIDEBAR
# =========================

with st.sidebar:
    st.header("📌 About")

    st.write(
        "This app converts natural language questions into SQL queries using Gemini API, "
        "then executes them on a SQLite e-commerce database."
    )

    st.divider()

    st.header("💡 Example questions")

    examples = [
        "top 5 produits les plus vendus",
        "quel est le chiffre d'affaires total ?",
        "top 5 clients par montant dépensé",
        "nombre de commandes par pays",
        "catégorie qui génère le plus de chiffre d'affaires",
        "âge moyen des utilisateurs par pays",
        "prix moyen des produits par catégorie"
    ]

    selected_example = st.selectbox(
        "Choisir un exemple :",
        examples
    )

    st.divider()

    st.header("⚙️ Options")

    show_sql = st.checkbox("Afficher le SQL généré", value=True)
    show_chart = st.checkbox("Afficher le graphique si possible", value=True)

    if st.button("Vider le cache SQL"):
        st.session_state.sql_cache = {}
        st.success("Cache vidé.")

    if st.button("Vider l'historique"):
        st.session_state.history = []
        st.success("Historique vidé.")


# =========================
# MAIN INPUT
# =========================

st.subheader("💬 Pose ta question")

question = st.text_input(
    "Écris ta question :",
    value=selected_example,
    placeholder="Exemple : top 5 produits les plus vendus"
)

run_button = st.button("Générer et exécuter SQL", type="primary")


# =========================
# MAIN EXECUTION
# =========================

if run_button:
    if not question.strip():
        st.warning("Écris une question avant de lancer.")
    else:
        with st.spinner("Génération SQL et exécution en cours..."):
            try:
                result = ask_database(question)

                st.session_state.history.append({
                    "question": result["question"],
                    "sql": result["sql"],
                    "source": result["source"]
                })

                st.success("Requête exécutée avec succès.")

                info_col1, info_col2 = st.columns([2, 1])

                with info_col1:
                    st.subheader("Question")
                    st.write(result["question"])

                with info_col2:
                    st.subheader("Source")
                    st.write(result["source"])

                if show_sql:
                    st.subheader("SQL généré")
                    st.code(result["sql"], language="sql")

                st.subheader("Résultat")

                df_display = result["dataframe"].copy()
                df_display.index = df_display.index + 1
                df_display.index.name = "Rank"

                st.dataframe(df_display, use_container_width=True)

                if show_chart:
                    show_chart_if_possible(result["dataframe"])

            except Exception as e:
                st.error(f"Erreur : {e}")


# =========================
# HISTORY
# =========================

if st.session_state.history:
    st.divider()
    st.subheader("🕘 Historique des requêtes")

    for item in reversed(st.session_state.history[-5:]):
        with st.expander(item["question"]):
            st.caption(f"Source : {item['source']}")
            st.code(item["sql"], language="sql")