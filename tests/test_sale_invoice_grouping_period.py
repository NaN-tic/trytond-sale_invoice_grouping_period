#!/usr/bin/env python
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
import unittest
import doctest
from datetime import datetime
import trytond.tests.test_tryton
from trytond.tests.test_tryton import POOL, DB_NAME, USER, CONTEXT, test_view, \
    test_depends
from trytond.tests.test_tryton import doctest_setup, doctest_teardown
from trytond.transaction import Transaction

DATES = (
    ('2016-01-01', 'monthly', '2016-01-01', '2016-01-31'),
    ('2016-01-15', 'monthly', '2016-01-01', '2016-01-31'),
    ('2016-01-31', 'monthly', '2016-01-01', '2016-01-31'),
    ('2016-01-31', 'monthly', '2016-01-01', '2016-01-31'),
    ('2016-02-04', 'monthly', '2016-02-01', '2016-02-29'),
    ('2016-01-01', 'biweekly', '2016-01-01', '2016-01-15'),
    ('2016-01-07', 'biweekly', '2016-01-01', '2016-01-15'),
    ('2016-01-15', 'biweekly', '2016-01-01', '2016-01-15'),
    ('2016-01-16', 'biweekly', '2016-01-16', '2016-01-31'),
    ('2016-01-20', 'biweekly', '2016-01-16', '2016-01-31'),
    ('2016-01-31', 'biweekly', '2016-01-16', '2016-01-31'),
    ('2016-01-01', 'ten-days', '2016-01-01', '2016-01-10'),
    ('2016-01-05', 'ten-days', '2016-01-01', '2016-01-10'),
    ('2016-01-10', 'ten-days', '2016-01-01', '2016-01-10'),
    ('2016-01-11', 'ten-days', '2016-01-11', '2016-01-20'),
    ('2016-01-15', 'ten-days', '2016-01-11', '2016-01-20'),
    ('2016-01-20', 'ten-days', '2016-01-11', '2016-01-20'),
    ('2016-01-21', 'ten-days', '2016-01-21', '2016-01-31'),
    ('2016-01-25', 'ten-days', '2016-01-21', '2016-01-31'),
    ('2016-01-31', 'ten-days', '2016-01-21', '2016-01-31'),
    ('2016-01-04', 'weekly-0', '2016-01-04', '2016-01-10'),
    ('2016-01-07', 'weekly-0', '2016-01-04', '2016-01-10'),
    ('2016-01-10', 'weekly-0', '2016-01-04', '2016-01-10'),
    ('2016-01-05', 'weekly-1', '2016-01-05', '2016-01-11'),
    ('2016-01-07', 'weekly-1', '2016-01-05', '2016-01-11'),
    ('2016-01-11', 'weekly-1', '2016-01-05', '2016-01-11'),
    ('2016-01-06', 'weekly-2', '2016-01-06', '2016-01-12'),
    ('2016-01-08', 'weekly-2', '2016-01-06', '2016-01-12'),
    ('2016-01-12', 'weekly-2', '2016-01-06', '2016-01-12'),
    ('2016-01-07', 'weekly-3', '2016-01-07', '2016-01-13'),
    ('2016-01-09', 'weekly-3', '2016-01-07', '2016-01-13'),
    ('2016-01-13', 'weekly-3', '2016-01-07', '2016-01-13'),
    ('2016-01-08', 'weekly-4', '2016-01-08', '2016-01-14'),
    ('2016-01-10', 'weekly-4', '2016-01-08', '2016-01-14'),
    ('2016-01-14', 'weekly-4', '2016-01-08', '2016-01-14'),
    ('2016-01-09', 'weekly-5', '2016-01-09', '2016-01-15'),
    ('2016-01-12', 'weekly-5', '2016-01-09', '2016-01-15'),
    ('2016-01-15', 'weekly-5', '2016-01-09', '2016-01-15'),
    ('2016-01-10', 'weekly-6', '2016-01-10', '2016-01-16'),
    ('2016-01-13', 'weekly-6', '2016-01-10', '2016-01-16'),
    ('2016-01-16', 'weekly-6', '2016-01-10', '2016-01-16'),
    )

class TestCase(unittest.TestCase):
    'Test module'

    def setUp(self):
        trytond.tests.test_tryton.install_module('sale_invoice_grouping_period')
        self.sale = POOL.get('sale.sale')

    def test0005views(self):
        'Test views'
        test_view('sale_invoice_grouping_period')

    def test0006depends(self):
        'Test depends'
        test_depends()

    def test0010calc_invoice_dates(self):
        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            for item in DATES:
                date = datetime.strptime(item[0], '%Y-%m-%d').date()
                period = item[1]
                start, end = self.sale._get_invoice_dates(date, period)
                self.assertEqual(start.strftime('%Y-%m-%d'), item[2],
                    msg='Wrong start date with date %s with period %s (%s '
                    'should be %s).' % (date, period, start, item[2]))
                self.assertEqual(end.strftime('%Y-%m-%d'), item[3], msg='Wrong '
                    'end date with date %s with period %s (%s should be %s).'
                    % (date, period, end, item[3]))


def suite():
    suite = trytond.tests.test_tryton.suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestCase))
    suite.addTests(doctest.DocFileSuite('scenario_sale_invoice_grouping_period.rst',
            setUp=doctest_setup, tearDown=doctest_teardown, encoding='utf-8',
            optionflags=doctest.REPORT_ONLY_FIRST_FAILURE))
    return suite
