
def other_detection(section_list):
    other_list = []
    index = 0
    while index < len(section_list):
        if section_list[index][1] is None:
            section_list[index] = (section_list[index][0],'S' + str(len(section_list[index][0])) )
            other_list.append(section_list[index][0])
        index += 1
    return other_list
