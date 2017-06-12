# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from . import party
from . import sale
from . import invoice


def register():
    Pool.register(
        party.Party,
        sale.Sale,
        invoice.Invoice,
        module='sale_invoice_grouping_period', type_='model')
