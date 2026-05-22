from odoo import models, fields
import io
import xlsxwriter
import base64


class AccountsPayableReportWizard(models.TransientModel):
    _name = 'accounts.payable.report.wizard'
    _description = 'Accounts Payable Report Wizard'

    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')

    partner_ids = fields.Many2many(
        'res.partner',
        string='Suppliers'
    )

    def action_print_xlsx(self):

        output = io.BytesIO()

        workbook = xlsxwriter.Workbook(
            output,
            {'in_memory': True}
        )

        sheet = workbook.add_worksheet(
            'Accounts Payable'
        )

        title_format = workbook.add_format({
            'align': 'center',
            'bold': True,
            'font_size': 16,
            'border': 1
        })

        sub_title_format = workbook.add_format({
            'bold': True,
            'font_size': 11,
            'align': 'left'
        })

        header_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'bg_color': '#D9D9D9',
            'font_size': 10,
            'text_wrap': True
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

        summary_label = workbook.add_format({
            'bold': True,
            'border': 1,
            'font_size': 10
        })

        summary_value = workbook.add_format({
            'border': 1,
            'font_size': 10,
            'num_format': '#,##0.00'
        })

        sheet.set_column('A:A', 28)
        sheet.set_column('B:B', 18)
        sheet.set_column('C:C', 20)
        sheet.set_column('D:D', 18)
        sheet.set_column('E:E', 18)
        sheet.set_column('F:F', 18)
        sheet.set_column('G:G', 18)
        sheet.set_column('H:H', 18)
        sheet.set_column('I:I', 20)
        sheet.set_column('J:J', 18)
        sheet.set_column('K:K', 35)
        sheet.set_column('L:L', 12)
        sheet.set_column('M:M', 25)

        sheet.merge_range(
            'A1:M2',
            'Accounts Payable Report',
            title_format
        )

        row = 3

        sheet.write(
            row, 0,
            'Company Name:',
            sub_title_format
        )

        sheet.write(
            row, 1,
            self.env.company.name or ''
        )

        row += 1

        sheet.write(
            row, 0,
            'Reporting Period:',
            sub_title_format
        )

        sheet.write(
            row, 1,
            '%s to %s' % (
                self.start_date or '',
                self.end_date or ''
            )
        )

        row += 1

        sheet.write(
            row, 0,
            'Prepared By:',
            sub_title_format
        )

        sheet.write(
            row, 1,
            self.env.user.name or ''
        )

        headers = [
            'Supplier Name',
            'Supplier Code',
            'Invoice Number',
            'Invoice Date',
            'Due Date',
            'Invoice Amount',
            'Total Amount',
            'Amount Paid',
            'Outstanding Amount',
            'Payment Status',
            'Payment method\ncredit card/ Chq/ e transfer/ EFT/ Direct deposit',
            'Currency',
            'Remarks'
        ]

        row = 8
        col = 0

        for header in headers:
            sheet.write(
                row,
                col,
                header,
                header_format
            )
            col += 1

        domain = [
            ('move_type', '=', 'in_invoice'),
            ('state', '=', 'posted')
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

        bills = self.env[
            'account.move'
        ].search(domain)

        row += 1

        total_invoice = 0
        total_amount_payable = 0.0
        total_paid = 0.0
        total_outstanding = 0.0

        for bill in bills:

            amount_paid = (
                bill.amount_total -
                bill.amount_residual
            )

            payment_method = ''

            payment = self.env[
                'account.payment'
            ].search([
                ('reconciled_bill_ids', 'in', bill.id)
            ], limit=1)

            if payment:
                payment_method = (
                    payment.journal_id.name
                )

            sheet.write(
                row, 0,
                bill.partner_id.name or '',
                text_format
            )

            sheet.write(
                row, 1,
                bill.partner_id.ref or '',
                text_format
            )

            sheet.write(
                row, 2,
                bill.name or '',
                text_format
            )

            sheet.write(
                row, 3,
                str(bill.invoice_date or ''),
                center_format
            )

            sheet.write(
                row, 4,
                str(bill.invoice_date_due or ''),
                center_format
            )

            sheet.write(
                row, 5,
                bill.amount_untaxed or 0.0,
                amount_format
            )

            sheet.write(
                row, 6,
                bill.amount_total or 0.0,
                amount_format
            )

            sheet.write(
                row, 7,
                amount_paid or 0.0,
                amount_format
            )

            sheet.write(
                row, 8,
                bill.amount_residual or 0.0,
                amount_format
            )

            sheet.write(
                row, 9,
                bill.payment_state or '',
                center_format
            )

            sheet.write(
                row, 10,
                payment_method or '',
                text_format
            )

            sheet.write(
                row, 11,
                bill.currency_id.name or '',
                center_format
            )

            sheet.write(
                row, 12,
                bill.narration or '',
                text_format
            )

            total_invoice += 1
            total_amount_payable += (
                bill.amount_total or 0.0
            )

            total_paid += amount_paid

            total_outstanding += (
                bill.amount_residual or 0.0
            )

            row += 1

        row += 3

        sheet.merge_range(
            row,
            0,
            row,
            3,
            'Summary Section (Optional):',
            sub_title_format
        )

        row += 2

        sheet.write(
            row, 0,
            'Total Invoices:',
            summary_label
        )

        sheet.write(
            row, 1,
            total_invoice,
            summary_value
        )

        row += 1

        sheet.write(
            row, 0,
            'Total Amount Payable:',
            summary_label
        )

        sheet.write(
            row, 1,
            total_amount_payable,
            summary_value
        )

        row += 1

        sheet.write(
            row, 0,
            'Total Paid:',
            summary_label
        )

        sheet.write(
            row, 1,
            total_paid,
            summary_value
        )

        row += 1

        sheet.write(
            row, 0,
            'Total Outstanding:',
            summary_label
        )

        sheet.write(
            row, 1,
            total_outstanding,
            summary_value
        )

        row += 3

        sheet.write(
            row,
            0,
            'Remarks:',
            sub_title_format
        )

        workbook.close()

        output.seek(0)

        file_data = base64.b64encode(
            output.read()
        )

        output.close()

        attachment = self.env[
            'ir.attachment'
        ].create({
            'name': 'Accounts_Payable_Report.xlsx',
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