import datetime
import unittest
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from proteus import Model
from trytond.modules.account.tests.tools import (create_chart,
                                                 create_fiscalyear,
                                                 get_accounts)
from trytond.modules.account_invoice.tests.tools import \
    set_fiscalyear_invoice_sequences
from trytond.modules.company.tests.tools import create_company, get_company
from trytond.modules.stock.exceptions import MoveFutureWarning
from trytond.tests.test_tryton import drop_db
from trytond.tests.tools import activate_modules


class Test(unittest.TestCase):

    def setUp(self):
        drop_db()
        super().setUp()

    def tearDown(self):
        drop_db()
        super().tearDown()

    def test(self):

        # Install sale_invoice_grouping
        config = activate_modules('sale_invoice_grouping_period')

        # Compute dates after module activation
        today = datetime.date.today()
        start_month = today + relativedelta(day=1)
        same_biweekly = today + relativedelta(day=10)
        next_biweekly = today + relativedelta(day=20)
        next_month = today + relativedelta(months=1)
        next_week = today + datetime.timedelta(days=7)
        next_week2 = today + datetime.timedelta(days=14)

        # Create company
        _ = create_company()
        company = get_company()

        # Create sale user
        User = Model.get('res.user')
        Group = Model.get('res.group')
        sale_user = User()
        sale_user.name = 'Sale'
        sale_user.login = 'sale'
        sale_group, = Group.find([('name', '=', 'Sales')])
        sale_user.groups.append(sale_group)
        sale_user.save()

        # Create stock user
        stock_user = User()
        stock_user.name = 'Stock'
        stock_user.login = 'stock'
        stock_group, = Group.find([('name', '=', 'Stock')])
        stock_user.groups.append(stock_group)
        stock_user.save()

        # Create account user
        account_user = User()
        account_user.name = 'Account'
        account_user.login = 'account'
        account_group, = Group.find([('name', '=', 'Accounting')])
        account_user.groups.append(account_group)
        account_user.save()

        # Create fiscal year
        fiscalyear = set_fiscalyear_invoice_sequences(
            create_fiscalyear(company))
        fiscalyear.click('create_period')

        # Create chart of accounts
        _ = create_chart(company)
        accounts = get_accounts(company)
        revenue = accounts['revenue']
        expense = accounts['expense']

        # Create parties
        Party = Model.get('party.party')
        customer = Party(name='Customer')
        customer.save()
        customer_daily = Party(name='Customer Daily')
        customer_daily.sale_invoice_grouping_method = 'standard'
        customer_daily.sale_invoice_grouping_period = 'daily'
        customer_daily.save()
        customer_weekly = Party(name='Customer BiWeekly')
        customer_weekly.sale_invoice_grouping_method = 'standard'
        customer_weekly.sale_invoice_grouping_period = 'weekly-0'
        customer_weekly.save()
        customer_biweekly = Party(name='Customer BiWeekly')
        customer_biweekly.sale_invoice_grouping_method = 'standard'
        customer_biweekly.sale_invoice_grouping_period = 'biweekly'
        customer_biweekly.save()
        customer_monthly = Party(name='Customer Monthly')
        customer_monthly.sale_invoice_grouping_method = 'standard'
        customer_monthly.sale_invoice_grouping_period = 'monthly'
        customer_monthly.save()
        customer_weekly_break = Party(name='Customer Weekly 0 break')
        customer_weekly_break.sale_invoice_grouping_method = 'standard'
        customer_weekly_break.sale_invoice_grouping_period = 'weekly-0-break'
        customer_weekly_break.save()

        # Create account category
        ProductCategory = Model.get('product.category')
        account_category = ProductCategory(name="Account Category")
        account_category.accounting = True
        account_category.account_expense = expense
        account_category.account_revenue = revenue
        account_category.save()

        # Create product
        ProductUom = Model.get('product.uom')
        unit, = ProductUom.find([('name', '=', 'Unit')])
        ProductTemplate = Model.get('product.template')
        template = ProductTemplate()
        template.name = 'product'
        template.default_uom = unit
        template.type = 'goods'
        template.salable = True
        template.list_price = Decimal('10')
        template.account_category = account_category
        template.save()
        product, = template.products
        template = ProductTemplate()
        template.name = 'product2'
        template.default_uom = unit
        template.type = 'goods'
        template.salable = True
        template.list_price = Decimal('10')
        template.account_category = account_category
        template.save()
        product2, = template.products

        # Create an Inventory
        Inventory = Model.get('stock.inventory')
        Location = Model.get('stock.location')
        storage, = Location.find([
            ('code', '=', 'STO'),
        ])
        inventory = Inventory()
        inventory.location = storage
        inventory_line = inventory.lines.new(product=product)
        inventory_line.quantity = 100.0
        inventory_line.expected_quantity = 0.0
        inventory_line2 = inventory.lines.new(product=product2)
        inventory_line2.quantity = 100.0
        inventory_line2.expected_quantity = 0.0
        inventory.click('confirm')
        self.assertEqual(inventory.state, 'done')

        # Sale some products
        config.user = sale_user.id
        Sale = Model.get('sale.sale')
        sale = Sale()
        sale.party = customer
        sale.invoice_method = 'order'
        sale_line = sale.lines.new()
        sale_line.product = product
        sale_line.quantity = 2.0
        sale.click('quote')
        sale.click('confirm')
        self.assertEqual(sale.state, 'processing')

        # Make another sale
        sale, = Sale.duplicate([sale])
        sale.click('quote')
        sale.click('confirm')
        self.assertEqual(sale.state, 'processing')

        # Check the invoices
        config.user = account_user.id
        Invoice = Model.get('account.invoice')
        invoices = Invoice.find([('party', '=', customer.id)])
        self.assertEqual(len(invoices), 2)
        invoice = invoices[0]
        self.assertEqual(invoice.type, 'out')
        invoice.click('post')
        self.assertEqual(invoice.state, 'posted')

        # Now we'll use the same scenario with the daily customer
        config.user = sale_user.id
        sale = Sale()
        sale.party = customer_daily
        sale.sale_date = today
        sale.invoice_method = 'order'
        sale_line = sale.lines.new()
        sale_line.product = product
        sale_line.quantity = 1.0
        sale.click('quote')
        sale.click('confirm')
        self.assertEqual(sale.state, 'processing')

        # Make another sale
        sale = Sale()
        sale.party = customer_daily
        sale.sale_date = today
        sale.invoice_method = 'order'
        sale_line = sale.lines.new()
        sale_line.product = product
        sale_line.quantity = 2.0
        sale.click('quote')
        sale.click('confirm')
        self.assertEqual(sale.state, 'processing')

        # Make another sale
        sale = Sale()
        sale.party = customer_daily
        sale.sale_date = today + relativedelta(day=1)
        sale.invoice_method = 'order'
        sale_line = sale.lines.new()
        sale_line.product = product
        sale_line.quantity = 3.0
        sale.click('quote')
        sale.click('confirm')
        self.assertEqual(sale.state, 'processing')

        # Check the invoices
        config.user = account_user.id
        invoices = Invoice.find([
            ('party', '=', customer_daily.id),
            ('start_date', '=', today),
            ('state', '=', 'draft'),
        ])
        self.assertEqual(len(invoices), 1)
        invoice, = invoices
        self.assertEqual(invoice.start_date, today)
        self.assertEqual(len(invoice.lines), 3)
        self.assertEqual(invoice.lines[0].quantity, 1.0)
        self.assertEqual(invoice.lines[1].quantity, 2.0)
        self.assertEqual(invoice.lines[2].quantity, 3.0)

        # Now we'll use the same scenario with the monthly customer
        config.user = sale_user.id
        sale = Sale()
        sale.party = customer_monthly
        sale.sale_date = start_month
        sale.invoice_method = 'order'
        sale_line = sale.lines.new()
        sale_line.product = product
        sale_line.quantity = 1.0
        sale.click('quote')
        sale.click('confirm')
        self.assertEqual(sale.state, 'processing')

        # Make another sale (weekly)
        Warning = Model.get('res.user.warning')
        sale = Sale()
        sale.party = customer_weekly
        sale.invoice_method = 'shipment'
        sale_line = sale.lines.new()
        sale_line.product = product
        sale_line.quantity = 2.0
        sale_line = sale.lines.new()
        sale_line.product = product2
        sale_line.quantity = 2.0
        sale.click('quote')
        sale.click('confirm')
        self.assertEqual(sale.state, 'processing')
        shipment, = sale.shipments
        config.user = stock_user.id
        move1, move2 = shipment.inventory_moves
        move1.quantity = Decimal(0)
        move1.save()
        shipment.effective_date = next_week
        shipment.save()
        shipment.click('assign_try')

        with self.assertRaises(MoveFutureWarning):
            try:
                shipment.click('pick')
            except MoveFutureWarning as warning:
                _, (key, *_) = warning.args
                raise

        Warning = Model.get('res.user.warning')
        Warning.skip(key, True, config.context)
        shipment.click('pick')
        shipment.click('pack')

        with self.assertRaises(MoveFutureWarning):
            try:
                shipment.click('do')
            except MoveFutureWarning as warning:
                _, (key, *_) = warning.args
                raise

        Warning.skip(key, True, config.context)
        shipment.click('do')
        self.assertEqual(shipment.state, 'done')
        config.user = sale_user.id
        sale.reload()
        shipment, _ = sale.shipments
        config.user = stock_user.id
        shipment.effective_date = next_week2
        shipment.save()
        shipment.click('assign_try')

        with self.assertRaises(MoveFutureWarning):
            try:
                shipment.click('pick')
            except MoveFutureWarning as warning:
                _, (key, *_) = warning.args
                raise

        Warning.skip(key, True, config.context)
        shipment.click('pick')
        shipment.click('pack')

        with self.assertRaises(MoveFutureWarning):
            try:
                shipment.click('do')
            except MoveFutureWarning as warning:
                _, (key, *_) = warning.args
                raise

        Warning.skip(key, True, config.context)
        shipment.click('do')
        self.assertEqual(shipment.state, 'done')
        config.user = sale_user.id
        sale.reload()
        self.assertEqual(len(sale.invoices), 2)
        invoice1, invoice2 = sale.invoices
        self.assertNotEqual(invoice1.start_date, invoice2.start_date)

        # Make another sale
        config.user = sale_user.id
        sale = Sale()
        sale.party = customer_monthly
        sale.sale_date = same_biweekly
        sale.invoice_method = 'order'
        sale_line = sale.lines.new()
        sale_line.product = product
        sale_line.quantity = 2.0
        sale.click('quote')
        sale.click('confirm')
        self.assertEqual(sale.state, 'processing')

        # Make another sale
        sale = Sale()
        sale.party = customer_monthly
        sale.sale_date = next_biweekly
        sale.invoice_method = 'order'
        sale_line = sale.lines.new()
        sale_line.product = product
        sale_line.quantity = 3.0
        sale.click('quote')
        sale.click('confirm')
        self.assertEqual(sale.state, 'processing')

        # Check the invoices
        config.user = account_user.id
        invoices = Invoice.find([
            ('party', '=', customer_monthly.id),
            ('state', '=', 'draft'),
        ])
        self.assertEqual(len(invoices), 1)
        invoice, = invoices
        self.assertEqual(invoice.start_date, start_month)
        self.assertEqual(len(invoice.lines), 3)
        self.assertEqual(invoice.lines[0].quantity, 1.0)
        self.assertEqual(invoice.lines[1].quantity, 2.0)
        self.assertEqual(invoice.lines[2].quantity, 3.0)

        # Create a sale for the next month
        config.user = sale_user.id
        sale = Sale()
        sale.party = customer_monthly
        sale.sale_date = next_month
        sale.invoice_method = 'order'
        sale_line = sale.lines.new()
        sale_line.product = product
        sale_line.quantity = 4.0
        sale.click('quote')
        sale.click('confirm')
        self.assertEqual(sale.state, 'processing')

        # A new invoice is created
        config.user = account_user.id
        invoices = Invoice.find([
            ('party', '=', customer_monthly.id),
            ('state', '=', 'draft'),
        ])
        self.assertEqual(len(invoices), 2)

        # Now we'll use the same scenario with the biweekly customer
        config.user = sale_user.id
        sale = Sale()
        sale.party = customer_biweekly
        sale.sale_date = start_month
        sale.invoice_method = 'order'
        sale_line = sale.lines.new()
        sale_line.product = product
        sale_line.quantity = 1.0
        sale.click('quote')
        sale.click('confirm')
        self.assertEqual(sale.state, 'processing')

        # Make another sale
        sale = Sale()
        sale.party = customer_biweekly
        sale.sale_date = same_biweekly
        sale.invoice_method = 'order'
        sale_line = sale.lines.new()
        sale_line.product = product
        sale_line.quantity = 2.0
        sale.click('quote')
        sale.click('confirm')
        self.assertEqual(sale.state, 'processing')

        # Check the invoices
        config.user = account_user.id
        invoices = Invoice.find([
            ('party', '=', customer_biweekly.id),
            ('state', '=', 'draft'),
        ])
        self.assertEqual(len(invoices), 1)
        invoice, = invoices
        self.assertEqual(len(invoice.lines), 2)
        self.assertEqual(invoice.lines[0].quantity, 1.0)
        self.assertEqual(invoice.lines[1].quantity, 2.0)

        # Create a sale for the next biweekly
        config.user = sale_user.id
        sale = Sale()
        sale.party = customer_biweekly
        sale.sale_date = next_biweekly
        sale.invoice_method = 'order'
        sale_line = sale.lines.new()
        sale_line.product = product
        sale_line.quantity = 4.0
        sale.click('quote')
        sale.click('confirm')
        self.assertEqual(sale.state, 'processing')

        # A new invoice is created
        config.user = account_user.id
        invoices = Invoice.find([
            ('party', '=', customer_biweekly.id),
            ('state', '=', 'draft'),
        ])
        self.assertEqual(len(invoices), 2)

        # Create a sale for the next weekly break
        config.user = sale_user.id
        sale = Sale()
        sale.party = customer_weekly_break
        sale.sale_date = datetime.date(2022, 6, 30)
        sale.invoice_method = 'order'
        sale_line = sale.lines.new()
        sale_line.product = product
        sale_line.quantity = 4.0
        sale.click('quote')
        sale.click('confirm')
        self.assertEqual(sale.state, 'processing')
        invoices = sale.invoices
        sale2 = Sale()
        sale2.party = customer_weekly_break
        sale2.sale_date = datetime.date(2022, 7, 2)
        sale2.invoice_method = 'order'
        sale_line = sale2.lines.new()
        sale_line.product = product
        sale_line.quantity = 4.0
        sale2.click('quote')
        sale2.click('confirm')
        self.assertEqual(sale2.state, 'processing')
        invoices2 = sale2.invoices
        sale3 = Sale()
        sale3.party = customer_weekly_break
        sale3.sale_date = datetime.date(2022, 7, 5)
        sale3.invoice_method = 'order'
        sale_line = sale3.lines.new()
        sale_line.product = product
        sale_line.quantity = 4.0
        sale3.click('quote')
        sale3.click('confirm')
        self.assertEqual(sale3.state, 'processing')
        invoices3 = sale3.invoices

        # Check the invoices
        config.user = account_user.id
        self.assertEqual(invoices[0].start_date, datetime.date(2022, 6, 27))

        self.assertEqual(invoices[0].end_date, datetime.date(2022, 6, 30))
        self.assertEqual(invoices2[0].start_date, datetime.date(2022, 7, 1))

        self.assertEqual(invoices2[0].end_date, datetime.date(2022, 7, 3))
        self.assertEqual(invoices3[0].start_date, datetime.date(2022, 7, 4))

        self.assertEqual(invoices3[0].end_date, datetime.date(2022, 7, 10))
