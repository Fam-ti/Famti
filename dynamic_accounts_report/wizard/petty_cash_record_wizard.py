from odoo import models, fields
import io
import xlsxwriter
import base64


class PettyCashRecordWizard(models.TransientModel):
    _name = 'petty.cash.record.wizard'
    _description = 'Petty Cash Record Wizard'

    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')

    partner_ids = fields.Many2many(
        'res.partner',
        string='Received By / Paid To'
    )

    opening_balance = fields.Float(
        string='Opening Balance'
    )

    def action_print_xlsx(self):

        output = io.BytesIO()

        workbook = xlsxwriter.Workbook(
            output,
            {'in_memory': True}
        )

        sheet = workbook.add_worksheet(
            'Petty Cash Record'
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

        sheet.set_column('A:A', 10)
        sheet.set_column('B:B', 18)
        sheet.set_column('C:C', 25)
        sheet.set_column('D:D', 35)
        sheet.set_column('E:E', 18)
        sheet.set_column('F:F', 18)
        sheet.set_column('G:G', 18)
        sheet.set_column('H:H', 30)
        sheet.set_column('I:I', 25)

        sheet.merge_range(
            'A1:I2',
            'Petty cash record',
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
            'Month / Period:',
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
            'Sr. No.',
            'Date',
            'Voucher / Receipt No.',
            'Purpose / Description',
            'Amount Issued',
            'Amount Spent',
            'Balance',
            'Received By / Paid To',
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

        sr_no = 1
        balance = self.opening_balance

        total_issued = 0.0
        total_spent = 0.0

        for payment in payments:

            amount_issued = 0.0
            amount_spent = 0.0

            if payment.payment_type == 'inbound':
                amount_issued = (
                    payment.amount or 0.0
                )

                balance += amount_issued

                total_issued += amount_issued

            else:
                amount_spent = (
                    payment.amount or 0.0
                )

                balance -= amount_spent

                total_spent += amount_spent

            sheet.write(
                row, 0,
                sr_no,
                center_format
            )

            sheet.write(
                row, 1,
                str(payment.date or ''),
                center_format
            )

            sheet.write(
                row, 2,
                payment.ref or '',
                text_format
            )

            sheet.write(
                row, 3,
                payment.ref or '',
                text_format
            )

            sheet.write(
                row, 4,
                amount_issued,
                amount_format
            )

            sheet.write(
                row, 5,
                amount_spent,
                amount_format
            )

            sheet.write(
                row, 6,
                balance,
                amount_format
            )

            sheet.write(
                row, 7,
                payment.partner_id.name or '',
                text_format
            )

            sheet.write(
                row, 8,
                '',
                text_format
            )

            sr_no += 1
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

        closing_balance = (
            self.opening_balance +
            total_issued -
            total_spent
        )

        sheet.write(
            row, 0,
            'Opening Balance:',
            summary_label
        )

        sheet.write(
            row, 1,
            self.opening_balance,
            summary_value
        )

        row += 1

        sheet.write(
            row, 0,
            'Total Issued:',
            summary_label
        )

        sheet.write(
            row, 1,
            total_issued,
            summary_value
        )

        row += 1

        sheet.write(
            row, 0,
            'Total Spent:',
            summary_label
        )

        sheet.write(
            row, 1,
            total_spent,
            summary_value
        )

        row += 1

        sheet.write(
            row, 0,
            'Closing Balance:',
            summary_label
        )

        sheet.write(
            row, 1,
            closing_balance,
            summary_value
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
            'name': 'Petty_Cash_Record.xlsx',
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