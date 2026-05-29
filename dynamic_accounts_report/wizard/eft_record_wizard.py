from odoo import models, fields
import io
import xlsxwriter
import base64


class EFTRecordWizard(models.TransientModel):
    _name = 'eft.record.wizard'
    _description = 'EFT Record Report'

    start_date = fields.Date(
        string='Start Date'
    )

    end_date = fields.Date(
        string='End Date'
    )

    partner_ids = fields.Many2many(
        'res.partner',
        string='Supplier / Company'
    )

    def action_print_xlsx(self):

        output = io.BytesIO()

        workbook = xlsxwriter.Workbook(
            output,
            {'in_memory': True}
        )

        sheet = workbook.add_worksheet(
            'EFT Record'
        )


        title_format = workbook.add_format({
            'bold': True,
            'font_size': 16,
            'align': 'center',
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

        remark_format = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'align': 'left'
        })

        signature_format = workbook.add_format({
            'bold': True,
            'font_size': 11,
            'align': 'left'
        })


        sheet.set_column('A:A', 18)
        sheet.set_column('B:B', 30)
        sheet.set_column('C:C', 25)
        sheet.set_column('D:D', 22)
        sheet.set_column('E:E', 28)
        sheet.set_column('F:F', 22)
        sheet.set_column('G:G', 18)
        sheet.set_column('H:H', 35)


        sheet.merge_range(
            'A1:H2',
            'EFT Record',
            title_format
        )


        headers = [
            'Date',
            'Supplier/ Company',
            'Invoice number/ PI No',
            'Container number',
            'Bank Name',
            'Advance Payment',
            'Amount',
            'Remark'
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

        for payment in payments:

            payment_method = ''

            if payment.journal_id:
                payment_method = (
                    payment.journal_id.name or ''
                ).lower()


            if ('eft' not in payment_method and
                    'transfer' not in payment_method):
                continue

            invoice_names = ', '.join(
                payment.reconciled_bill_ids.mapped(
                    'name'
                )
            )

            container_number = ''

            if payment.ref:
                container_number = payment.ref

            bank_name = ''

            if payment.journal_id:
                bank_name = payment.journal_id.name

            advance_payment = 'No'

            if not payment.reconciled_bill_ids:
                advance_payment = 'Yes'

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
                container_number,
                text_format
            )

            sheet.write(
                row, 4,
                bank_name,
                text_format
            )

            sheet.write(
                row, 5,
                advance_payment,
                center_format
            )

            sheet.write(
                row, 6,
                payment.amount or 0.0,
                amount_format
            )

            sheet.write(
                row, 7,
                payment.ref or '',
                text_format
            )

            row += 1


        row += 3

        sheet.write(
            row,
            0,
            'Remarks:',
            remark_format
        )


        row += 3

        sheet.write(
            row,
            0,
            'Approved by',
            signature_format
        )

        row += 2

        sheet.write(
            row,
            0,
            'Verified by',
            signature_format
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
            'name': 'EFT_Record.xlsx',
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