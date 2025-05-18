def base_structure_creation(section_list):
    base_structure = []

    is_supported = True

    for section in section_list:

        if section[1] is None:
            raise ValueError

        if section[1][0] in ['W','E']:
            is_supported = False

        base_structure.append(section[1])

    return is_supported, ''.join(base_structure)
