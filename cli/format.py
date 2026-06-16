def format_table(columns, results):
    results = results[:15]
    column_widths = []
    # find max width of each column
    column_row = ['|']
    for i, col in enumerate(columns):
        col = col.name
        column_widths.append(max([len(col)] + [len(str(row[i])) for row in results]))
        column_row.append(f' {col:<{column_widths[i]}} |')
    
    to_print = [''.join(column_row)]
    total_width = len(to_print[0])
    break_row = '-' * total_width
    to_print.append(break_row)

    for row in results:
        row_to_print = ['|']
        for i, col in enumerate(row):
            row_to_print.append(f' {str(row[i]):<{column_widths[i]}} |')
        to_print.append(''.join(row_to_print))
    
    return '\n'.join(to_print)