# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from sql import Cast, Literal
from sql.aggregate import Max
from sql.functions import Substring, Position
from sql.operators import Like

from trytond.pool import Pool, PoolMeta
from trytond.model import fields
from .party import GROUPING_PERIODS

__all__ = ['Invoice']


class Invoice:
    __name__ = 'account.invoice'
    __metaclass__ = PoolMeta

    sale_date = fields.Function(fields.Date('Sale Date'),
        'get_sale_date', searcher='search_sale_date')
    invoice_grouping_period = fields.Function(fields.Selection(
            GROUPING_PERIODS, 'Invoice Grouping Period'),
        'get_invoice_grouping_period',
        searcher='search_invoice_grouping_period')

    def get_sale_date(self, name):
        pool = Pool()
        SaleLine = pool.get('sale.line')
        if self.origin and isinstance(self.origin, SaleLine):
            return self.origin.sale.sale_date

    @classmethod
    def search_sale_date(cls, name, clause):
        pool = Pool()
        InvoiceLine = pool.get('account.invoice.line')
        Sale = pool.get('sale.sale')
        SaleLine = pool.get('sale.line')
        _, operator, value = clause
        Operator = fields.SQL_OPERATORS[operator]
        table = InvoiceLine.__table__()
        sale = Sale.__table__()
        line = SaleLine.__table__()

        value = cls.sale_date.sql_format(value)

        query = table.join(line,
            condition=(line.id == Cast(Substring(table.origin,
                    Position(',', table.origin) + Literal(1)),
                SaleLine.id.sql_type().base))
            ).join(sale, condition=(sale.id == line.sale)
                ).select(table.invoice,
                    where=(Like(table.origin, Literal('sale.line,%'))),
                    group_by=(table.invoice),
                    having=Operator(Max(sale.sale_date), value)
                    )
        return [('id', 'in', query)]

    def get_invoice_grouping_period(self, name):
        if self.party:
            return self.party.sale_invoice_grouping_period

    @classmethod
    def search_invoice_grouping_period(cls, name, clause):
        return [('party.sale_invoice_grouping_period',) + tuple(clause[1:])]
