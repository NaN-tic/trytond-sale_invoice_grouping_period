# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import fields
from trytond.pool import PoolMeta
from trytond.pyson import Eval

__all__ = ['Party']

GROUPING_PERIODS = [
    (None, 'Standard'),
    ('daily', 'Daily'),
    ('biweekly', 'Biweekly'),
    ('monthly', 'Monthly'),
    ]


class Party:
    __name__ = 'party.party'
    __metaclass__ = PoolMeta

    sale_invoice_grouping_period = fields.Property(fields.Selection(
            GROUPING_PERIODS, 'Sale Invoice Grouping Period', states={
                'invisible': Eval('sale_invoice_grouping_method').in_(
                    [None, 'standalone']),
                }, depends=['sale_invoice_grouping_method']))
