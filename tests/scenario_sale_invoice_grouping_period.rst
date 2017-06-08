=====================================
Sale Invoice Grouping Period Scenario
=====================================

Imports::

    >>> import datetime
    >>> from dateutil.relativedelta import relativedelta
    >>> from decimal import Decimal
    >>> from proteus import Model, Wizard
    >>> from trytond.tests.tools import activate_modules
    >>> from trytond.modules.company.tests.tools import create_company, \
    ...     get_company
    >>> from trytond.modules.account.tests.tools import create_fiscalyear, \
    ...     create_chart, get_accounts
    >>> from trytond.modules.account_invoice.tests.tools import \
    ...     set_fiscalyear_invoice_sequences
    >>> today = datetime.date.today()
    >>> start_month = today + relativedelta(day=1)
    >>> same_biweekly = today + relativedelta(day=10)
    >>> next_biweekly = today + relativedelta(day=20)
    >>> next_month = today + relativedelta(months=1)

Install sale_invoice_grouping::

    >>> config = activate_modules('sale_invoice_grouping_period')

Create company::

    >>> _ = create_company()
    >>> company = get_company()

Create sale user::

    >>> User = Model.get('res.user')
    >>> Group = Model.get('res.group')
    >>> sale_user = User()
    >>> sale_user.name = 'Sale'
    >>> sale_user.login = 'sale'
    >>> sale_user.main_company = company
    >>> sale_group, = Group.find([('name', '=', 'Sales')])
    >>> sale_user.groups.append(sale_group)
    >>> sale_user.save()

Create account user::

    >>> account_user = User()
    >>> account_user.name = 'Account'
    >>> account_user.login = 'account'
    >>> account_user.main_company = company
    >>> account_group, = Group.find([('name', '=', 'Account')])
    >>> account_user.groups.append(account_group)
    >>> account_user.save()

Create fiscal year::

    >>> fiscalyear = set_fiscalyear_invoice_sequences(
    ...     create_fiscalyear(company))
    >>> fiscalyear.click('create_period')

Create chart of accounts::

    >>> _ = create_chart(company)
    >>> accounts = get_accounts(company)
    >>> revenue = accounts['revenue']
    >>> expense = accounts['expense']

Create parties::

    >>> Party = Model.get('party.party')
    >>> customer = Party(name='Customer')
    >>> customer.save()
    >>> customer_daily = Party(name='Customer Daily')
    >>> customer_daily.sale_invoice_grouping_method = 'standard'
    >>> customer_daily.sale_invoice_grouping_period = 'daily'
    >>> customer_daily.save()
    >>> customer_biweekly = Party(name='Customer BiWeekly')
    >>> customer_biweekly.sale_invoice_grouping_method = 'standard'
    >>> customer_biweekly.sale_invoice_grouping_period = 'biweekly'
    >>> customer_biweekly.save()
    >>> customer_monthly = Party(name='Customer Monthly')
    >>> customer_monthly.sale_invoice_grouping_method = 'standard'
    >>> customer_monthly.sale_invoice_grouping_period = 'monthly'
    >>> customer_monthly.save()

Create product::

    >>> ProductUom = Model.get('product.uom')
    >>> unit, = ProductUom.find([('name', '=', 'Unit')])
    >>> ProductTemplate = Model.get('product.template')
    >>> Product = Model.get('product.product')
    >>> product = Product()
    >>> template = ProductTemplate()
    >>> template.name = 'product'
    >>> template.default_uom = unit
    >>> template.type = 'goods'
    >>> template.purchasable = True
    >>> template.salable = True
    >>> template.list_price = Decimal('10')
    >>> template.cost_price = Decimal('5')
    >>> template.cost_price_method = 'fixed'
    >>> template.account_expense = expense
    >>> template.account_revenue = revenue
    >>> template.save()
    >>> product.template = template
    >>> product.save()

Sale some products::

    >>> config.user = sale_user.id
    >>> Sale = Model.get('sale.sale')
    >>> sale = Sale()
    >>> sale.party = customer
    >>> sale.invoice_method = 'order'
    >>> sale_line = sale.lines.new()
    >>> sale_line.product = product
    >>> sale_line.quantity = 2.0
    >>> sale.click('quote')
    >>> sale.click('confirm')
    >>> sale.click('process')
    >>> sale.state
    u'processing'

Make another sale::

    >>> sale, = Sale.duplicate([sale])
    >>> sale.click('quote')
    >>> sale.click('confirm')
    >>> sale.click('process')
    >>> sale.state
    u'processing'

Check the invoices::

    >>> config.user = account_user.id
    >>> Invoice = Model.get('account.invoice')
    >>> invoices = Invoice.find([('party', '=', customer.id)])
    >>> len(invoices)
    2
    >>> invoice = invoices[0]
    >>> invoice.type
    u'out'
    >>> invoice.click('post')
    >>> invoice.state
    u'posted'

Now we'll use the same scenario with the daily customer::

    >>> config.user = sale_user.id
    >>> sale = Sale()
    >>> sale.party = customer_daily
    >>> sale.sale_date = today
    >>> sale.invoice_method = 'order'
    >>> sale_line = sale.lines.new()
    >>> sale_line.product = product
    >>> sale_line.quantity = 1.0
    >>> sale.click('quote')
    >>> sale.click('confirm')
    >>> sale.click('process')
    >>> sale.state
    u'processing'

Make another sale::

    >>> sale = Sale()
    >>> sale.party = customer_daily
    >>> sale.sale_date = today
    >>> sale.invoice_method = 'order'
    >>> sale_line = sale.lines.new()
    >>> sale_line.product = product
    >>> sale_line.quantity = 2.0
    >>> sale.click('quote')
    >>> sale.click('confirm')
    >>> sale.click('process')
    >>> sale.state
    u'processing'

Make another sale::

    >>> sale = Sale()
    >>> sale.party = customer_daily
    >>> sale.sale_date = today + relativedelta(day=1)
    >>> sale.invoice_method = 'order'
    >>> sale_line = sale.lines.new()
    >>> sale_line.product = product
    >>> sale_line.quantity = 3.0
    >>> sale.click('quote')
    >>> sale.click('confirm')
    >>> sale.click('process')
    >>> sale.state
    u'processing'

Check the invoices::

    >>> config.user = account_user.id
    >>> invoices = Invoice.find([
    ...     ('party', '=', customer_daily.id),
    ...     ('sale_date', '=', today),
    ...     ('state', '=', 'draft'),
    ...     ])
    >>> len(invoices)
    1
    >>> invoice, = invoices
    >>> invoice.sale_date == today
    True
    >>> len(invoice.lines)
    2
    >>> invoice.lines[0].quantity
    1.0
    >>> invoice.lines[1].quantity
    2.0

Create a sale for the next day::

    >>> config.user = sale_user.id
    >>> sale = Sale()
    >>> sale.party = customer_daily
    >>> sale.sale_date = today + datetime.timedelta(days=1)
    >>> sale.invoice_method = 'order'
    >>> sale_line = sale.lines.new()
    >>> sale_line.product = product
    >>> sale_line.quantity = 4.0
    >>> sale.click('quote')
    >>> sale.click('confirm')
    >>> sale.click('process')
    >>> sale.state
    u'processing'

A new invoice is created::

    >>> config.user = account_user.id
    >>> invoices = Invoice.find([
    ...     ('party', '=', customer_daily.id),
    ...     ('sale_date', '>=', today),
    ...     ('state', '=', 'draft'),
    ...     ])
    >>> len(invoices)
    2

Now we'll use the same scenario with the monthly customer::

    >>> config.user = sale_user.id
    >>> sale = Sale()
    >>> sale.party = customer_monthly
    >>> sale.sale_date = start_month
    >>> sale.invoice_method = 'order'
    >>> sale_line = sale.lines.new()
    >>> sale_line.product = product
    >>> sale_line.quantity = 1.0
    >>> sale.click('quote')
    >>> sale.click('confirm')
    >>> sale.click('process')
    >>> sale.state
    u'processing'

Make another sale::

    >>> sale = Sale()
    >>> sale.party = customer_monthly
    >>> sale.sale_date = same_biweekly
    >>> sale.invoice_method = 'order'
    >>> sale_line = sale.lines.new()
    >>> sale_line.product = product
    >>> sale_line.quantity = 2.0
    >>> sale.click('quote')
    >>> sale.click('confirm')
    >>> sale.click('process')
    >>> sale.state
    u'processing'

Make another sale::

    >>> sale = Sale()
    >>> sale.party = customer_monthly
    >>> sale.sale_date = next_biweekly
    >>> sale.invoice_method = 'order'
    >>> sale_line = sale.lines.new()
    >>> sale_line.product = product
    >>> sale_line.quantity = 3.0
    >>> sale.click('quote')
    >>> sale.click('confirm')
    >>> sale.click('process')
    >>> sale.state
    u'processing'

Check the invoices::

    >>> config.user = account_user.id
    >>> invoices = Invoice.find([
    ...     ('party', '=', customer_monthly.id),
    ...     ('state', '=', 'draft'),
    ...     ])
    >>> len(invoices)
    1
    >>> invoice, = invoices
    >>> invoice.sale_date == next_biweekly
    True
    >>> len(invoice.lines)
    3
    >>> invoice.lines[0].quantity
    1.0
    >>> invoice.lines[1].quantity
    2.0
    >>> invoice.lines[2].quantity
    3.0

Create a sale for the next month::

    >>> config.user = sale_user.id
    >>> sale = Sale()
    >>> sale.party = customer_monthly
    >>> sale.sale_date = next_month
    >>> sale.invoice_method = 'order'
    >>> sale_line = sale.lines.new()
    >>> sale_line.product = product
    >>> sale_line.quantity = 4.0
    >>> sale.click('quote')
    >>> sale.click('confirm')
    >>> sale.click('process')
    >>> sale.state
    u'processing'

A new invoice is created::

    >>> config.user = account_user.id
    >>> invoices = Invoice.find([
    ...     ('party', '=', customer_monthly.id),
    ...     ('state', '=', 'draft'),
    ...     ])
    >>> len(invoices)
    2

Now we'll use the same scenario with the biweekly customer::

    >>> config.user = sale_user.id
    >>> sale = Sale()
    >>> sale.party = customer_biweekly
    >>> sale.sale_date = start_month
    >>> sale.invoice_method = 'order'
    >>> sale_line = sale.lines.new()
    >>> sale_line.product = product
    >>> sale_line.quantity = 1.0
    >>> sale.click('quote')
    >>> sale.click('confirm')
    >>> sale.click('process')
    >>> sale.state
    u'processing'

Make another sale::

    >>> sale = Sale()
    >>> sale.party = customer_biweekly
    >>> sale.sale_date = same_biweekly
    >>> sale.invoice_method = 'order'
    >>> sale_line = sale.lines.new()
    >>> sale_line.product = product
    >>> sale_line.quantity = 2.0
    >>> sale.click('quote')
    >>> sale.click('confirm')
    >>> sale.click('process')
    >>> sale.state
    u'processing'

Check the invoices::

    >>> config.user = account_user.id
    >>> invoices = Invoice.find([
    ...     ('party', '=', customer_biweekly.id),
    ...     ('state', '=', 'draft'),
    ...     ])
    >>> len(invoices)
    1
    >>> invoice, = invoices
    >>> len(invoice.lines)
    2
    >>> invoice.lines[0].quantity
    1.0
    >>> invoice.lines[1].quantity
    2.0

Create a sale for the next biweekly::

    >>> config.user = sale_user.id
    >>> sale = Sale()
    >>> sale.party = customer_biweekly
    >>> sale.sale_date = next_biweekly
    >>> sale.invoice_method = 'order'
    >>> sale_line = sale.lines.new()
    >>> sale_line.product = product
    >>> sale_line.quantity = 4.0
    >>> sale.click('quote')
    >>> sale.click('confirm')
    >>> sale.click('process')
    >>> sale.state
    u'processing'

A new invoice is created::

    >>> config.user = account_user.id
    >>> invoices = Invoice.find([
    ...     ('party', '=', customer_biweekly.id),
    ...     ('state', '=', 'draft'),
    ...     ])
    >>> len(invoices)
    2
