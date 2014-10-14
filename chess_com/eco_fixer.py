if __name__ == '__main__':
    import re

    raw_lines = open('eco_raw.txt', 'r').readlines()
    fixed_lines = []

    expression = re.compile('(?<=^\d{1}) |(?<= \d{1}) |(?<= \d{2}) ',
        re.MULTILINE)

    for line_num, line_content in enumerate(raw_lines):
        if line_num % 2 == 0:
            fixed_lines.append(line_content)
        else:
            fixed_line = re.sub(expression, '.', line_content)
            fixed_lines.append(fixed_line)

    result = 'eco_mapping = {\n'
    for i in xrange(0, len(fixed_lines), 2):
        info_line = fixed_lines[i].strip()
        moves_line = fixed_lines[i + 1].strip()

        result += '\t"%s": "%s",\n' % (moves_line, info_line)
    result += '}'

    fixed_file = open('eco_mapping.py', 'w')
    fixed_file.write(result)
