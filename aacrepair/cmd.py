"""Module runs aacrepair on commandline with menu options.

Please check ``error_dict`` message, if instance fails to repair.
"""
import os
import pathlib
from aacrepair import AacRepair
from aacrepair import header_aac

idle_msg = r'nothing to do ... "E" Exit'
exit_msg = '\n  Thank you for using AacRepair.'
menu_file_msg = 'Single File aac or aacPlus'
menu_folder_msg = 'Bulk Repair, Folder'


def menu_main():
    """Main menu to choose from."""
    option_msg = 'Invalid option. Please enter a number between 1 and 3.'

    print('\n\tMenu "Main"')
    menu_options_dict = {
        1: menu_file_msg,
        2: menu_folder_msg,
        3: 'Exit',
    }

    while 1:
        for key in menu_options_dict.keys():
            print(key, '--', menu_options_dict[key])
        try:
            option = int(input('Enter your choice: '))
        except ValueError:
            print(option_msg)
            continue
        if option == 1:
            file_repair()
            break
        elif option == 2:
            bulk_repair()
            break
        elif option == 3:
            print(exit_msg)
            exit()
        else:
            print(option_msg)
    return


def bulk_repair():
    """Input loop to repair a whole folder of aac files.

    :methods: prepare_path_write_bulk: create instance with folder and export path argument
    """
    print(f'\nType "E" to Exit\n'
          f'\n\t{menu_folder_msg}\n')
    while True:
        print('(A) Type folder, repaired in <folder>/aac_repair .\n'
              '(B) type /folder/foo /cloud/bar ,for custom export path.\n')
        line_input = input(r'Enter a path, OS syntax (f:\10 or /home ) -->:')
        aac_path = line_input.strip()
        if not len(aac_path):
            print(idle_msg)
        else:
            if len(aac_path) > 1:
                prepare_path_run_write_bulk(aac_path)
                break
            else:
                if (aac_path == 'E') or (aac_path == 'E'.lower()):
                    print(exit_msg)
                    break


def prepare_path_run_write_bulk(aac_path):
    """Prepare path arguments to feed the repair instance

    :params: aac_path: src directory arg[0] dst directory arg[1]
    :methods: instance_repair_bulk: create instance with default folder or export path
    """
    path_list = aac_path.split(' ')
    default_path = path_list[0]
    export_path = path_list[1] if len(path_list) > 1 else None
    if pathlib.Path(default_path).is_dir():
        if export_path:
            instance_repair_bulk(default_path, export_path=True)
        else:
            instance_repair_bulk(default_path)
        print(f'{exit_msg}')
    else:
        print(f"  Folder {default_path}\nis not readable. Exit\n{exit_msg}")


def instance_repair_bulk(aac_path, export_path=None):
    """Create instance with option for custom export folder.

    :params: aac_path: src directory
    :params: export_path: this function calls the setter to change export directory
    """
    aacRepair = AacRepair(aac_path)
    if export_path:
        aacRepair.set_export_path(export_path)
    return aacRepair.repair()


def file_repair():
    """Input loop to repair a single aac file.

    :methods: repair_write_one_file: read, repair and store renamed file
    """
    print(f'\nType "E" to Exit\n'
          f'\n\t{menu_file_msg}')
    while True:
        line_input = input(r'Path, OS syntax (f:\10\foo.aac or /home/foo.aac ) -->:')
        aac_path = line_input.strip()

        if not len(aac_path):
            print(idle_msg)
        else:
            if len(aac_path) > 1:
                if pathlib.Path(aac_path).is_file():
                    repair_write_one_file(aac_path)
                    print(f'{exit_msg}')
                else:
                    print(f"\n  File is not readable. Exit\n{exit_msg}")
                break
            else:
                if (aac_path == 'E') or (aac_path == 'E'.lower()):
                    print(exit_msg)
                    break


def repair_write_one_file(aac_path, name_prefix=None, print_out=True):
    """Repair a single aac or aacPlus file and writes it with a name prefix.

    :param: aac_path: file path
    :param: name_prefix: distinguish the file from defective one
    :param: print_out: None disables print to screen

    :methods: header_dict.header_info: header bits to property dictionary
    :return: AAC frame header for further processing
    :rtype: dict
    """
    if aac_path[-5:] == ".aacp" or aac_path[-4:] == ".aac":

        aacRepair = AacRepair()
        rep_object = aacRepair.repair_object(aac_path)  # instance method converts file path content to bytes

        file_name_path, file_name = os.path.split(aac_path)
        if rep_object:
            prefix = name_prefix if name_prefix else "_aacrepair_"
            new_f_name = os.path.join(file_name_path, prefix + file_name)
            with open(new_f_name, 'wb') as binary_writer:
                binary_writer.write(rep_object)

            if print_out:
                h_dict = header_aac.header_info(rep_object, frame_bytes=None, print_out=True)
                cut_bytes = aacRepair.file_size_dict[aac_path] - len(rep_object)
                print(f'\nNew file name: {new_f_name}\nCut: {cut_bytes} bytes')
            else:
                h_dict = header_aac.header_info(rep_object, print_out=None)
            return h_dict
        else:
            if print_out:
                print(f'\nFile content Error\nReturn value: {rep_object}')
                if aac_path in aacRepair.error_dict.keys():
                    print(f'\nError dictionary value: {aacRepair.error_dict[aac_path]}')
    else:
        if print_out:
            print('\nNo aac file - Exit')


def main():
    """Call menu_main to start the module from command line."""
    menu_main()


if __name__ == '__main__':
    main()
