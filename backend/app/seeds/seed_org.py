"""Seed data for companies, branches, departments (DB-agnostic)."""
import os, uuid
from sqlalchemy import create_engine, text

DB_URL = os.getenv("SQLALCHEMY_DATABASE_URL", "sqlite:///./app.db")
engine = create_engine(DB_URL, future=True)

def u(): return str(uuid.uuid4())

def run():
    with engine.begin() as conn:
        # Companies
        c_system = u(); c_acme = u()
        conn.execute(text("""INSERT INTO companies (id, code, name) VALUES (:id1, 'SYSTEM', 'System Company'), (:id2, 'ACME', 'Acme Corporation')"""),
                     dict(id1=c_system, id2=c_acme))
        # Branches
        b_hq = u(); b_east = u()
        conn.execute(text("""INSERT INTO branches (id, company_id, code, name) VALUES (:b1, :c1, 'HQ', 'Headquarters'), (:b2, :c2, 'EAST', 'East Branch')"""),
                     dict(b1=b_hq, c1=c_system, b2=b_east, c2=c_acme))
        # Departments
        d_fin = u(); d_sales = u(); d_it = u()
        conn.execute(text("""INSERT INTO departments (id, company_id, branch_id, code, name) VALUES (:d1, :c1, NULL, 'FIN', 'Finance'), (:d2, :c2, :b2, 'SALES', 'Sales'), (:d3, :c1, :b1, 'IT', 'Information Technology')"""),
                     dict(d1=d_fin, c1=c_system, d2=d_sales, c2=c_acme, b2=b_east, d3=d_it, b1=b_hq))
    print("Seed completed.")
if __name__ == "__main__":
    run()
