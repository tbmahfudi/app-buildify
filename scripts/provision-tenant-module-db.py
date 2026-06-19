#!/usr/bin/env python3
"""Prototype: provision a per-tenant module database. Story 22.1.1."""
import os, time, subprocess, sys


def provision(tenant_id: str, module_id: str) -> dict:
    db_name = f"{tenant_id}_{module_id}".replace('-', '_')
    pg_url = os.environ.get('DATABASE_URL', 'postgresql://appuser:apppassword@localhost:5432/appdb')

    start = time.time()

    # Create database
    create_cmd = ['psql', pg_url, '-c', f'CREATE DATABASE {db_name};']
    result = subprocess.run(create_cmd, capture_output=True, text=True)
    if result.returncode != 0 and 'already exists' not in result.stderr:
        return {'success': False, 'error': result.stderr, 'elapsed_s': time.time() - start}

    elapsed = time.time() - start
    print(f"Provisioned {db_name} in {elapsed:.2f}s")
    gate_pass = elapsed <= 60
    print(f"Gate (≤60s): {'PASS' if gate_pass else 'FAIL'}")
    return {'success': True, 'db_name': db_name, 'elapsed_s': elapsed, 'gate_pass': gate_pass}


if __name__ == '__main__':
    tenant_id = sys.argv[1] if len(sys.argv) > 1 else 'test_tenant'
    module_id = sys.argv[2] if len(sys.argv) > 2 else 'financial'
    result = provision(tenant_id, module_id)
    print(result)
