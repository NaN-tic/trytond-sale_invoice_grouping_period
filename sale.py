# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
import datetime
from dateutil.relativedelta import relativedelta, MO, TU, TH, WE, FR, SA, SU
from trytond.model import fields
from trytond.pool import PoolMeta
from trytond.pyson import Eval

__all__ = ['Sale', 'SaleLine']


class Sale(metaclass=PoolMeta):
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
                if line.type != 'line':
                    continue
                quantity = (line._get_invoice_line_quantity() - line._get_invoiced_quantity())
                if quantity:
                    date = line.invoice_date
                    break
        if date is None:
            date = self.sale_date
        return date

    def _get_grouped_invoice_domain(self, invoice):
        invoice_domain = super(Sale, self)._get_grouped_invoice_domain(invoice)
        period = self.party.sale_invoice_grouping_period
        # invoice_grouping_method is standard, shipment_address... find invoices
        if self.invoice_grouping_method != None and period:
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
            if period.endswith('break'):
                diff = date.weekday() - int(period[-7])
            else:
                diff = date.weekday() - int(period[-1])
            if diff < 0:
                diff = 7 + diff
            start = date - relativedelta(days=diff)
            interval = relativedelta(days=6)
            if period.endswith('break'):
                if start.month != (start + interval).month:
                    weekday_num = period[:-6][-1:]
                    if weekday_num == '0':
                        weekday = MO(-1)
                    elif weekday_num == '1':
                        weekday = TU(-1)
                    elif weekday_num == '2':
                        weekday = TH(-1)
                    elif weekday_num == '3':
                        weekday = WE(-1)
                    elif weekday_num == '4':
                        weekday = FR(-1)
                    elif weekday_num == '5':
                        weekday = SA(-1)
                    elif weekday_num == '6':
                        weekday = SU(-1)
                    last_day = start + relativedelta(day=31, weekday=weekday)
                    if last_day < datetime.date.today():
                        start = start + relativedelta(day=31, months=1, weekday=weekday)
                        interval = relativedelta(day=31, months=1, weekday=weekday)
                    else:
                        start = last_day
                        interval = relativedelta(day=31, months=1, weekday=weekday)
        elif period == 'daily':
            start = datetime.date.today()
            interval = relativedelta(day=0)
        return start, start + interval

    def _get_invoice_sale(self):
        invoice = super(Sale, self)._get_invoice_sale()

        period = self.party.sale_invoice_grouping_period
        # invoice_grouping_method is standard, shipment_address... find invoices
        if self.invoice_grouping_method != None and period:
            date = self._get_grouped_invoice_date()
            start, end = self._get_invoice_dates(date,
                self.party.sale_invoice_grouping_period)
            invoice.start_date = start
            invoice.end_date = end
        return invoice


class SaleLine(metaclass=PoolMeta):
    __name__ = 'sale.line'
    invoice_date = fields.Function(fields.Date('Invoice Date',
            states={
                'invisible': Eval('type') != 'line',
                },
            depends=['type']),
        'get_invoice_date')

    @classmethod
    def get_invoice_date(cls, lines, name):
        res = dict((l.id, None) for l in lines)
        for line in lines:
            dates = filter(
                None, (m.effective_date or m.planned_date for m in line.moves
                    if m.state != 'cancelled' and not m.invoice_lines and m.quantity > 0))
            res[line.id] = min(dates, default=None)
        return res
