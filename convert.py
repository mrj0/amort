#!/usr/bin/env python

import argparse
import decimal
import os
import sys
from decimal import Decimal, getcontext

import uno
from unohelper import Base, systemPathToFileUrl, absolutize
from com.sun.star.beans import PropertyValue
from com.sun.star.io import XOutputStream

open_props = PropertyValue("Hidden", 0, True, 0),
PDF_FILTER = "calc_pdf_Export"


class OutputStream(Base, XOutputStream):
    def __init__(self):
        self.closed = 0

    def closeOutput(self):
        self.closed = 1

    def writeBytes(self, seq):
        sys.stdout.write(seq.value)

    def flush(self):
        pass


if __name__ == '__main__':
    getcontext().prec = 8
    getcontext().rounding = decimal.ROUND_HALF_UP

    parser = argparse.ArgumentParser('convert.py')

    parser.add_argument("-n", "--name", help="Prepared for name", default='test')
    parser.add_argument("-w", "--workbook", help="Workbook path", default='amort.ods')
    parser.add_argument("-d", "--dest", help="Output path", default='amort.pdf')
    parser.add_argument("-p", "--price", help="Purchase price", default='400000')
    parser.add_argument("-t", "--term", help="Term", default='30')
    parser.add_argument("-r", "--rate", help="Interest rate", default='4.25')
    parser.add_argument("--down-percent", help="The amount down as a percentage")
    parser.add_argument("--down", "--down", help="The amount down")

    args = parser.parse_args()

    if args.down_percent and args.down:
        print("Pass either a percent or total down")
        sys.exit(1)

    if not args.down_percent and not args.down:
        print('You should specify --down or --down-percent, assuming 20%')
        args.down_percent = '20'

    # get the uno component context from the PyUNO runtime
    local_context = uno.getComponentContext()

    # create the UnoUrlResolver
    resolver = local_context.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", local_context)

    # connect to the running office
    ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
    manager = ctx.ServiceManager

    # get the central desktop object
    desktop = manager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)

    cwd = systemPathToFileUrl(os.getcwd())
    url = absolutize(cwd, systemPathToFileUrl(args.workbook))
    print('Opening url', url)

    doc = desktop.loadComponentFromURL(url, "_blank", 0, open_props)

    try:
        monthly = doc.getSheets().getByIndex(0)
        yearly = doc.getSheets().getByIndex(1)
        monthly.getCellRangeByName('c2').setString(args.name)
        yearly.getCellRangeByName('c2').setString(args.name)

        monthly.getCellRangeByName('f4').setValue(args.price)
        monthly.getCellRangeByName('f7').setValue(args.term)

        monthly.getCellRangeByName('f8').setValue(str(Decimal(args.rate) / 100))

        if args.down:
            monthly.getCellRangeByName('g5').setValue(args.down)
            percent = Decimal(args.down) / Decimal(args.price)
            print('setting percent', percent * 100)
            monthly.getCellRangeByName('f5').setValue(str(percent))
        if args.down_percent:
            monthly.getCellRangeByName('f5').setValue(str(Decimal(args.down_percent) / 100))
            down = Decimal(args.price) * (Decimal(args.down_percent) / 100)
            print('setting down', down)
            monthly.getCellRangeByName('g5').setValue(str(down))

        outProps = (
            PropertyValue("FilterName", 0, PDF_FILTER, 0),
            PropertyValue("Overwrite", 0, True, 0),
            PropertyValue("OutputStream", 0, OutputStream(), 0)
        )
        destUrl = absolutize(cwd, systemPathToFileUrl(args.dest))
        doc.storeToURL(destUrl, outProps)
    finally:
        doc.dispose()
