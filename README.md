aac Repair
==========
repair aac and aacPlus files grabbed from the internet

Info
----
Aac files consist of multiple segments, frames. Each frame has a header and payload. 
Browser get stuck if aac file frame is defective and will not start to play or refuse to play next aac file.
This will stop the entire playlist.
File gets trimmed from head to tail, to remove defective frames. 
Cut off byte count is shown in the summary.

Usage
-----
    from aacrepair import AacRepair
    
    # 'r' before a string tells the Python interpreter to treat backslashes as a literal (raw) character
    aacRepair = AacRepair(r"F:\propaganda-podcasts")
    aacRepair.repair()
    
Instantiate AacRepair class with two possible arguments, mandatory folder path and optional dictionary. 
1. No dictionary provided. Folder path is used as list to import files into a dictionary AND store repaired files.
2. A dictionary of files is provided. Folder path is used to store repaired files. (best use on web server)


Web Server
* endpoint converts uploaded files from file storage type to bytestream, use .read() function
   * web server gets not the file path, only file name - needs path to store repaired files
   * dictionary {file(n).aac: b'\x65\x66\x67\x00\x10\x00\x00\x00\x04\x00'}

::

    files = request.files.getlist('fileUploadAcpRepair')
    f_dict = {f: open(f, "rb").read() for f in files if f[-5:] == ".aacp" or f[-4:] == ".aac"}
    aacRepair = AacRepair("/home/Kitty/aac_files", f_dict)
    aacRepair.repair()

File System
* List of files in folder is written to dictionary {file_name_key: file_byte_content_value}

::

    aacRepair = AacRepair("/home/Kitty/aac_files")
    aacRepair.repair()



pip install
-----------
    """ Linux """
    $ pip3 install aacrepair

    """ Windows """
    > pip install aacrepair


Uninstall
---
Python user:

* find the module location
* uninstall and then remove remnants

>$ pip3 show aacrepair

>$ pip3 uninstall aacrepair

Location: ... /python310/site-packages
