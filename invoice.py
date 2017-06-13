# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import PoolMeta
from trytond.model import fields

__all__ = ['Invoice']


class Invoice:
    __name__ = 'account.invoice'
    __metaclass__ = PoolMeta
    start_date = fields.Date('Start Date', readonly=True)
    end_date = fields.Date('End Date', readonly=True)
