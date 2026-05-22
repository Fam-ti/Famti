from odoo import models, fields
import io
import xlsxwriter
import base64


class DailyExpenseSheetWizard(models.TransientModel):
    _name = 'daily.expense.sheet.wizard'
    _description = 'Daily Expense Sheet Report'

    start_date = fields.Date(
        string='Start Date'
    )

    end_date = fields.Date(
        string='End Date'
    )

    partner_ids = fields.Many2many(
        'res.partner',
        string='Companies'
    )

    payment_method = fields.Selection([
        ('credit_card', 'Credit Card'),
        ('cheque', 'Cheque'),
        ('etransfer', 'E-Transfer'),
        ('eft', 'EFT'),
        ('direct_deposit', 'Direct Deposit'),
    ], string='Payment Method')

    def action_print_xlsx(self):

        output = io.BytesIO()

        workbook = xlsxwriter.Workbook(
            output,
            {'in_memory': True}
        )

        sheet = workbook.add_worksheet(
            'Daily Expense Sheet'
        )


        title_format = workbook.add_format({
            'bold': True,
            'font_size': 16,
            'align': 'center',
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

        summary_title = workbook.add_format({
            'bold': True,
            'font_size': 12
        })


        sheet.set_column('A:A', 30)
        sheet.set_column('B:B', 22)
        sheet.set_column('C:C', 18)
        sheet.set_column('D:D', 18)
        sheet.set_column('E:E', 18)
        sheet.set_column('F:F', 18)
        sheet.set_column('G:G', 18)
        sheet.set_column('H:H', 18)
        sheet.set_column('I:I', 18)
        sheet.set_column('J:J', 18)
        sheet.set_column('K:K', 30)
        sheet.set_column('L:L', 12)
        sheet.set_column('M:M', 30)


        sheet.merge_range(
            'A1:M2',
            'Daily Expense Sheet',
            title_format
        )

        row = 4


        headers = [
            'Company Name',
            'Invoice Number',
            'Invoice Date',
            'Due Date',
            'Invoice Amount',
            'Total Amount',
            'Amount Paid',
            'Outstanding Amount',
            'Payment Status',
            'Payment method',
            'Currency',
            'Remarks'
        ]

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
        total_amount = 0.0
        total_paid = 0.0
        total_outstanding = 0.0

        for bill in bills:

            payment_method = ''

            payments = self.env[
                'account.payment'
            ].search([
                ('reconciled_bill_ids', 'in', bill.id),
                ('state', '=', 'posted')
            ], limit=1)

            if payments and payments.journal_id:
                payment_method = (
                    payments.journal_id.name
                )

            invoice_amount = (
                bill.amount_untaxed or 0.0
            )

            total_bill_amount = (
                bill.amount_total or 0.0
            )

            amount_paid = (
                total_bill_amount -
                bill.amount_residual
            )

            outstanding = (
                bill.amount_residual or 0.0
            )

            status = ''

            if bill.payment_state == 'paid':
                status = 'Paid'

            elif bill.payment_state == 'partial':
                status = 'Partial'

            else:
                status = 'Unpaid'

            sheet.write(
                row, 0,
                bill.partner_id.name or '',
                text_format
            )

            sheet.write(
                row, 1,
                bill.name or '',
                text_format
            )

            sheet.write(
                row, 2,
                str(bill.invoice_date or ''),
                center_format
            )

            sheet.write(
                row, 3,
                str(bill.invoice_date_due or ''),
                center_format
            )

            sheet.write(
                row, 4,
                invoice_amount,
                amount_format
            )

            sheet.write(
                row, 5,
                total_bill_amount,
                amount_format
            )

            sheet.write(
                row, 6,
                amount_paid,
                amount_format
            )

            sheet.write(
                row, 7,
                outstanding,
                amount_format
            )

            sheet.write(
                row, 8,
                status,
                center_format
            )

            sheet.write(
                row, 9,
                payment_method,
                text_format
            )

            sheet.write(
                row, 10,
                bill.currency_id.name or '',
                center_format
            )

            sheet.write(
                row, 11,
                bill.ref or '',
                text_format
            )

            total_invoice += 1
            total_amount += total_bill_amount
            total_paid += amount_paid
            total_outstanding += outstanding

            row += 1


        sheet.merge_range(
            row,
            0,
            row,
            4,
            'TOTAL',
            header_format
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
            total_paid,
            total_format
        )

        sheet.write(
            row,
            7,
            total_outstanding,
            total_format
        )


        row += 3

        sheet.write(
            row,
            0,
            'Remarks:',
            sub_title_format
        )


        row += 3

        sheet.write(
            row,
            0,
            'Summary Section (Optional):',
            summary_title
        )

        row += 2

        sheet.write(
            row,
            0,
            'Total Invoices:',
            sub_title_format
        )

        sheet.write(
            row,
            1,
            total_invoice,
            amount_format
        )

        row += 1

        sheet.write(
            row,
            0,
            'Total Amount Payable:',
            sub_title_format
        )

        sheet.write(
            row,
            1,
            total_amount,
            amount_format
        )

        row += 1

        sheet.write(
            row,
            0,
            'Total Paid:',
            sub_title_format
        )

        sheet.write(
            row,
            1,
            total_paid,
            amount_format
        )

        row += 1

        sheet.write(
            row,
            0,
            'Total Outstanding:',
            sub_title_format
        )

        sheet.write(
            row,
            1,
            total_outstanding,
            amount_format
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
            'name': 'Daily_Expense_Sheet.xlsx',
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