aacRepair - PyPi, GitHub (short) documentation
==============================================
repair aac and aacPlus files grabbed from the internet

![Tests](https://github.com/44xtc44/aacRepair/actions/workflows/tests.yml/badge.svg?branch=dev)

Info
----
AAC files consist of multiple segments, frames. Each frame has a header and a payload. 
Browser gets stuck if AAC file frame is defective and will not start to play or refuse to play next AAC file.
This will stop the entire playlist.
File gets trimmed from head to tail, to remove defective frames. 
Cut off byte count is shown in the summary.

Command Line
------------
    
    $ aacrepair  # run exec Script
    $ python -m aacrepair.cmd  # if Python path for script failed
    
Menu

            Menu "Main"
    1 -- Single File aac or aacPlus
    2 -- Bulk Repair, Folder
    3 -- Exit
    Enter your choice: 2
   
Folder

	Bulk Repair, Folder

    (A) Type folder, repaired in <folder>/aac_repair .
    (B) type /folder/foo /cloud/bar ,for custom export path.

    Enter a path, OS syntax (f:\10 or /home ) -->:f:\10 f:\10\repaired_aac



aacrepair Module 
----------------

bulk repair
-----------

    from aacrepair import AacRepair
    
    # 'r' before a string tells the Python interpreter to treat backslashes as a literal (raw) character
    aacRepair = AacRepair(r"F:\propaganda-podcasts")
    # setter overrides default export path 'F:\propaganda-podcasts\aac_repair' 
    aacRepair.set_export_path(r"F:\repaired_foobar")
    aacRepair.repair()
    
Instantiate AacRepair class with two possible arguments, mandatory folder path and optional dictionary. 
1. No dictionary provided. Folder path is used as list to import files into a dictionary AND store repaired files.
2. A dictionary of files is provided. Folder path is used to store repaired files. (best use on web server)


Web Server
   * Endpoint converts multi-file upload from file storage type to bytestream, uses .read() method
   * List of files is written to dictionary {file_name_key: file_byte_content_value}
   * web server gets not the file path, only file name - needs path to store repaired files
   * dictionary {file(n).aac: b'\x65\x66\x67\x00\x10\x00\x00\x00\x04\x00'}

    files = request.files.getlist('fileUploadAcpRepair')
    f_dict = {f: open(f, "rb").read() for f in files if f[-5:] == ".aacp" or f[-4:] == ".aac"}
    aacRepair = AacRepair("/home/Kitty/aac_files", f_dict)
    aacRepair.repair()

File System
* List of files in folder is written to dictionary {file_name_key: file_byte_content_value}


     aacRepair = AacRepair("/home/Kitty/meow_aac")
     aacRepair.set_export_path("/home/Kitty/foo")
     aacRepair.repair()

single object
-------------

``head`` and ``tail`` are used to cut chunks left or right only

    aacRepair = AacRepair()
    # converts file path to file content, if object is not of type bytes
    rep_object = aacRepair.repair_object(aac_path_or_object, head=None, tail=None)


header_aac Module
-----------------
Use as input for further aac stream processing or repair.

    from aacrepair import header_aac

header_aac module example to show all frames with header.

    header_aac.pull_frame('/home/foo/bar.aac')


header_aac dictionary output
----------------------------

header_aac dictionary output of ``header_info(aac_object, frame_bytes=None, print_out=True)``

    SYNC_WORD_BOOL: True 
    MPEG4_BOOL: True 
    Layer_BOOL: True 
    CRC_16_IS_SET_BOOL: False 
    PROFILE_INT: 1 
    PROFILE_STR: AAC Main 
    SAMPLING_FREQUENCY_INT: 3 
    SAMPLING_FREQUENCY_STR: 48000 Hz 
    PRIVATE_BIT_BOOL: False 
    CHANNEL_CONFIG_INT: 2 
    CHANNEL_CONFIG_STR: 2 channels: front-left, front-right 
    ORIGINALITY_BOOL: False 
    HOME_BOOL: False 
    COPYRIGHT_ID_INT: 0 
    COPYRIGHT_START_INT: 0 
    FRAME_LENGTH_INT: 530 
    BIT_RESERVOIR_INT: 2047 
    FRAME_NUMBER_INT: 0 
    CRC_16: {} 
    IS_LAST_FRAME_BOOL: False 
    ERROR_STR:  
    FRAME_BYTES: b'' 


Bytes

       ======== ======== ======== ======== ======== ======== ======== ======== ========
            1       2       3        4        5        6        7        8        9
       ======== ======== ======== ======== ======== ======== ======== ======== ========
       AAAAAAAA AAAABCCD EEFFFFGH HHIJKLMM MMMMMMMM MMMOOOOO OOOOOOPP QQQQQQQQ QQQQQQQQ
       ======== ======== ======== ======== ======== ======== ======== ======== ========

Bit Groups

       ===== ========= ====== ====================================================================================
       Group    Number  Count  Description
       ===== ========= ====== ====================================================================================
       A         0-12    12 	Syncword, all bits 1
       B           13       1 	MPEG Version set 0 is MPEG-4, set 1 MPEG-2
       C        14-15       2 	Layer set to 0
       D           16       1 	[[[ ``Warning`` ]]], set to 1 if there is no CRC and 0 if there is CRC
       E        17-18       2 	Profile, the MPEG-4 Audio Object Type https://en.wikipedia.org/wiki/MPEG-4_Part_3
       F        19-22       4 	MPEG-4 Sampling Frequency  https://wiki.multimedia.cx/index.php/MPEG-4_Audio
       G           23       1 	Private bit set to 0,
       H        24-26       3 	MPEG-4 Channel Configuration https://wiki.multimedia.cx/index.php/MPEG-4_Audio
       I           27       1 	Originality, set 1 originality of audio, else 0
       J           28       1 	Home, set to 1 to signal home usage of the audio, else 0
       K           29       1 	Copyright ID bit
       L           30       1 	Copyright ID start
       M        31-43      13 	Frame length of ADTS frame including headers and CRC check - 1
       O        44-54      11 	Buffer fullness, states the bit-reservoir per frame
       P        55-56       2 	Number of AAC ADTS frame minus 1
       Q        57-72      16 	CRC check
       ===== ========= ====== ====================================================================================


pip install
-----------
    """ Linux """
    $ pip3 install aacrepair

    """ Windows """
    > pip install aacrepair


Uninstall
---------
Python user:

* find the module location
* uninstall and then remove remnants

>$ pip3 show aacrepair

>$ pip3 uninstall aacrepair

Location: ... /python310/site-packages

What's next - contributions welcome
-----------------------------------
- try multithread a test
- multiprocessing plus multithreading repair, if file count is x (works only on linux)
- android 'Threading in Worker', make it run
