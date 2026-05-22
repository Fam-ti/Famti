from odoo import models, fields
import io
import xlsxwriter
import base64


class CreditCardPaymentReportWizard(models.TransientModel):
    _name = 'credit.card.payment.report.wizard'
    _description = 'Credit Card Payment Report Wizard'

    start_date = fields.Date(string='Start Date')

    end_date = fields.Date(string='End Date')

    partner_ids = fields.Many2many(
        'res.partner',
        string='Companies'
    )

    payment_type = fields.Selection([
        ('cash', 'Cash'),
        ('credit_card', 'Credit Card'),
        ('etransfer', 'E-Transfer'),
    ], string='Payment Type', required=True)

    def action_print_xlsx(self):

        output = io.BytesIO()

        workbook = xlsxwriter.Workbook(
            output,
            {'in_memory': True}
        )

        sheet = workbook.add_worksheet(
            'Payment Report'
        )

        title_format = workbook.add_format({
            'align': 'center',
            'bold': True,
            'font_size': 16,
            'border': 1
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

        remark_format = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'align': 'left'
        })

        sheet.set_column('A:A', 18)
        sheet.set_column('B:B', 30)
        sheet.set_column('C:C', 20)
        sheet.set_column('D:D', 18)
        sheet.set_column('E:E', 22)
        sheet.set_column('F:F', 25)

        title = ''

        if self.payment_type == 'cash':
            title = 'Cash Payment'

        elif self.payment_type == 'credit_card':
            title = 'Credit Card Payment'

        elif self.payment_type == 'etransfer':
            title = 'E-Transfer Payment'

        sheet.merge_range(
            'A1:F2',
            title,
            title_format
        )

        headers = [
            'Date',
            'Company',
            'Invoice no',
            'Amount',
            'Type of Credit',
            'Payment method'
        ]

        row = 3
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
            ('payment_type', '=', 'inbound'),
            ('state', '=', 'posted')
        ]

        if self.start_date:
            domain.append((
                'date',
                '>=',
                self.start_date
            ))

        if self.end_date:
            domain.append((
                'date',
                '<=',
                self.end_date
            ))

        if self.partner_ids:
            domain.append((
                'partner_id',
                'in',
                self.partner_ids.ids
            ))

        payments = self.env[
            'account.payment'
        ].search(domain)

        row += 1

        total_amount = 0.0

        for payment in payments:

            payment_method_name = ''

            if payment.journal_id:
                payment_method_name = (
                    payment.journal_id.name or ''
                ).lower()

            if self.payment_type == 'cash':

                if 'cash' not in payment_method_name:
                    continue

            elif self.payment_type == 'credit_card':

                if ('card' not in payment_method_name and
                        'credit' not in payment_method_name):
                    continue

            elif self.payment_type == 'etransfer':

                if ('transfer' not in payment_method_name and
                        'eft' not in payment_method_name):
                    continue

            invoice_names = ', '.join(
                payment.reconciled_invoice_ids.mapped(
                    'name'
                )
            )

            sheet.write(
                row, 0,
                str(payment.date or ''),
                center_format
            )

            sheet.write(
                row, 1,
                payment.partner_id.name or '',
                text_format
            )

            sheet.write(
                row, 2,
                invoice_names or '',
                text_format
            )

            sheet.write(
                row, 3,
                payment.amount or 0.0,
                amount_format
            )

            sheet.write(
                row, 4,
                'Credit',
                center_format
            )

            sheet.write(
                row, 5,
                payment.journal_id.name or '',
                text_format
            )

            total_amount += (
                payment.amount or 0.0
            )

            row += 1

        sheet.merge_range(
            row,
            0,
            row,
            2,
            'TOTAL',
            header_format
        )

        sheet.write(
            row,
            3,
            total_amount,
            total_format
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
            'name': '%s_Report.xlsx' % title.replace(' ', '_'),
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