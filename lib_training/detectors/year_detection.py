def detect_year(section):
    working_string = section[0]
    parsing = []


    year_prefix = ['19','20']

    for prefix in year_prefix:

        start = 0
        while True:
            start_index = working_string[start:].find(prefix)
            if start_index == -1:
                break
            start_index += start
            if len(working_string) < start_index + 4:
                break
            start = start_index + 2
            if start_index != 0:
                if working_string[start_index -1].isdigit():
                    continue
            if start_index + 4 < len(working_string):
                if working_string[start_index + 4].isdigit():
                    continue
            if working_string[start_index + 2].isdigit():
                if working_string[start_index + 3].isdigit():
                    year = working_string[start_index:start_index + 4]
                    if start_index != 0:
                        parsing.append((working_string[0:start_index], None))
                    parsing.append((working_string[start_index:start_index+4],'Y1'))
                    if start_index +4 < len(working_string):
                        parsing.append((working_string[start_index+4:], None))
                    return parsing, year

    return section, None


def year_detection(section_list):
    year_list = []

    index = 0
    while index < len(section_list):

        if section_list[index][1] is None:

            parsing, year = detect_year(section_list[index])

            if year:
                year_list.append(year)
                del section_list[index]
                section_list[index:index] = parsing
                continue

        index += 1

    return year_list
