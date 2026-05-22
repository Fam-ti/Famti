from odoo import models, fields
import io
import xlsxwriter
import base64


class ChequePaymentReportWizard(models.TransientModel):
    _name = 'cheque.payment.report.wizard'
    _description = 'Cheque Payment Report Wizard'

    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')

    partner_ids = fields.Many2many(
        'res.partner',
        string='Partners'
    )

    def action_print_xlsx(self):

        output = io.BytesIO()

        workbook = xlsxwriter.Workbook(
            output,
            {'in_memory': True}
        )

        sheet = workbook.add_worksheet(
            'Cheque Payments'
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

        summary_title_format = workbook.add_format({
            'bold': True,
            'font_size': 12,
            'align': 'left'
        })

        summary_label_format = workbook.add_format({
            'bold': True,
            'border': 1,
            'font_size': 10,
            'align': 'left'
        })

        summary_value_format = workbook.add_format({
            'border': 1,
            'font_size': 10,
            'align': 'right',
            'num_format': '#,##0.00'
        })

        sheet.set_column('A:A', 18)
        sheet.set_column('B:B', 30)
        sheet.set_column('C:C', 20)
        sheet.set_column('D:D', 20)
        sheet.set_column('E:E', 30)
        sheet.set_column('F:F', 15)
        sheet.set_column('G:G', 18)
        sheet.set_column('H:H', 28)
        sheet.set_column('I:I', 25)

        sheet.merge_range(
            'A1:I2',
            'Cheque Payment Report',
            title_format
        )

        headers = [
            'Issue Date',
            'Payer/ Payee',
            'Invoice no',
            'Cheque number',
            'Bank Name/ Branch name',
            'Currency USD/CAD',
            'Total Amount',
            'Status(cleared/ pending/ bounced)',
            'Remarks'
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

        total_issued = 0
        total_received = 0

        total_amount_issued = 0.0
        total_amount_received = 0.0

        for payment in payments:

            invoice_names = ', '.join(
                payment.reconciled_invoice_ids.mapped(
                    'name'
                )
            )

            cheque_number = (
                payment.ref or ''
            )

            bank_name = ''

            if payment.journal_id:
                bank_name = (
                    payment.journal_id.name
                )

            status = 'Cleared'

            if payment.state != 'posted':
                status = 'Pending'

            payer_payee = (
                payment.partner_id.name or ''
            )

            if payment.payment_type == 'inbound':
                total_received += 1
                total_amount_received += (
                    payment.amount or 0.0
                )

            elif payment.payment_type == 'outbound':
                total_issued += 1
                total_amount_issued += (
                    payment.amount or 0.0
                )

            sheet.write(
                row, 0,
                str(payment.date or ''),
                center_format
            )

            sheet.write(
                row, 1,
                payer_payee,
                text_format
            )

            sheet.write(
                row, 2,
                invoice_names,
                text_format
            )

            sheet.write(
                row, 3,
                cheque_number,
                text_format
            )

            sheet.write(
                row, 4,
                bank_name,
                text_format
            )

            sheet.write(
                row, 5,
                payment.currency_id.name or '',
                center_format
            )

            sheet.write(
                row, 6,
                payment.amount or 0.0,
                amount_format
            )

            sheet.write(
                row, 7,
                status,
                center_format
            )

            sheet.write(
                row, 8,
                '',
                text_format
            )

            row += 1

        row += 3

        sheet.merge_range(
            row,
            0,
            row,
            3,
            'Summary Section (Optional):',
            summary_title_format
        )

        row += 2

        sheet.write(
            row,
            0,
            'Total Cheques Issued:',
            summary_label_format
        )

        sheet.write(
            row,
            1,
            total_issued,
            summary_value_format
        )

        row += 1

        sheet.write(
            row,
            0,
            'Total Cheques Received:',
            summary_label_format
        )

        sheet.write(
            row,
            1,
            total_received,
            summary_value_format
        )

        row += 1

        sheet.write(
            row,
            0,
            'Total Amount Issued:',
            summary_label_format
        )

        sheet.write(
            row,
            1,
            total_amount_issued,
            summary_value_format
        )

        row += 1

        sheet.write(
            row,
            0,
            'Total Amount Received:',
            summary_label_format
        )

        sheet.write(
            row,
            1,
            total_amount_received,
            summary_value_format
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
            'name': 'Cheque_Payment_Report.xlsx',
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