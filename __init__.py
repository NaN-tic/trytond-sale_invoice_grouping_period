# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from .party import *
from .sale import *
from .invoice import *


def register():
    Pool.register(
        Party,
        Sale,
        Invoice,
        module='sale_invoice_period', type_='model')
