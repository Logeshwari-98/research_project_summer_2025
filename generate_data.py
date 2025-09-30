# generate_data.py
import pandas as pd
import json
from pathlib import Path
import random
from datetime import datetime, timedelta

OUT = Path("data")
OUT.mkdir(exist_ok=True)

def make_transactions(n=200):
    products = [
        {"product_id": 1, "name": "Widget", "category": "Hardware"},
        {"product_id": 2, "name": "Gadget", "category": "Electronics"},
        {"product_id": 3, "name": "Service A", "category": "Services"}
    ]
    customers = [
        {"customer_id": 1, "name": "Alpha LLC", "region": "EU"},
        {"customer_id": 2, "name": "Beta GmbH", "region": "EU"},
        {"customer_id": 3, "name": "Gamma Inc", "region": "US"},
        {"customer_id": 4, "name": "Delta Ltd", "region": "APAC"}
    ]
    rows = []
    start = datetime(2023,1,1)
    for i in range(1, n+1):
        dt = start + timedelta(days=random.randint(0, 700))
        prod = random.choice(products)
        cust = random.choice(customers)
        amount = round(random.uniform(50, 2000), 2)
        cost = round(amount * random.uniform(0.3, 0.8), 2)
        rows.append({
            "transaction_id": i,
            "date": dt.strftime("%Y-%m-%d"),
            "customer_id": cust["customer_id"],
            "product_id": prod["product_id"],
            "amount": amount,
            "currency": "EUR" if cust["region"] == "EU" else "USD",
            "region": cust["region"],
            "cost": cost
        })
    df = pd.DataFrame(rows)
    df.to_csv(OUT/"transactions.csv", index=False)

def make_products():
    df = pd.DataFrame([
        {"product_id":1,"name":"Widget","category":"Hardware","base_cost":100},
        {"product_id":2,"name":"Gadget","category":"Electronics","base_cost":150},
        {"product_id":3,"name":"Service A","category":"Services","base_cost":20}
    ])
    df.to_csv(OUT/"products.csv", index=False)

def make_customers():
    df = pd.DataFrame([
        {"customer_id":1,"name":"Alpha LLC","segment":"Enterprise","country":"Germany","region":"EU"},
        {"customer_id":2,"name":"Beta GmbH","segment":"SMB","country":"Germany","region":"EU"},
        {"customer_id":3,"name":"Gamma Inc","segment":"Enterprise","country":"USA","region":"US"},
        {"customer_id":4,"name":"Delta Ltd","segment":"SMB","country":"India","region":"APAC"}
    ])
    df.to_csv(OUT/"customers.csv", index=False)

def make_expenses():
    df = pd.DataFrame([
        {"expense_id":1,"date":"2023-03-15","type":"Hosting","amount":1200,"region":"US"},
        {"expense_id":2,"date":"2023-04-20","type":"Salaries","amount":15000,"region":"EU"},
        {"expense_id":3,"date":"2023-07-01","type":"Marketing","amount":4000,"region":"APAC"},
    ])
    df.to_csv(OUT/"expenses.csv", index=False)

def write_lineage():
    """
    Multi-step lineage for metrics typical in finance:
    - total_revenue
    - revenue_q2_2023
    - gross_margin_percentage_by_product
    - net_income_2023 (simple illustrative)
    - customer_ltv (multi-step)
    """
    lineage = {
        "total_revenue": {
            "metric": "total_revenue",
            "description": "Total revenue is the sum of all transaction amounts across all dates and regions.",
            "steps": [
                {
                    "id": "t1",
                    "sql": "SELECT SUM(amount) as total_revenue FROM transactions;",
                    "description": "Aggregate all transactions and sum the 'amount' column to obtain total revenue."
                }
            ]
        },
        "revenue_q2_2023": {
            "metric": "revenue_q2_2023",
            "description": "Revenue for Q2 2023 (Apr 1 to Jun 30, 2023).",
            "steps": [
                {"id":"q2_1","sql":"SELECT * FROM transactions WHERE date BETWEEN '2023-04-01' AND '2023-06-30';","description":"Filter transactions to dates within Q2 2023."},
                {"id":"q2_2","sql":"SELECT SUM(amount) as q2_revenue FROM <filtered> ;","description":"Sum amounts from the filtered transaction set to compute Q2 revenue."}
            ]
        },
        "gross_margin_percentage_by_product": {
            "metric":"gross_margin_percentage_by_product",
            "description":"Gross margin percentage per product = (revenue_by_product - cogs_by_product) / revenue_by_product",
            "steps":[
                {"id":"g1","sql":"SELECT product_id, SUM(amount) as revenue FROM transactions GROUP BY product_id;","description":"Aggregate revenue by product using transactions grouped by product_id."},
                {"id":"g2","sql":"SELECT product_id, SUM(cost) as cogs FROM transactions GROUP BY product_id;","description":"Aggregate COGS by product (using transaction-level 'cost' field)."},
                {"id":"g3","sql":"SELECT r.product_id, (r.revenue - c.cogs) / r.revenue as gross_margin_pct FROM revenue r JOIN cogs c ON r.product_id = c.product_id;","description":"Join revenue and cogs by product and compute (revenue - cogs)/revenue for each product."}
            ]
        },
        "net_income_2023": {
            "metric":"net_income_2023",
            "description":"Net income for calendar year 2023 approximated as total revenue in 2023 minus operating expenses dated in 2023.",
            "steps":[
                {"id":"n1","sql":"SELECT SUM(amount) as rev_2023 FROM transactions WHERE date BETWEEN '2023-01-01' AND '2023-12-31';","description":"Sum transaction amounts for 2023 to get revenue in 2023."},
                {"id":"n2","sql":"SELECT SUM(amount) as expenses_2023 FROM expenses WHERE date BETWEEN '2023-01-01' AND '2023-12-31';","description":"Sum expenses in 2023."},
                {"id":"n3","sql":"SELECT rev_2023 - expenses_2023 as net_income_2023;","description":"Subtract expenses from revenue to compute net income."}
            ]
        },
        "customer_ltv": {
            "metric":"customer_ltv",
            "description":"Simplified customer lifetime value (CLV): average revenue per customer * expected customer lifetime (in years).",
            "steps":[
                {"id":"c1","sql":"SELECT customer_id, SUM(amount) as revenue_per_customer FROM transactions GROUP BY customer_id;","description":"Aggregate revenue per customer."},
                {"id":"c2","sql":"SELECT AVG(revenue_per_customer) as avg_rev_per_customer FROM <customer_revenue> ;","description":"Compute average revenue per customer across all customers."},
                {"id":"c3","sql":"# business rule: use expected lifetime = 3 years","description":"Apply business rule: expected customer lifetime = 3 years."},
                {"id":"c4","sql":"SELECT avg_rev_per_customer * 3 as expected_customer_ltv;","description":"Multiply average revenue per customer by expected lifetime to get CLV."}
            ]
        }
    }
    with open("data/lineage.json","w") as f:
        json.dump(lineage, f, indent=2)

if __name__ == "__main__":
    make_products()
    make_customers()
    make_transactions(600)
    make_expenses()
    write_lineage()
    print("Data generated in ./data/ (transactions.csv, products.csv, customers.csv, expenses.csv, lineage.json)")
