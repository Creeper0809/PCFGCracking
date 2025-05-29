def _detect_digits(section):
    working_string = section[0]
    parsing = []
    is_run = False
    start_pos = -1

    for pos, value in enumerate(working_string):
        if value.isdigit():
            if not is_run:
                is_run = True
                start_pos = pos
        if not value.isdigit() or pos == len(working_string) - 1:
            if is_run:
                if start_pos !=0:
                    parsing.append((section[0][0:start_pos],None))
                if value.isdigit():
                    end_pos = pos
                else:
                    end_pos = pos - 1
                found_digit = ''.join(section[0][start_pos:end_pos + 1])

                parsing.append((found_digit,'D' + str(len(found_digit)) ))
                if end_pos != len(section[0]) -1:
                    parsing.append((section[0][end_pos+1:],None))

                return parsing, found_digit

    return section, None

def digit_detection(section_list):
    digit_list = []
    index = 0
    while index < len(section_list):

        if section_list[index][1] is None:

            parsing, digit_string = _detect_digits(section_list[index])

            if digit_string is not None:
                digit_list.append(digit_string)

                del section_list[index]
                section_list[index:index] = parsing
        index += 1

    return digit_list
