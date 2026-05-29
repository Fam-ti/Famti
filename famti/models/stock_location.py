from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError
from odoo import models
import io
import base64
import xlsxwriter
from datetime import datetime


# class StockLocation(models.Model):
#     _inherit = 'stock.location'

#     serial_prefix = fields.Char(string="Serial Prefix")


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    is_tolling = fields.Boolean(string="Is Tolling")
    logo = fields.Image("Logo", max_width=1920, max_height=1920, default=lambda self: self.env.company.logo)

    so_type = fields.Selection(
        related='sale_id.so_type',
        string="SO Type",
        store=True
    )
    po_type = fields.Selection(
        related='purchase_id.po_type',
        string="PO Type",
        store=True
    )

    parent_location_id = fields.Many2one(
        'stock.location',
        default=lambda self: self.env['stock.location'].search([
            ('complete_name', '=', 'FM/Stock')
        ], limit=1)
    )
    
    def button_validate(self):

        for picking in self:
            for move_line in picking.move_line_ids_without_package:

                if move_line.lot_id:
                    if move_line.lot_id.qc_status != 'passed':
                        raise ValidationError(_(
                            "Lot %s is not QC Passed.\n"
                            "You cannot validate this delivery."
                        ) % (move_line.lot_id.name))

        return super().button_validate()


    def action_dispatched_shipment_excel(self):
        
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)

        sheet = workbook.add_worksheet('Dispatch Report')
        title_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 14,
            'bg_color': '#FFFF00',
            'border': 1,
        })

        header_format = workbook.add_format({
            'bold': True,
            'border': 1,
            'align': 'center',
            'bg_color': '#FFFF00',
        })

        cell_format = workbook.add_format({
            'border': 1,
            'bg_color': '#DDEBF7',
        })

        number_format = workbook.add_format({
            'border': 1,
            'bg_color': '#DDEBF7',
            'num_format': '#,##0.00',
        })

        date_format = workbook.add_format({
            'border': 1,
            'bg_color': '#DDEBF7',
            'num_format': 'mmm-dd-yyyy',
        })

        grand_total_format = workbook.add_format({
            'bold': True,
            'border': 1,
            'align': 'center',
            'bg_color': '#FFFF00',
            'num_format': '#,##0.00',
        })


        normal_pickings = self.filtered(
            lambda p: p.sale_id.so_type != 'tolling'
        )

        tolling_pickings = self.filtered(
            lambda p: p.sale_id.so_type == 'tolling'
        )


        left_headers = [
            'Customer Name',
            'Sales Order No.',
            'PO #',
            'Weight Lbs',
            '# of pallets',
            'Pick Up Date',
            'Notes'
        ]

        current_month = datetime.today().strftime('%B')
        current_year = datetime.today().strftime('%Y')

        title = f'{current_month} Dispatched Shipments {current_year}'

        sheet.merge_range(
            'A1:G1',
            title,
            title_format
        )

        for col, header in enumerate(left_headers):
            sheet.write(1, col, header, header_format)

        row_left = 2

        grand_weight_left = 0.0
        grand_pallet_left = 0

        for picking in normal_pickings:

            sale = picking.sale_id

            total_weight = 0.0

            for move in picking.move_ids_without_package:
                total_weight += (
                    move.quantity * move.product_id.weight
                )

            pallet_count = len(
                picking.move_line_ids.mapped('result_package_id')
            )

            grand_weight_left += total_weight
            grand_pallet_left += pallet_count

            sheet.write(row_left, 0,picking.partner_id.name or '',cell_format)
            sheet.write(row_left, 1,sale.name or '',cell_format)
            sheet.write(row_left, 2,sale.buyer_po_number or '',)
            sheet.write(row_left, 3,total_weight,number_format)
            sheet.write(row_left, 4,pallet_count,cell_format)

            if picking.scheduled_date:
                sheet.write_datetime(
                    row_left, 5,
                    picking.scheduled_date,
                    date_format
                )

            sheet.write(
                row_left, 6,
                picking.note or '',
                cell_format
            )

            row_left += 1

        sheet.merge_range(row_left, 0,row_left, 2,'Grand Total',grand_total_format)
        sheet.write(row_left, 3,grand_weight_left,grand_total_format)
        sheet.write(row_left, 4,grand_pallet_left,grand_total_format)

        right_headers = [
            'Customer Name',
            'Sales Order No.',
            'PO #',
            'Weight Lbs',
            '# of pallets',
            'Pick Up Date'
        ]

        start_col = 8

        tolling_title = f'{current_month} Toll Slitting {current_year}'

        sheet.merge_range(
            0, start_col,
            0, start_col + 5,
            tolling_title,
            title_format
        )

        for col, header in enumerate(right_headers):
            sheet.write(
                1,
                start_col + col,
                header,
                header_format
            )

        row_right = 2

        grand_weight_right = 0.0
        grand_pallet_right = 0

        for picking in tolling_pickings:

            sale = picking.sale_id

            total_weight = 0.0

            for move in picking.move_ids_without_package:
                total_weight += (
                    move.quantity * move.product_id.weight
                )

            pallet_count = len(
                picking.move_line_ids.mapped('result_package_id')
            )

            grand_weight_right += total_weight
            grand_pallet_right += pallet_count
            sheet.write(row_right, start_col,picking.partner_id.name or '',cell_format)
            sheet.write(row_right, start_col + 1,sale.name or '',cell_format)
            sheet.write(row_right, start_col + 2,sale.buyer_po_number or '',cell_format)
            sheet.write(row_right, start_col + 3,total_weight,number_format)
            sheet.write(row_right, start_col + 4,pallet_count,cell_format)

            if picking.scheduled_date:
                sheet.write_datetime(
                    row_right, start_col + 5,
                    picking.scheduled_date,
                    date_format
                )

            row_right += 1

        sheet.merge_range(row_right, start_col,row_right, start_col + 2,'Grand Total',grand_total_format)
        sheet.write(row_right, start_col + 3,grand_weight_right,grand_total_format)
        sheet.write(row_right, start_col + 4,grand_pallet_right,grand_total_format)

        sheet.set_column('A:A', 35)
        sheet.set_column('B:B', 22)
        sheet.set_column('C:C', 18)
        sheet.set_column('D:D', 15)
        sheet.set_column('E:E', 15)
        sheet.set_column('F:F', 18)
        sheet.set_column('G:G', 25)

        sheet.set_column('I:I', 35)
        sheet.set_column('J:J', 22)
        sheet.set_column('K:K', 18)
        sheet.set_column('L:L', 15)
        sheet.set_column('M:M', 15)
        sheet.set_column('N:N', 18)

        workbook.close()
        output.seek(0)

        attachment = self.env['ir.attachment'].create({
            'name': 'Dispatch_Report.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(output.read()),
            'mimetype':
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
        }
