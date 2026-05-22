from odoo import models, fields
import io
import xlsxwriter
import base64


class CreditNoteWizard(models.TransientModel):
    _name = 'credit.note.wizard'
    _description = 'Credit Note Report Wizard'

    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')

    partner_ids = fields.Many2many(
        'res.partner',
        string='Companies'
    )

    def action_print_xlsx(self):

        output = io.BytesIO()

        workbook = xlsxwriter.Workbook(
            output,
            {'in_memory': True}
        )


        sheet = workbook.add_worksheet(
            'Credit Note'
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
            'num_format': '#,##0.00',
            'align': 'right'
        })


        sheet.set_column('A:A', 20)
        sheet.set_column('B:B', 18)
        sheet.set_column('C:C', 28)
        sheet.set_column('D:D', 20)
        sheet.set_column('E:E', 15)
        sheet.set_column('F:F', 30)
        sheet.set_column('G:G', 15)
        sheet.set_column('H:H', 15)
        sheet.set_column('I:I', 15)
        sheet.set_column('J:J', 15)
        sheet.set_column('K:K', 18)
        sheet.set_column('L:L', 15)
        sheet.set_column('M:M', 25)


        sheet.merge_range(
            'A1:M2',
            'FAM Credit Note SHEET',
            title_format
        )


        headers = [
            'Credit note no',
            'Credit Date',
            'Purchase order against Credit',
            'Type of Film',
            'Qty/lb',
            'Credit to company name',
            'Amount',
            'HST',
            'Total',
            'Currency',
            'Status',
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
            ('move_type', '=', 'out_refund')
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

        credit_notes = self.env[
            'account.move'
        ].search(domain)


        row += 1

        total_credit = 0.0

        for note in credit_notes:

            qty = sum(
                note.invoice_line_ids.mapped(
                    'quantity'
                )
            )

            status = 'Credited'

            if note.state == 'cancel':
                status = 'Cancelled'

            sheet.write(
                row, 0,
                note.name or '',
                text_format
            )

            sheet.write(
                row, 1,
                str(note.invoice_date or ''),
                center_format
            )

            sheet.write(
                row, 2,
                note.invoice_origin or '',
                text_format
            )

            sheet.write(
                row, 3,
                '',
                text_format
            )

            sheet.write(
                row, 4,
                qty,
                center_format
            )

            sheet.write(
                row, 5,
                note.partner_id.name or '',
                text_format
            )

            sheet.write(
                row, 6,
                note.amount_untaxed or 0.0,
                amount_format
            )

            sheet.write(
                row, 7,
                note.amount_tax or 0.0,
                amount_format
            )

            sheet.write(
                row, 8,
                note.amount_total or 0.0,
                amount_format
            )

            sheet.write(
                row, 9,
                note.currency_id.name or '',
                center_format
            )

            sheet.write(
                row, 10,
                status,
                center_format
            )

            sheet.write(
                row, 11,
                '',
                text_format
            )

            total_credit += (
                note.amount_total or 0.0
            )

            row += 1


        sheet.merge_range(
            row,
            0,
            row,
            7,
            'TOTAL',
            header_format
        )

        sheet.write(
            row,
            8,
            total_credit,
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
            'name': 'Credit_Note_Report.xlsx',
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