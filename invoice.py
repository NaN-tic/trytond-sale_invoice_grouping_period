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
__metaclass__ = PoolMeta


class Invoice:
    __name__ = 'account.invoice'
    start_date = fields.Date('Start Date', readonly=True)
    end_date = fields.Date('End Date', readonly=True)
