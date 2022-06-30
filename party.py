# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import fields
from trytond.pool import PoolMeta, Pool
from trytond.pyson import Eval, Bool

__all__ = ['Party', 'PartySaleInvoiceGroupingMethod']

GROUPING_PERIODS = [
    (None, 'Standard'),
    ('daily', 'Daily'),
    ('weekly-0', 'Weekly - Monday'),
    ('weekly-1', 'Weekly - Tuesday'),
    ('weekly-2', 'Weekly - Wednesday'),
    ('weekly-3', 'Weekly - Thursday'),
    ('weekly-4', 'Weekly - Friday'),
    ('weekly-5', 'Weekly - Saturday'),
    ('weekly-6', 'Weekly - Sunday'),
    ('weekly-0-break', 'Weekly - Monday - monthly close'),
    ('weekly-1-break', 'Weekly - Tuesday - monthly close'),
    ('weekly-2-break', 'Weekly - Wednesday - monthly close'),
    ('weekly-3-break', 'Weekly - Thursday - monthly close'),
    ('weekly-4-break', 'Weekly - Friday - monthly close'),
    ('weekly-5-break', 'Weekly - Saturday - monthly close'),
    ('weekly-6-break', 'Weekly - Sunday - monthly close'),
    ('ten-days', 'Every Ten Days'),
    ('biweekly', 'Biweekly'),
    ('monthly', 'Monthly'),
    ]


class Party(metaclass=PoolMeta):
    __name__ = 'party.party'

    sale_invoice_grouping_period = fields.MultiValue(fields.Selection(
            GROUPING_PERIODS, 'Sale Invoice Grouping Period',
            states={
                'invisible': ~Bool(Eval('sale_invoice_grouping_method')),
                },
            depends=['sale_invoice_grouping_method'], sort=False))

    @classmethod
    def multivalue_model(cls, field):
        pool = Pool()
        PartySaleInvoiceGroupingMethod = pool.get(
            'party.party.sale_invoice_grouping_method')
        if field == 'sale_invoice_grouping_period':
            return PartySaleInvoiceGroupingMethod
        return super(Party, cls).multivalue_model(field)


class PartySaleInvoiceGroupingMethod(metaclass=PoolMeta):
    __name__ = 'party.party.sale_invoice_grouping_method'

    sale_invoice_grouping_period = fields.Selection(
        GROUPING_PERIODS, "Sale Invoice Grouping Period")

    @classmethod
    def _migrate_property(cls, field_names, value_names, fields):
        field_names.append('sale_invoice_grouping_period')
        value_names.append('sale_invoice_grouping_period')
        super(PartySaleInvoiceGroupingMethod, cls)._migrate_property(
            field_names, value_names, fields)
