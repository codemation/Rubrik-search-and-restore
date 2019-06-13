# Rubrik-search-and-restore
*Purpose:* 
  Provide a cli method of searching indexed files within virtual-machine & fileset snapshots. This information can then be  applied 
for generating a downloadable link for restoration / verifications purposes. 

1. Create an credentials file, containing 'username|pw'. 
    Method: echo -n 'admin:abcd1234' > ~/special_cdm_auth

2. Update auth.cfg within search_and_restore package with credential file location. 
    Method echo -n '~/special_cdm_auth' > auth.cfg

3. Use search.py to find files within fileset or virtual machine backups.

4. Using file(s) & path(s), with snapshot uuid, generate a downloadable link using restore.py which is provided with associated curl command to download.

*Search.py:*

        Usage: search.py <cdm_ip> <vm> <name> <searchString> [--files|--expand]

        Usage: search.py <cdm_ip> <fileset> <name> <host> <searchString> [--files|--expand]

        --files: view file names only 
    Example: (virtual Machine)
        python3 search.py 10.35.36.165 vm jjamison-ubu16 /home/rksupport/data/
        Out:
            /home/rksupport/data/71.txt
            versions:
            oldest: 2019-03-20T12:18:25+0000 snapshot: cd8ac1b4-10a7-45a1-ad21-55700c51d369
            newest: 2019-03-20T12:18:25+0000 snapshot: 7dd06b60-2af6-4d83-a807-1f6526ac0ced 

            /home/rksupport/data/31.txt
            versions:
            oldest: 2019-03-20T12:18:25+0000 snapshot: cd8ac1b4-10a7-45a1-ad21-55700c51d369
            newest: 2019-03-20T12:18:25+0000 snapshot: 7dd06b60-2af6-4d83-a807-1f6526ac0ced 

            /home/rksupport/data/67.txt
            versions:
            oldest: 2019-03-20T12:18:25+0000 snapshot: cd8ac1b4-10a7-45a1-ad21-55700c51d369
            newest: 2019-03-20T12:18:25+0000 snapshot: 7dd06b60-2af6-4d83-a807-1f6526ac0ced 

    Example: (Fileset)
        In:
            python3 search.py 10.35.36.165 fileset data 10.35.36.253 /home/rksupport/ 
        Out:
            /home/rksupport/data/2.txt
            versions:
            oldest: 2019-03-20T12:18:25+0000 snapshot: 77821b62-e319-4ab7-b5a1-ad0032871322
            newest: 2019-03-20T12:18:25+0000 snapshot: a54eacdd-760f-4114-b834-6c2384412af6 

            /home/rksupport/data/25.txt
            versions:
            oldest: 2019-03-20T12:18:25+0000 snapshot: 77821b62-e319-4ab7-b5a1-ad0032871322
            newest: 2019-03-20T12:18:25+0000 snapshot: a54eacdd-760f-4114-b834-6c2384412af6 

*restore.py*
    Usage:
        restore.py <cdm_ip> <vm|fileset> <object_name> <snapshot_id> <filepaths>
    Example: (Virtual machine)
        In:
            python3 restore.py 10.35.36.165 vm jjamison-ubu16 7dd06b60-2af6-4d83-a807-1f6526ac0ced /home/rksupport/test/71.txt,/home/rksupport/data/31.txt
        Out:
            Use the following command to download the specified files: 
            curl -s -H "Authorization: Basic $(cat ~/cdm_auth | base64)" 'https://10.35.36.165/download_dir/Ws3zz1gb1sV3cm2DVXlp.zip' -o Rubrik-Download-Ws3zz1gb1sV3cm2DVXlp.zip --insecure
    Example: (Fileset)
        In:
            python3 restore.py 10.35.36.165 fileset data a54eacdd-760f-4114-b834-6c2384412af6 /home/rksupport
        Out:
            Successfully Completed Generation of FileDownload
            
            Use the following command to download the specified files: 
            curl -s -H "Authorization: Basic $(cat ~/cdm_auth | base64)" 'https://10.35.36.165/download_dir/4Afql4qsPlVwkvnN5yei.zip' -o rksupport.zip --insecure

"""
