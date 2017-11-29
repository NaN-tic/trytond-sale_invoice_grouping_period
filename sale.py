# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
import datetime
from dateutil.relativedelta import relativedelta
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction

__all__ = ['Sale']


class Sale:
    __metaclass__ = PoolMeta
    __name__ = 'sale.sale'

    def _get_grouped_invoice_order(self):
        res = super(Sale, self)._get_grouped_invoice_order()

        if self.invoice_grouping_method == 'period':
            return [('invoice_date', 'DESC')]
        return res

    def _get_grouped_invoice_date(self):
        date = None
        if self.invoice_method == 'shipment':
            for line in self.lines:
                date = line.shipping_date
                break
        if date is None:
            date = self.sale_date
        return date

    def _get_grouped_invoice_domain(self, invoice):
        invoice_domain = super(Sale, self)._get_grouped_invoice_domain(invoice)
        period = self.party.sale_invoice_grouping_period
        if self.invoice_grouping_method == 'standard' and period:
            date = self._get_grouped_invoice_date()
            start, end = self._get_invoice_dates(date,
                self.party.sale_invoice_grouping_period)
            invoice_domain += [
                ('start_date', '=', start),
                ('end_date', '=', end),
                ]
        return invoice_domain

    @staticmethod
    def _get_invoice_dates(date, period):
        if period == 'monthly':
            interval = relativedelta(months=1, days=-1)
            start = datetime.date(date.year, date.month, 1)
        elif period == 'biweekly':
            if date.day <= 15:
                start_day = 1
                interval = relativedelta(day=15)
            else:
                start_day = 16
                interval = relativedelta(months=1, day=1, days=-1)
            start = datetime.date(date.year, date.month, start_day)
        elif period == 'ten-days':
            if date.day <= 10:
                start_day = 1
                interval = relativedelta(day=10)
            elif date.day <= 20:
                start_day = 11
                interval = relativedelta(day=20)
            else:
                start_day = 21
                interval = relativedelta(months=1, day=1, days=-1)
            start = datetime.date(date.year, date.month, start_day)
        elif period.startswith('weekly'):
            diff = date.weekday() - int(period[-1])
            if diff < 0:
                diff = 7 + diff
            start = date - relativedelta(days=diff)
            interval = relativedelta(days=6)
        elif period == 'daily':
            start = datetime.date.today()
            interval = relativedelta(day=0)
        return start, start + interval

    def _get_invoice_sale(self):
        Lang = Pool().get('ir.lang')

        invoice = super(Sale, self)._get_invoice_sale()

        period = self.party.sale_invoice_grouping_period
        if self.invoice_grouping_method == 'standard' and period:
            for code in [Transaction().language, 'en_US']:
                langs = Lang.search([
                        ('code', '=', code),
                        ], limit=1)
                if langs:
                    break
            lang, = langs
            date = self._get_grouped_invoice_date()
            start, end = self._get_invoice_dates(date,
                self.party.sale_invoice_grouping_period)
            invoice.start_date = start
            invoice.end_date = end
            start, end = [Lang.strftime(x, lang.code, lang.date) for x in
                (start, end)]
            invoice.description = '%s - %s' % (start, end)
        return invoice
