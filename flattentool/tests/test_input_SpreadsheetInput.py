# -*- coding: utf-8 -*-
"""
Tests of SpreadsheetInput class from input.py, and its chidlren.
Tests of unflatten method are in test_input_SpreadsheetInput_unflatten.py
"""
from __future__ import unicode_literals
from flattentool.input import SpreadsheetInput, CSVInput, XLSXInput
from decimal import Decimal
from collections import OrderedDict
import sys
import pytest
import openpyxl
import datetime
from six import text_type

class ListInput(SpreadsheetInput):
    def __init__(self, sheets, **kwargs):
        self.sheets = sheets
        super(ListInput, self).__init__(**kwargs)

    def get_sheet_lines(self, sheet_name):
        return self.sheets[sheet_name]

    def read_sheets(self):
        self.sub_sheet_names = list(self.sheets.keys())
        self.sub_sheet_names.remove(self.main_sheet_name)

def test_spreadsheetinput_base_fails():
    spreadsheet_input = SpreadsheetInput()
    with pytest.raises(NotImplementedError):
        spreadsheet_input.read_sheets()
    with pytest.raises(NotImplementedError):
        spreadsheet_input.get_sheet_lines('test')


class TestSuccessfulInput(object):
    def test_csv_input(self, tmpdir):
        main = tmpdir.join('main.csv')
        main.write('colA,colB\ncell1,cell2\ncell3,cell4')
        subsheet = tmpdir.join('subsheet.csv')
        subsheet.write('colC,colD\ncell5,cell6\ncell7,cell8')

        csvinput = CSVInput(input_name=tmpdir.strpath, main_sheet_name='main')
        assert csvinput.main_sheet_name == 'main'

        csvinput.read_sheets()

        assert list(csvinput.get_main_sheet_lines()) == \
            [{'colA': 'cell1', 'colB': 'cell2'}, {'colA': 'cell3', 'colB': 'cell4'}]
        assert csvinput.sub_sheet_names == ['subsheet']
        assert list(csvinput.get_sheet_lines('subsheet')) == \
            [{'colC': 'cell5', 'colD': 'cell6'}, {'colC': 'cell7', 'colD': 'cell8'}]

    def test_xlsx_input(self):
        xlsxinput = XLSXInput(input_name='flattentool/tests/fixtures/xlsx/basic.xlsx', main_sheet_name='main')
        assert xlsxinput.main_sheet_name == 'main'

        xlsxinput.read_sheets()

        assert list(xlsxinput.get_main_sheet_lines()) == \
            [{'colA': 'cell1', 'colB': 'cell2'}, {'colA': 'cell3', 'colB': 'cell4'}]
        assert xlsxinput.sub_sheet_names == ['subsheet']
        assert list(xlsxinput.get_sheet_lines('subsheet')) == \
            [{'colC': 'cell5', 'colD': 'cell6'}, {'colC': 'cell7', 'colD': 'cell8'}]

    def test_xlsx_input_integer(self):
        xlsxinput = XLSXInput(input_name='flattentool/tests/fixtures/xlsx/integer.xlsx', main_sheet_name='main')
        assert xlsxinput.main_sheet_name == 'main'

        xlsxinput.read_sheets()

        assert list(xlsxinput.get_main_sheet_lines()) == \
            [{'colA': 1}]
        assert xlsxinput.sub_sheet_names == []

    def test_xlsx_input_formula(self):
        """ When a forumla is present, we should use the value, rather than the
        formula itself. """

        xlsxinput = XLSXInput(input_name='flattentool/tests/fixtures/xlsx/formula.xlsx', main_sheet_name='main')
        assert xlsxinput.main_sheet_name == 'main'

        xlsxinput.read_sheets()

        assert list(xlsxinput.get_main_sheet_lines()) == \
            [{'colA': 1, 'colB': 2}, {'colA': 2, 'colB': 4}]
        assert xlsxinput.sub_sheet_names == ['subsheet']
        assert list(xlsxinput.get_sheet_lines('subsheet')) == \
            [{'colC': 3, 'colD': 9}, {'colC': 4, 'colD': 12}]


class TestInputFailure(object):
    def test_csv_no_directory(self):
        csvinput = CSVInput(input_name='nonesensedirectory', main_sheet_name='main')
        if sys.version > '3':
            with pytest.raises(FileNotFoundError):
                csvinput.read_sheets()
        else:
            with pytest.raises(OSError):
                csvinput.read_sheets()

    def test_csv_no_files(self, tmpdir):
        csvinput = CSVInput(input_name=tmpdir.strpath, main_sheet_name='main')
        with pytest.raises(ValueError) as e:
            csvinput.read_sheets()
        assert 'Main sheet' in text_type(e) and 'not found' in text_type(e)

    def test_xlsx_no_file(self, tmpdir):
        xlsxinput = XLSXInput(input_name=tmpdir.strpath.join('test.xlsx'), main_sheet_name='main')
        if sys.version > '3':
            with pytest.raises(FileNotFoundError):
                xlsxinput.read_sheets()
        else:
            with pytest.raises(IOError):
                xlsxinput.read_sheets()

    def test_xlsx_no_main_sheet(self):
        xlsxinput = XLSXInput(input_name='flattentool/tests/fixtures/xlsx/basic.xlsx', main_sheet_name='notmain')
        with pytest.raises(ValueError) as e:
            xlsxinput.read_sheets()
        assert 'Main sheet "notmain" not found in workbook.' in text_type(e)


class TestUnicodeInput(object):
    def test_csv_input_utf8(self, tmpdir):
        main = tmpdir.join('main.csv')
        main.write_text('colA\néαГ😼𝒞人', encoding='utf8')
        csvinput = CSVInput(input_name=tmpdir.strpath, main_sheet_name='main')  # defaults to utf8
        csvinput.read_sheets()
        assert list(csvinput.get_main_sheet_lines()) == \
            [{'colA': 'éαГ😼𝒞人'}]
        assert csvinput.sub_sheet_names == []

    def test_csv_input_latin1(self, tmpdir):
        main = tmpdir.join('main.csv')
        main.write_text('colA\né', encoding='latin-1')
        csvinput = CSVInput(input_name=tmpdir.strpath, main_sheet_name='main')
        csvinput.encoding = 'latin-1'
        csvinput.read_sheets()
        assert list(csvinput.get_main_sheet_lines()) == \
            [{'colA': 'é'}]
        assert csvinput.sub_sheet_names == []

    @pytest.mark.xfail(
        sys.version_info < (3, 0),
        reason='Python 2 CSV readers does not support UTF-16 (or any encodings with null bytes')
    def test_csv_input_utf16(self, tmpdir):
        main = tmpdir.join('main.csv')
        main.write_text('colA\néαГ😼𝒞人', encoding='utf16')
        csvinput = CSVInput(input_name=tmpdir.strpath, main_sheet_name='main')
        csvinput.encoding = 'utf16'
        csvinput.read_sheets()
        assert list(csvinput.get_main_sheet_lines()) == \
            [{'colA': 'éαГ😼𝒞人'}]
        assert csvinput.sub_sheet_names == []

    def test_xlsx_input_utf8(self):
        """This is an xlsx file saved by OpenOffice. It seems to use UTF8 internally."""
        xlsxinput = XLSXInput(input_name='flattentool/tests/fixtures/xlsx/unicode.xlsx', main_sheet_name='main')

        xlsxinput.read_sheets()
        assert list(xlsxinput.get_main_sheet_lines())[0]['id'] == 'éαГ😼𝒞人'


def test_convert_type(recwarn):
    si = SpreadsheetInput()
    assert si.convert_type('', 'somestring') == 'somestring'
    # If not type is specified, ints are kept as ints...
    assert si.convert_type('', 3) == 3

    # ... but all other ojbects are converted to strings
    class NotAString(object):
        def __str__(self):
            return 'string representation'
    assert NotAString() != 'string representation'
    assert si.convert_type('', NotAString()) == 'string representation'
    assert si.convert_type('string', NotAString()) == 'string representation'

    assert si.convert_type('string', 3) == '3'
    assert si.convert_type('number', '3') == Decimal('3')
    assert si.convert_type('number', '1.2') == Decimal('1.2')
    assert si.convert_type('integer', '3') == 3
    assert si.convert_type('integer', 3) == 3

    assert si.convert_type('boolean', 'TRUE') is True
    assert si.convert_type('boolean', 'True') is True
    assert si.convert_type('boolean', 1) is True
    assert si.convert_type('boolean', '1') is True
    assert si.convert_type('boolean', 'FALSE') is False
    assert si.convert_type('boolean', 'False') is False
    assert si.convert_type('boolean', 0) is False
    assert si.convert_type('boolean', '0') is False
    si.convert_type('boolean', 2)
    assert 'Unrecognised value for boolean: "2"' in text_type(recwarn.pop(UserWarning).message)
    si.convert_type('boolean', 'test')
    assert 'Unrecognised value for boolean: "test"' in text_type(recwarn.pop(UserWarning).message)

    si.convert_type('integer', 'test')
    assert 'Non-integer value "test"' in text_type(recwarn.pop(UserWarning).message)

    si.convert_type('number', 'test')
    assert 'Non-numeric value "test"' in text_type(recwarn.pop(UserWarning).message)

    assert si.convert_type('string', '') is None
    assert si.convert_type('number', '') is None
    assert si.convert_type('integer', '') is None
    assert si.convert_type('array', '') is None
    assert si.convert_type('boolean', '') is None
    assert si.convert_type('string', None) is None
    assert si.convert_type('number', None) is None
    assert si.convert_type('integer', None) is None
    assert si.convert_type('array', None) is None
    assert si.convert_type('boolean', None) is None

    assert si.convert_type('array', 'one') == ['one']
    assert si.convert_type('array', 'one;two') == ['one', 'two']
    assert si.convert_type('array', 'one,two;three,four') == [['one', 'two'], ['three', 'four']]

    with pytest.raises(ValueError) as e:
        si.convert_type('notatype', 'test')
    assert 'Unrecognised type: "notatype"' in text_type(e)

    assert si.convert_type('string', datetime.datetime(2015, 1, 1)) == '2015-01-01T00:00:00+00:00'
    assert si.convert_type('', datetime.datetime(2015, 1, 1)) == '2015-01-01T00:00:00+00:00'
    assert si.convert_type('string', datetime.datetime(2015, 1, 1, 13, 37, 59)) == '2015-01-01T13:37:59+00:00'
    assert si.convert_type('', datetime.datetime(2015, 1, 1, 13, 37, 59)) == '2015-01-01T13:37:59+00:00'

    si = SpreadsheetInput(timezone_name='Europe/London')
    assert si.convert_type('string', datetime.datetime(2015, 1, 1)) == '2015-01-01T00:00:00+00:00'
    assert si.convert_type('', datetime.datetime(2015, 1, 1)) == '2015-01-01T00:00:00+00:00'
    assert si.convert_type('string', datetime.datetime(2015, 1, 1, 13, 37, 59)) == '2015-01-01T13:37:59+00:00'
    assert si.convert_type('', datetime.datetime(2015, 1, 1, 13, 37, 59)) == '2015-01-01T13:37:59+00:00'
    assert si.convert_type('string', datetime.datetime(2015, 6, 1)) == '2015-06-01T00:00:00+01:00'
    assert si.convert_type('', datetime.datetime(2015, 6, 1)) == '2015-06-01T00:00:00+01:00'
    assert si.convert_type('string', datetime.datetime(2015, 6, 1, 13, 37, 59)) == '2015-06-01T13:37:59+01:00'
    assert si.convert_type('', datetime.datetime(2015, 6, 1, 13, 37, 59)) == '2015-06-01T13:37:59+01:00'