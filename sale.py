#This file is part of Tryton.  The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
from dateutil.relativedelta import relativedelta
import datetime
import calendar

from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction

__all__ = ['Sale']
__metaclass__ = PoolMeta


class Sale:
    __name__ = 'sale.sale'

    def _get_grouped_invoice_order(self):
        res = super(Sale, self)._get_grouped_invoice_order()
        if not res:
            return [('invoice_date', 'DESC')]
        return res

    def _get_grouped_invoice_domain(self, invoice):
        invoice_domain = super(Sale, self)._get_grouped_invoice_domain(invoice)
        minimum_date = self._get_minimum_invoice_date()
        if minimum_date:
            invoice_domain.append(
                ('sale_date', '>=', minimum_date)
                )
        maximum_date = self._get_maximum_invoice_date()
        if maximum_date:
            invoice_domain.append(
                ('sale_date', '<=', maximum_date)
                )
        return invoice_domain

    def _get_minimum_invoice_date(self):
        period = self.party.sale_invoice_grouping_period
        if not period:
            return
        if period == 'monthly':
            interval_date = relativedelta(months=1)
            min_date = datetime.date(self.sale_date.year, self.sale_date.month,
                1)
        elif period == 'biweekly':
            interval_date = relativedelta(weeks=2)
            min_date = datetime.date(self.sale_date.year, self.sale_date.month,
                1 if self.sale_date.day <= 15 else 15)

        return max(min_date, (self.sale_date - interval_date))

    def _get_maximum_invoice_date(self):
        period = self.party.sale_invoice_grouping_period
        if not period:
            return
        _, last_day = calendar.monthrange(self.sale_date.year,
            self.sale_date.month)
        if period == 'monthly':
            interval_date = relativedelta(months=1)
            max_date = datetime.date(self.sale_date.year, self.sale_date.month,
                last_day)
        elif period == 'biweekly':
            interval_date = relativedelta(weeks=2)
            max_date = datetime.date(self.sale_date.year, self.sale_date.month,
                15 if self.sale_date.day <= 15 else last_day)

        return min(max_date, (self.sale_date + interval_date))

    def _get_invoice_sale(self, invoice_type):
        pool = Pool()
        Lang = pool.get('ir.lang')
        invoice = super(Sale, self)._get_invoice_sale(invoice_type)
        period = self.party.sale_invoice_grouping_period
        if period:
            for code in [Transaction().language, 'en_US']:
                langs = Lang.search([
                        ('code', '=', code),
                        ])
                if langs:
                    break
            lang, = langs
            start_date = Lang.strftime(self._get_minimum_invoice_date(),
                lang.code, lang.date)
            end_date = Lang.strftime(self._get_maximum_invoice_date(),
                lang.code, lang.date)
            invoice.description = "%s - %s" % (start_date, end_date)
        return invoice
