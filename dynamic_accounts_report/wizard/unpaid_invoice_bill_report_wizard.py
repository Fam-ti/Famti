from odoo import models, fields
import io
import xlsxwriter
import base64
from datetime import date


class UnpaidInvoiceBillReportWizard(models.TransientModel):
    _name = 'unpaid.invoice.bill.report.wizard'
    _description = 'Unpaid Invoice Bills Report Wizard'

    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')

    partner_ids = fields.Many2many(
        'res.partner',
        string='Customers / Vendors'
    )

    report_type = fields.Selection([
        ('customer', 'Customer Invoice'),
        ('vendor', 'Vendor Bills')
    ], string='Report Type',
       default='customer',
       required=True)

    def action_print_xlsx(self):

        output = io.BytesIO()

        workbook = xlsxwriter.Workbook(
            output,
            {'in_memory': True}
        )

        # ================= SHEET ================= #

        sheet = workbook.add_worksheet(
            'Unpaid Report'
        )

        # ================= FORMATS ================= #

        title_format = workbook.add_format({
            'bold': True,
            'font_size': 16,
            'align': 'center'
        })

        company_format = workbook.add_format({
            'bold': True,
            'font_size': 12,
            'align': 'center'
        })

        filter_format = workbook.add_format({
            'font_size': 11,
            'align': 'center'
        })

        header_format = workbook.add_format({
            'bold': True,
            'border': 1,
            'bg_color': '#D9D9D9',
            'align': 'center',
            'font_size': 10
        })

        text_format = workbook.add_format({
            'border': 1,
            'font_size': 10,
            'align': 'left'
        })

        center_format = workbook.add_format({
            'border': 1,
            'font_size': 10,
            'align': 'center'
        })

        amount_format = workbook.add_format({
            'border': 1,
            'font_size': 10,
            'align': 'right',
            'num_format': '#,##0.00'
        })

        total_format = workbook.add_format({
            'bold': True,
            'border': 1,
            'bg_color': '#D9D9D9',
            'font_size': 10,
            'align': 'right',
            'num_format': '#,##0.00'
        })

        total_text_format = workbook.add_format({
            'bold': True,
            'border': 1,
            'bg_color': '#D9D9D9',
            'font_size': 10,
            'align': 'center'
        })

        # ================= COLUMN WIDTH ================= #

        sheet.set_column('A:A', 18)
        sheet.set_column('B:B', 22)
        sheet.set_column('C:C', 22)
        sheet.set_column('D:D', 18)
        sheet.set_column('E:E', 15)
        sheet.set_column('F:F', 18)
        sheet.set_column('G:G', 20)

        # ================= TITLE ================= #

        sheet.merge_range(
            'A1:G1',
            'Unpaid Invoice/ Bills Report',
            title_format
        )

        sheet.merge_range(
            'A2:G2',
            self.env.company.name or '',
            company_format
        )

        reporting_period = 'All Dates'

        if self.start_date or self.end_date:
            reporting_period = '%s to %s' % (
                self.start_date or '',
                self.end_date or ''
            )

        sheet.merge_range(
            'A3:G3',
            reporting_period,
            filter_format
        )

        # ================= HEADERS ================= #

        headers = [
            'Date',
            'Transaction type',
            '#',
            'Due date',
            'Past due',
            'Amount',
            'Open balance'
        ]

        row = 5
        col = 0

        for header in headers:
            sheet.write(
                row,
                col,
                header,
                header_format
            )
            col += 1

        # ================= DOMAIN ================= #

        move_type = 'out_invoice'

        if self.report_type == 'vendor':
            move_type = 'in_invoice'

        domain = [
            ('move_type', '=', move_type),
            ('state', '=', 'posted'),
            ('payment_state', 'in', [
                'not_paid',
                'partial'
            ])
        ]

        if self.start_date:
            domain.append((
                'invoice_date',
                '>=',
                self.start_date
            ))

        if self.end_date:
            domain.append((
                'invoice_date',
                '<=',
                self.end_date
            ))

        if self.partner_ids:
            domain.append((
                'partner_id',
                'in',
                self.partner_ids.ids
            ))

        invoices = self.env[
            'account.move'
        ].search(domain)

        # ================= DATA ================= #

        row += 1

        total_amount = 0.0
        total_balance = 0.0

        today = date.today()

        for inv in invoices:

            past_due = 0

            if inv.invoice_date_due:
                if inv.invoice_date_due < today:
                    past_due = (
                        today -
                        inv.invoice_date_due
                    ).days

            transaction_type = (
                'Customer Invoice'
            )

            if inv.move_type == 'in_invoice':
                transaction_type = (
                    'Vendor Bill'
                )

            sheet.write(
                row, 0,
                str(inv.invoice_date or ''),
                center_format
            )

            sheet.write(
                row, 1,
                transaction_type,
                text_format
            )

            sheet.write(
                row, 2,
                inv.name or '',
                text_format
            )

            sheet.write(
                row, 3,
                str(inv.invoice_date_due or ''),
                center_format
            )

            sheet.write(
                row, 4,
                past_due,
                center_format
            )

            sheet.write(
                row, 5,
                inv.amount_total or 0.0,
                amount_format
            )

            sheet.write(
                row, 6,
                inv.amount_residual or 0.0,
                amount_format
            )

            total_amount += (
                inv.amount_total or 0.0
            )

            total_balance += (
                inv.amount_residual or 0.0
            )

            row += 1

        # ================= TOTAL ================= #

        sheet.merge_range(
            row,
            0,
            row,
            4,
            'TOTAL',
            total_text_format
        )

        sheet.write(
            row,
            5,
            total_amount,
            total_format
        )

        sheet.write(
            row,
            6,
            total_balance,
            total_format
        )

        # ================= CLOSE ================= #

        workbook.close()

        output.seek(0)

        file_data = base64.b64encode(
            output.read()
        )

        output.close()

        attachment = self.env[
            'ir.attachment'
        ].create({
            'name': 'Unpaid_Invoice_Bills_Report.xlsx',
            'type': 'binary',
            'datas': file_data,
            'mimetype':
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true'
                   % attachment.id,
            'target': 'self',
        }