# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.

from trytond.model import fields
from trytond.pool import PoolMeta
from trytond.pyson import Eval, Bool

__all__ = ['Party']
__metaclass__ = PoolMeta

GROUPING_PERIODS = [
    (None, 'Standard'),
    ('biweekly', 'Biweekly'),
    ('monthly', 'Monthly'),
    ('ten-days', 'Every Ten Days'),
    ]


class Party:
    __name__ = 'party.party'

    sale_invoice_grouping_period = fields.Property(fields.Selection(
            GROUPING_PERIODS, 'Sale Invoice Grouping Period', states={
                'invisible': ~Bool(Eval('sale_invoice_grouping_method')),
                }, depends=['sale_invoice_grouping_method']))
