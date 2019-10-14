#!/usr/bin/python3

"""
See README.MD
"""

from urllib.parse import quote

try:
    with open('auth.cfg', 'r') as auth:
        auth_path = auth.readline().rstrip()
except:
    auth_path = None
    pass
auth = '-H "Authorization: Basic $(cat %s | base64)"'%(auth_path) if auth_path is not None else None

def get_curl_response(curl):
    print(curl)
    import os, json
    os.system('%s | python -m json.tool > response.json'%(curl))
    with open('response.json', 'r') as f:
        response = json.load(f)
        return response

def list_files(response, kw):
    print("Files found with search path:")
    for file in response:
        print(file['path'])
        if not 'files' in kw:
            print("versions:")
            oldest_v, oldest_s = file['fileVersions'][0]['lastModified'], file['fileVersions'][0]['snapshotId']
            print("oldest: %s snapshot: %s"%(oldest_v, oldest_s))
            newest_v, newest_s = file['fileVersions'][-1]['lastModified'], file['fileVersions'][-1]['snapshotId']
            print("newest: %s snapshot: %s \n"%(newest_v, newest_s))
            if 'expand' in kw:
                print("Expanded Version List:")
                for fv in file['fileVersions']:
                    print("date: %s snapshot: %s"%(fv['lastModified'], fv['snapshotId']))
                print("\n")
        

def fileset(name, host, search, **kw):
    """
        searches name / host for FS ID and lists files matching search-path and associated snapshots.
    """
    header = "--header 'Accept: application/json'"
    url = "'https://%s/api/v1/fileset?name=%s&host_name=%s'"%(cdm,name,host)
    curl = "curl -s -X GET %s %s %s --insecure"%(auth, header, url)
    response = get_curl_response(curl)
    fileSetId = None
    if response['total'] > 1:
        print("Found more than 1 fileSet with name: %s & host: %s"%(name, host))
        for fId in response['data']:
            print("name: %s id: %s"%(fId['name'], fId['id']))
            if name == fId['templateName']:
                fileSetId = fId
    else:
        if response['total'] > 0:
            fileSetId = response['data'][0]
        else:
            print("No entries found for provided fileset/host combination")
            return
    
    print("Using %s -- %s"%(fileSetId['name'], fileSetId['id']))
    url = "'https://%s/api/v1/fileset/%s/search?path=%s'"%(cdm, quote(fileSetId['id'], safe=''), quote(search, safe=''))
    curl = "curl -s -X GET %s %s %s --insecure"%(auth, header, url)
    response = get_curl_response(curl)
    if response['total'] > 0:
        list_files(response['data'], kw)
    else:
        print("No files found matching provided using search string: %s in fileset: %s for host: %s"%(search, name, host))

def vm(name, search, **kw):
    """
        get VM ID:
    """
    header = "--header 'Accept: application/json'"
    url = "'https://%s/api/v1/vmware/vm?name=%s'"%(cdm,name)
    curl = "curl -s -X GET %s %s %s --insecure"%(auth,header, url)
    response = get_curl_response(curl)
    if not 'total' in response:
        try:
            print(response['message'])
        except:
            print(response)
        return
    if int(response['total']) > 1:
        print ("Multiple ID's found with the provided vmware name: %s"%(name))
        for resp in response['data']:
            print(response['data'][resp]['id'])
            return
    else:
        if response['total'] == 0:
            print("No vm id found with matching name: %s"%(name))
            return
        print("Found vm id matching name: %s"%(name))
        vmid=response['data'][0]['id']
        url = "'https://%s/api/v1/vmware/vm/%s/search?path=%s'"%(cdm,vmid, search)
        curl = "curl -s -X GET %s %s %s --insecure"%(auth, header, url)
        response = get_curl_response(curl)
        if response['total'] > 0:
            list_files(response['data'], kw)
        else:
            print("Not files found matching search string: %s in vm: %s"%(search, name))
def main():
    if auth is None:
        print("""
        Missing auth.cfg file
        Run:
            echo -n "<path-to-auth-file>" > auth.cfg
        Also required:
            echo -n "admin:password" > path-to-auth-file # Keep this file in safe place
        
        Example:
            echo -n "~/cdm_auth" > auth.cfg
            echo -n "admin:abcd1234" > ~/cdm_auth
        """)
        return
    import sys
    args = sys.argv
    global cdm
    try:
        cdm, objtype, name = args[1], args[2], args[3]
    except:
        if len(args) < 4:
            if len(args) < 3:
                if len(args) < 2:
                    print("Missing CDM IP")
                print("Missing objtype vm|fileset")
            print("Missing name")
        usage()
        return
    if objtype == 'fileset':
        try:
            host, searchString = args[4], args[5]
        except:
            if len(args) < 6:
                if len(args) < 5:
                    print("Missing field: Host")
                print("Missing search string")
            usage()
            return
        if len(args) > 6:
            kwArgs = args[6]
            if kwArgs == '--expand':
                fileset(name,host, searchString, expand=True)
            elif kwArgs == '--files':
                fileset(name,host, searchString, files=True)
            else:
                print("Unrecognized argument: %s"%(kwArgs))
                usage()
        else:
            fileset(name,host, searchString)
    elif objtype =='vm':
        if len(args) > 4: 
            searchString = args[4]
        else:
            print("Missing filed: searchString")
            usage()
            return
        if len(args) > 5:
            kwArgs = args[5]
            if kwArgs == '--expand':
                vm(name, searchString, expand=True)
            elif kwArgs == '--files':
                vm(name, searchString, files=True)
            else:
                print("Unrecognized argument: %s"%(kwArgs))
                usage()
        else:
            vm(name, searchString)
    else:
        print("Unrecognized argument " + objtype + "\nExpected fileset|vm" )
        usage()
def usage():
    print("""
        Usage: search.py <cdm_ip> <vm> <name> <searchString> [--files|--expand]

        Usage: search.py <cdm_ip> <fileset> <name> <host> <searchString> [--files|--expand]

        --files: view file names only 
    """)

if __name__ == '__main__':
    main()