from odoo import models, fields
import io
import xlsxwriter
import base64


class ProfitLossStatementWizard(models.TransientModel):
    _name = 'profit.loss.statement.wizard'
    _description = 'Income Statement / Profit & Loss Statement'

    start_date = fields.Date(
        string='Start Date',
        required=True
    )

    end_date = fields.Date(
        string='End Date',
        required=True
    )

    def _get_account_balance(self, account_types):

        lines = self.env[
            'account.move.line'
        ].search([
            ('date', '>=', self.start_date),
            ('date', '<=', self.end_date),
            ('parent_state', '=', 'posted'),
            ('account_id.account_type', 'in', account_types)
        ])

        balance = sum(
            lines.mapped('balance')
        )

        return abs(balance)

    def action_print_xlsx(self):

        output = io.BytesIO()

        workbook = xlsxwriter.Workbook(
            output,
            {'in_memory': True}
        )


        sheet = workbook.add_worksheet(
            'Profit & Loss'
        )


        title_format = workbook.add_format({
            'bold': True,
            'font_size': 16,
            'align': 'center'
        })

        sub_title_format = workbook.add_format({
            'bold': True,
            'font_size': 12,
            'align': 'center'
        })

        section_format = workbook.add_format({
            'bold': True,
            'font_size': 12,
            'bg_color': '#D9D9D9',
            'border': 1,
            'align': 'left'
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
            'font_size': 10
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
            'bg_color': '#EAEAEA',
            'font_size': 10,
            'align': 'right',
            'num_format': '#,##0.00'
        })

        total_text_format = workbook.add_format({
            'bold': True,
            'border': 1,
            'bg_color': '#EAEAEA',
            'font_size': 10
        })


        sheet.set_column('A:A', 12)
        sheet.set_column('B:B', 45)
        sheet.set_column('C:C', 22)


        sheet.merge_range(
            'A1:C1',
            self.env.company.name or '',
            title_format
        )

        sheet.merge_range(
            'A2:C2',
            'Income Statement / Profit & Loss Statement',
            title_format
        )

        sheet.merge_range(
            'A3:C3',
            'For the Period Ending %s' % (
                self.end_date or ''
            ),
            sub_title_format
        )

        row = 5

        sales_revenue = self._get_account_balance([
            'income'
        ])

        service_income = 0.0
        other_income = 0.0

        total_revenue = (
            sales_revenue +
            service_income +
            other_income
        )

        sheet.merge_range(
            row, 0, row, 2,
            '1. Revenue / Income',
            section_format
        )

        row += 1

        headers = [
            'Sr. No.',
            'Description',
            'Amount (Currency)'
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

        row += 1

        revenue_data = [
            [1, 'Sales Revenue', sales_revenue],
            [2, 'Service Income', service_income],
            [3, 'Other Income', other_income],
        ]

        for rec in revenue_data:

            sheet.write(
                row, 0,
                rec[0],
                text_format
            )

            sheet.write(
                row, 1,
                rec[1],
                text_format
            )

            sheet.write(
                row, 2,
                rec[2],
                amount_format
            )

            row += 1

        sheet.write(
            row, 0,
            '',
            total_text_format
        )

        sheet.write(
            row, 1,
            'Total Revenue / Income',
            total_text_format
        )

        sheet.write(
            row, 2,
            total_revenue,
            total_format
        )

        row += 2

        opening_inventory = 0.0

        purchases = self._get_account_balance([
            'expense_direct_cost'
        ])

        direct_expenses = 0.0
        closing_inventory = 0.0

        total_cogs = (
            opening_inventory +
            purchases +
            direct_expenses -
            closing_inventory
        )

        sheet.merge_range(
            row, 0, row, 2,
            '2. Cost of Goods Sold (COGS)',
            section_format
        )

        row += 1

        for i, header in enumerate(headers):
            sheet.write(
                row,
                i,
                header,
                header_format
            )

        row += 1

        cogs_data = [
            [1, 'Opening Inventory', opening_inventory],
            [2, 'Purchases', purchases],
            [3, 'Direct Expenses', direct_expenses],
            [4, 'Closing Inventory', closing_inventory],
        ]

        for rec in cogs_data:

            sheet.write(
                row, 0,
                rec[0],
                text_format
            )

            sheet.write(
                row, 1,
                rec[1],
                text_format
            )

            sheet.write(
                row, 2,
                rec[2],
                amount_format
            )

            row += 1

        sheet.write(
            row, 1,
            'Total COGS',
            total_text_format
        )

        sheet.write(
            row, 2,
            total_cogs,
            total_format
        )

        row += 2

        gross_profit = (
            total_revenue -
            total_cogs
        )

        sheet.merge_range(
            row, 0, row, 2,
            '3. Gross Profit',
            section_format
        )

        row += 1

        sheet.write(
            row, 0,
            'Description',
            header_format
        )

        sheet.write(
            row, 1,
            'Amount (Currency)',
            header_format
        )

        row += 1

        sheet.write(
            row, 0,
            'Gross Profit',
            text_format
        )

        sheet.write(
            row, 1,
            gross_profit,
            amount_format
        )

        row += 3

        salaries = 0.0
        rent_utilities = 0.0
        marketing = 0.0
        depreciation = 0.0

        other_expenses = self._get_account_balance([
            'expense'
        ])

        total_operating_expenses = (
            salaries +
            rent_utilities +
            marketing +
            depreciation +
            other_expenses
        )

        sheet.merge_range(
            row, 0, row, 2,
            '4. Operating Expenses',
            section_format
        )

        row += 1

        for i, header in enumerate(headers):
            sheet.write(
                row,
                i,
                header,
                header_format
            )

        row += 1

        expense_data = [
            [1, 'Salaries & Wages', salaries],
            [2, 'Rent / Utilities', rent_utilities],
            [3, 'Marketing / Advertising', marketing],
            [4, 'Depreciation', depreciation],
            [5, 'Other Operating Expenses', other_expenses],
        ]

        for rec in expense_data:

            sheet.write(
                row, 0,
                rec[0],
                text_format
            )

            sheet.write(
                row, 1,
                rec[1],
                text_format
            )

            sheet.write(
                row, 2,
                rec[2],
                amount_format
            )

            row += 1

        sheet.write(
            row, 1,
            'Total Operating Expenses',
            total_text_format
        )

        sheet.write(
            row, 2,
            total_operating_expenses,
            total_format
        )

        row += 2

        operating_profit = (
            gross_profit -
            total_operating_expenses
        )

        sheet.merge_range(
            row, 0, row, 2,
            '5. Operating Profit / EBIT',
            section_format
        )

        row += 1

        sheet.write(
            row, 0,
            'Operating Profit / EBIT',
            text_format
        )

        sheet.write(
            row, 1,
            operating_profit,
            amount_format
        )

        row += 3

        interest_income = 0.0
        interest_expense = 0.0
        other_non_operating = 0.0

        total_non_operating = (
            interest_income -
            interest_expense +
            other_non_operating
        )

        sheet.merge_range(
            row, 0, row, 2,
            '6. Non-Operating Income & Expenses',
            section_format
        )

        row += 1

        for i, header in enumerate(headers):
            sheet.write(
                row,
                i,
                header,
                header_format
            )

        row += 1

        non_operating_data = [
            [1, 'Interest Income', interest_income],
            [2, 'Interest Expense', interest_expense],
            [3, 'Other Non-Operating Income / Expenses',
             other_non_operating],
        ]

        for rec in non_operating_data:

            sheet.write(
                row, 0,
                rec[0],
                text_format
            )

            sheet.write(
                row, 1,
                rec[1],
                text_format
            )

            sheet.write(
                row, 2,
                rec[2],
                amount_format
            )

            row += 1

        sheet.write(
            row, 1,
            'Total Non-Operating Income / Expenses',
            total_text_format
        )

        sheet.write(
            row, 2,
            total_non_operating,
            total_format
        )


        row += 2

        profit_before_tax = (
            operating_profit +
            total_non_operating
        )

        sheet.merge_range(
            row, 0, row, 2,
            '7. Net Profit Before Tax (PBT)',
            section_format
        )

        row += 1

        sheet.write(
            row, 0,
            'Net Profit Before Tax',
            text_format
        )

        sheet.write(
            row, 1,
            profit_before_tax,
            amount_format
        )

        row += 3

        income_tax = 0.0
        total_tax = income_tax

        sheet.merge_range(
            row, 0, row, 2,
            '8. Tax Expense',
            section_format
        )

        row += 1

        for i, header in enumerate(headers):
            sheet.write(
                row,
                i,
                header,
                header_format
            )

        row += 1

        sheet.write(
            row, 0,
            1,
            text_format
        )

        sheet.write(
            row, 1,
            'Income Tax',
            text_format
        )

        sheet.write(
            row, 2,
            income_tax,
            amount_format
        )

        row += 1

        sheet.write(
            row, 1,
            'Total Tax',
            total_text_format
        )

        sheet.write(
            row, 2,
            total_tax,
            total_format
        )

        row += 2

        net_profit_after_tax = (
            profit_before_tax -
            total_tax
        )

        sheet.merge_range(
            row, 0, row, 2,
            '9. Net Profit / Loss After Tax (PAT)',
            section_format
        )

        row += 1

        sheet.write(
            row, 0,
            'Net Profit / Loss After Tax',
            text_format
        )

        sheet.write(
            row, 1,
            net_profit_after_tax,
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
            'name': 'Profit_Loss_Statement.xlsx',
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