"""Initial migration - create financial tables

Revision ID: 001_initial_financial
Revises:
Create Date: 2024-12-10 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import CheckConstraint, UniqueConstraint


# revision identifiers, used by Alembic.
revision = '001_initial_financial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create financial_accounts table
    op.create_table(
        'financial_accounts',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), nullable=False, index=True),
        sa.Column('company_id', sa.String(36), nullable=False, index=True),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('category', sa.String(100)),
        sa.Column('sub_category', sa.String(100)),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False, index=True),
        sa.Column('is_header', sa.Boolean, default=False, nullable=False),
        sa.Column('parent_account_id', sa.String(36), sa.ForeignKey('financial_accounts.id')),
        sa.Column('current_balance', sa.Numeric(18, 2), default=0.00, nullable=False),
        sa.Column('debit_balance', sa.Numeric(18, 2), default=0.00, nullable=False),
        sa.Column('credit_balance', sa.Numeric(18, 2), default=0.00, nullable=False),
        sa.Column('currency_code', sa.String(3), default='USD', nullable=False),
        sa.Column('tax_category', sa.String(50)),
        sa.Column('requires_department', sa.Boolean, default=False, nullable=False),
        sa.Column('requires_project', sa.Boolean, default=False, nullable=False),
        sa.Column('extra_data', sa.Text),
        sa.Column('created_by', sa.String(36)),
        sa.Column('updated_by', sa.String(36)),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime, onupdate=sa.func.now()),
        UniqueConstraint('tenant_id', 'company_id', 'code', name='uq_account_code'),
        CheckConstraint("type IN ('asset', 'liability', 'equity', 'revenue', 'expense')", name='chk_account_type'),
    )

    # Create financial_customers table
    op.create_table(
        'financial_customers',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), nullable=False, index=True),
        sa.Column('company_id', sa.String(36), nullable=False, index=True),
        sa.Column('customer_number', sa.String(50), nullable=False),
        sa.Column('name', sa.String(255), nullable=False, index=True),
        sa.Column('display_name', sa.String(255)),
        sa.Column('email', sa.String(255), index=True),
        sa.Column('phone', sa.String(50)),
        sa.Column('website', sa.String(255)),
        sa.Column('billing_address_line1', sa.String(255)),
        sa.Column('billing_address_line2', sa.String(255)),
        sa.Column('billing_city', sa.String(100)),
        sa.Column('billing_state', sa.String(100)),
        sa.Column('billing_postal_code', sa.String(20)),
        sa.Column('billing_country', sa.String(100)),
        sa.Column('shipping_address_line1', sa.String(255)),
        sa.Column('shipping_address_line2', sa.String(255)),
        sa.Column('shipping_city', sa.String(100)),
        sa.Column('shipping_state', sa.String(100)),
        sa.Column('shipping_postal_code', sa.String(20)),
        sa.Column('shipping_country', sa.String(100)),
        sa.Column('currency_code', sa.String(3), default='USD', nullable=False),
        sa.Column('payment_terms_days', sa.Integer, default=30, nullable=False),
        sa.Column('credit_limit', sa.Numeric(18, 2)),
        sa.Column('tax_id', sa.String(50)),
        sa.Column('tax_exempt', sa.Boolean, default=False, nullable=False),
        sa.Column('receivables_account_id', sa.String(36), sa.ForeignKey('financial_accounts.id')),
        sa.Column('current_balance', sa.Numeric(18, 2), default=0.00, nullable=False),
        sa.Column('overdue_balance', sa.Numeric(18, 2), default=0.00, nullable=False),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False, index=True),
        sa.Column('notes', sa.Text),
        sa.Column('extra_data', sa.Text),
        sa.Column('created_by', sa.String(36)),
        sa.Column('updated_by', sa.String(36)),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime, onupdate=sa.func.now()),
        UniqueConstraint('tenant_id', 'company_id', 'customer_number', name='uq_customer_number'),
    )

    # Create financial_tax_rates table
    op.create_table(
        'financial_tax_rates',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), nullable=False, index=True),
        sa.Column('company_id', sa.String(36), nullable=False, index=True),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('rate_percentage', sa.Numeric(5, 2), nullable=False),
        sa.Column('tax_type', sa.String(50), nullable=False),
        sa.Column('tax_authority', sa.String(255)),
        sa.Column('tax_jurisdiction', sa.String(100)),
        sa.Column('effective_from', sa.Date, nullable=False),
        sa.Column('effective_to', sa.Date),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False, index=True),
        sa.Column('is_default', sa.Boolean, default=False, nullable=False),
        sa.Column('is_compound', sa.Boolean, default=False, nullable=False),
        sa.Column('tax_account_id', sa.String(36)),
        sa.Column('applies_to_sales', sa.Boolean, default=True, nullable=False),
        sa.Column('applies_to_purchases', sa.Boolean, default=False, nullable=False),
        sa.Column('country_code', sa.String(2)),
        sa.Column('state_code', sa.String(50)),
        sa.Column('city', sa.String(100)),
        sa.Column('postal_code', sa.String(20)),
        sa.Column('extra_data', sa.Text),
        sa.Column('created_by', sa.String(36)),
        sa.Column('updated_by', sa.String(36)),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime, onupdate=sa.func.now()),
        UniqueConstraint('tenant_id', 'company_id', 'code', name='uq_tax_rate_code'),
        CheckConstraint('rate_percentage >= 0 AND rate_percentage <= 100', name='chk_rate_percentage_range'),
        CheckConstraint("tax_type IN ('sales_tax', 'vat', 'gst', 'excise', 'service_tax', 'other')", name='chk_tax_type'),
    )

    # Create financial_journal_entries table
    op.create_table(
        'financial_journal_entries',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), nullable=False, index=True),
        sa.Column('company_id', sa.String(36), nullable=False, index=True),
        sa.Column('entry_number', sa.String(50), nullable=False),
        sa.Column('reference_number', sa.String(100)),
        sa.Column('entry_date', sa.Date, nullable=False, index=True),
        sa.Column('posting_date', sa.Date),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('memo', sa.Text),
        sa.Column('status', sa.String(20), default='draft', nullable=False, index=True),
        sa.Column('is_posted', sa.Boolean, default=False, nullable=False),
        sa.Column('posted_at', sa.DateTime),
        sa.Column('posted_by', sa.String(36)),
        sa.Column('is_reversal', sa.Boolean, default=False, nullable=False),
        sa.Column('reversed_entry_id', sa.String(36), sa.ForeignKey('financial_journal_entries.id')),
        sa.Column('reversed_at', sa.DateTime),
        sa.Column('reversed_by', sa.String(36)),
        sa.Column('source_type', sa.String(50)),
        sa.Column('source_id', sa.String(36)),
        sa.Column('total_debit', sa.Numeric(18, 2), default=0.00, nullable=False),
        sa.Column('total_credit', sa.Numeric(18, 2), default=0.00, nullable=False),
        sa.Column('currency_code', sa.String(3), default='USD', nullable=False),
        sa.Column('tags', sa.Text),
        sa.Column('extra_data', sa.Text),
        sa.Column('created_by', sa.String(36), nullable=False),
        sa.Column('updated_by', sa.String(36)),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime, onupdate=sa.func.now()),
        UniqueConstraint('tenant_id', 'company_id', 'entry_number', name='uq_entry_number'),
        CheckConstraint("status IN ('draft', 'posted', 'reversed', 'void')", name='chk_entry_status'),
        CheckConstraint('total_debit = total_credit', name='chk_balanced'),
    )

    # Create financial_journal_entry_lines table
    op.create_table(
        'financial_journal_entry_lines',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('journal_entry_id', sa.String(36), sa.ForeignKey('financial_journal_entries.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('account_id', sa.String(36), sa.ForeignKey('financial_accounts.id'), nullable=False, index=True),
        sa.Column('line_number', sa.Integer, nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('debit_amount', sa.Numeric(18, 2), default=0.00, nullable=False),
        sa.Column('credit_amount', sa.Numeric(18, 2), default=0.00, nullable=False),
        sa.Column('department_id', sa.String(36)),
        sa.Column('project_id', sa.String(36)),
        sa.Column('extra_data', sa.Text),
        CheckConstraint('(debit_amount > 0 AND credit_amount = 0) OR (credit_amount > 0 AND debit_amount = 0)', name='chk_line_amount'),
    )

    # Create financial_invoices table
    op.create_table(
        'financial_invoices',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), nullable=False, index=True),
        sa.Column('company_id', sa.String(36), nullable=False, index=True),
        sa.Column('invoice_number', sa.String(50), nullable=False),
        sa.Column('reference_number', sa.String(100)),
        sa.Column('customer_id', sa.String(36), sa.ForeignKey('financial_customers.id'), nullable=False, index=True),
        sa.Column('invoice_date', sa.Date, nullable=False, index=True),
        sa.Column('due_date', sa.Date, nullable=False, index=True),
        sa.Column('payment_terms_days', sa.Integer, default=30, nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('memo', sa.Text),
        sa.Column('status', sa.String(20), default='draft', nullable=False, index=True),
        sa.Column('subtotal', sa.Numeric(18, 2), default=0.00, nullable=False),
        sa.Column('tax_amount', sa.Numeric(18, 2), default=0.00, nullable=False),
        sa.Column('discount_amount', sa.Numeric(18, 2), default=0.00, nullable=False),
        sa.Column('total_amount', sa.Numeric(18, 2), default=0.00, nullable=False),
        sa.Column('paid_amount', sa.Numeric(18, 2), default=0.00, nullable=False),
        sa.Column('balance_due', sa.Numeric(18, 2), default=0.00, nullable=False),
        sa.Column('last_payment_date', sa.Date),
        sa.Column('currency_code', sa.String(3), default='USD', nullable=False),
        sa.Column('discount_type', sa.String(20)),
        sa.Column('discount_value', sa.Numeric(18, 2), default=0.00),
        sa.Column('shipping_amount', sa.Numeric(18, 2), default=0.00),
        sa.Column('journal_entry_id', sa.String(36), sa.ForeignKey('financial_journal_entries.id')),
        sa.Column('sent_at', sa.DateTime),
        sa.Column('sent_by', sa.String(36)),
        sa.Column('delivered_at', sa.DateTime),
        sa.Column('tags', sa.Text),
        sa.Column('extra_data', sa.Text),
        sa.Column('created_by', sa.String(36), nullable=False),
        sa.Column('updated_by', sa.String(36)),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime, onupdate=sa.func.now()),
        UniqueConstraint('tenant_id', 'company_id', 'invoice_number', name='uq_invoice_number'),
        CheckConstraint("status IN ('draft', 'sent', 'partially_paid', 'paid', 'overdue', 'void', 'cancelled')", name='chk_invoice_status'),
        CheckConstraint('total_amount >= 0', name='chk_total_positive'),
        CheckConstraint('paid_amount >= 0 AND paid_amount <= total_amount', name='chk_paid_amount'),
        CheckConstraint('balance_due >= 0 AND balance_due <= total_amount', name='chk_balance_due'),
    )

    # Create financial_invoice_line_items table
    op.create_table(
        'financial_invoice_line_items',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('invoice_id', sa.String(36), sa.ForeignKey('financial_invoices.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('line_number', sa.Integer, nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('item_id', sa.String(36)),
        sa.Column('item_code', sa.String(50)),
        sa.Column('quantity', sa.Numeric(18, 4), default=1.0000, nullable=False),
        sa.Column('unit_price', sa.Numeric(18, 2), nullable=False),
        sa.Column('line_total', sa.Numeric(18, 2), nullable=False),
        sa.Column('discount_percentage', sa.Numeric(5, 2), default=0.00),
        sa.Column('discount_amount', sa.Numeric(18, 2), default=0.00),
        sa.Column('tax_rate_id', sa.String(36)),
        sa.Column('tax_percentage', sa.Numeric(5, 2), default=0.00),
        sa.Column('tax_amount', sa.Numeric(18, 2), default=0.00, nullable=False),
        sa.Column('is_taxable', sa.Boolean, default=True, nullable=False),
        sa.Column('revenue_account_id', sa.String(36), sa.ForeignKey('financial_accounts.id')),
        sa.Column('department_id', sa.String(36)),
        sa.Column('project_id', sa.String(36)),
        sa.Column('extra_data', sa.Text),
        CheckConstraint('quantity > 0', name='chk_line_quantity_positive'),
        CheckConstraint('unit_price >= 0', name='chk_line_price_positive'),
        CheckConstraint('line_total >= 0', name='chk_line_total_positive'),
    )

    # Create financial_payments table
    op.create_table(
        'financial_payments',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), nullable=False, index=True),
        sa.Column('company_id', sa.String(36), nullable=False, index=True),
        sa.Column('payment_number', sa.String(50), nullable=False),
        sa.Column('reference_number', sa.String(100)),
        sa.Column('customer_id', sa.String(36), sa.ForeignKey('financial_customers.id'), nullable=False, index=True),
        sa.Column('payment_date', sa.Date, nullable=False, index=True),
        sa.Column('payment_method', sa.String(50), nullable=False),
        sa.Column('payment_amount', sa.Numeric(18, 2), nullable=False),
        sa.Column('allocated_amount', sa.Numeric(18, 2), default=0.00, nullable=False),
        sa.Column('unallocated_amount', sa.Numeric(18, 2), default=0.00, nullable=False),
        sa.Column('currency_code', sa.String(3), default='USD', nullable=False),
        sa.Column('check_number', sa.String(50)),
        sa.Column('card_last_four', sa.String(4)),
        sa.Column('transaction_id', sa.String(100)),
        sa.Column('bank_name', sa.String(100)),
        sa.Column('bank_account', sa.String(50)),
        sa.Column('deposit_account_id', sa.String(36), sa.ForeignKey('financial_accounts.id'), nullable=False),
        sa.Column('status', sa.String(20), default='pending', nullable=False, index=True),
        sa.Column('is_cleared', sa.Boolean, default=False, nullable=False),
        sa.Column('cleared_date', sa.Date),
        sa.Column('journal_entry_id', sa.String(36), sa.ForeignKey('financial_journal_entries.id')),
        sa.Column('is_voided', sa.Boolean, default=False, nullable=False),
        sa.Column('voided_at', sa.DateTime),
        sa.Column('voided_by', sa.String(36)),
        sa.Column('void_reason', sa.Text),
        sa.Column('description', sa.Text),
        sa.Column('memo', sa.Text),
        sa.Column('extra_data', sa.Text),
        sa.Column('created_by', sa.String(36), nullable=False),
        sa.Column('updated_by', sa.String(36)),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime, onupdate=sa.func.now()),
        UniqueConstraint('tenant_id', 'company_id', 'payment_number', name='uq_payment_number'),
        CheckConstraint("status IN ('pending', 'cleared', 'allocated', 'partially_allocated', 'voided')", name='chk_payment_status'),
        CheckConstraint('payment_amount > 0', name='chk_payment_amount_positive'),
        CheckConstraint('allocated_amount >= 0 AND allocated_amount <= payment_amount', name='chk_allocated_amount'),
        CheckConstraint('unallocated_amount >= 0 AND unallocated_amount <= payment_amount', name='chk_unallocated_amount'),
    )

    # Create financial_payment_allocations table
    op.create_table(
        'financial_payment_allocations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('payment_id', sa.String(36), sa.ForeignKey('financial_payments.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('invoice_id', sa.String(36), sa.ForeignKey('financial_invoices.id'), nullable=False, index=True),
        sa.Column('allocation_date', sa.Date, nullable=False),
        sa.Column('allocation_amount', sa.Numeric(18, 2), nullable=False),
        sa.Column('is_voided', sa.Boolean, default=False, nullable=False),
        sa.Column('voided_at', sa.DateTime),
        sa.Column('voided_by', sa.String(36)),
        sa.Column('description', sa.Text),
        sa.Column('extra_data', sa.Text),
        sa.Column('created_by', sa.String(36), nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
        CheckConstraint('allocation_amount > 0', name='chk_allocation_amount_positive'),
    )


def downgrade() -> None:
    # Drop tables in reverse order (respect foreign keys)
    op.drop_table('financial_payment_allocations')
    op.drop_table('financial_payments')
    op.drop_table('financial_invoice_line_items')
    op.drop_table('financial_invoices')
    op.drop_table('financial_journal_entry_lines')
    op.drop_table('financial_journal_entries')
    op.drop_table('financial_tax_rates')
    op.drop_table('financial_customers')
    op.drop_table('financial_accounts')
