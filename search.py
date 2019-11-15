#!/usr/bin/env python

"""
See README.MD
"""

from urllib.parse import quote
import os

def get_auth_path():
    try:
        with open('auth.cfg', 'r') as auth:
            auth_path = auth.readline().rstrip()
            with open(auth_path, 'r') as testOpen:
                pass
            return auth_path
    except: 
        return None
auth_path = get_auth_path()
try:
    if auth_path == None:
        print("trying environment variables")
        with open('temp.cfg', 'w') as auth:
            user = os.environ['user'].rstrip()
            pw = os.environ['password'].rstrip()
            auth.write(f'{user}:{pw}')
        with open('temp.cfg', 'r') as auth:
            auth_path = os.path.realpath(auth.name)
        with open('auth.cfg', 'w') as authcfg:
            authcfg.write(auth_path)
        auth_path=get_auth_path()
except:
    print("missing environment variables user|password")
    auth_path = None

auth = '-H "Authorization: Basic $(cat %s | base64)"'%(auth_path) if auth_path is not None else None

def log(obj, kw):
    if 'debug' in kw:
        print(obj)

def get_curl_response(curl, kw):
    log("Request: %s"%(curl), kw)
    import os, json
    os.system('%s | python -m json.tool > response.json'%(curl))
    with open('response.json', 'r') as f:
        response = json.load(f)
        log("Response: %s"%(response), kw)
        return response

def list_files(response, kw):
    print("Files found with search path:")
    for file in response:
        if 'path' in file:
            print(file['path'])
        else:
            print("File:  ", file)
            pint("Oops something bad happened here")
            break
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
        
def hostGroup(host, search, **kw):
    header = "--header 'Accept: application/json'"
    url = "'https://%s/api/v1/host?hostname=%s'"%(cdm,host)
    curl = "curl -s -X GET %s %s %s --insecure"%(auth, header, url)
    response = get_curl_response(curl, kw)
    if response['total'] > 1:
        print("Found more than 1 host with name: %s"%(host))
    for hId in response['data']:
        hostId = hId['id']
        break
    header = "--header 'Accept: application/json'"
    url = "'https://%s/api/v1/host/%s/search?path=%s'"%(cdm, quote(hostId, safe=''), quote(search, safe=''))
    curl = "curl -s -X GET %s %s %s --insecure"%(auth, header, url)
    response = get_curl_response(curl, kw)
    if response['total'] > 0:
        list_files(response['data'], kw)
    else:
        print("No files found matching provided using search string: %s in for host: %s"%(search, host))


def fileset(name, host, search, **kw):
    """
        searches name / host for FS ID and lists files matching search-path and associated snapshots.
    """
    header = "--header 'Accept: application/json'"
    url = "'https://%s/api/v1/fileset?name=%s&host_name=%s'"%(cdm,name,host)
    curl = "curl -s -X GET %s %s %s --insecure"%(auth, header, url)
    response = get_curl_response(curl, kw)
    fileSetId = None
    if not 'total' in response:
        print("response indicated an issue")
        print(response)
        return
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
    response = get_curl_response(curl, kw)
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
    response = get_curl_response(curl, kw)
    if not 'total' in response:
        try:
            print(response['message'])
        except:
            print(response)
        return
    ind = 0
    if int(response['total']) > 1:
        vmsFound = name + ' | '
        for i, vm_config in enumerate(response['data']):
            if vm_config['name'] == name:
                ind = i
            else:
                vmsFound = vmsFound + vm_config['name'] + ' | '
        print("Multiple VM's found matching provided vm name: %s"%(vmsFound))
    if response['total'] == 0:
        print("No vm id found with matching name: %s"%(name))
        return
     
    print("Found vm id matching name: %s"%(name))
    vmid=response['data'][ind]['id']
    url = "'https://%s/api/v1/vmware/vm/%s/search?path=%s'"%(cdm,vmid, search)
    curl = "curl -s -X GET %s %s %s --insecure"%(auth, header, url)
    response = get_curl_response(curl, kw)
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
    if objtype == 'host':
        try:
            host, searchString = args[3], args[4]
        except:
            if len(args) < 5:
                if len(args) < 4:
                    print("Missing field: Host")
                print(args)
                print("Missing search string")
        if len(args) > 5:
            kwArgs = args[5]
            if kwArgs == '--expand':
                hostGroup(host, searchString, expand=True)
            elif kwArgs == '--files':
                hostGroup(host, searchString, files=True)
            elif kwArgs == '--debug':
                hostGroup(name, searchString, debug=True)
            else:
                print("Unrecognized argument: %s"%(kwArgs))
                usage()
                return
        else:
            hostGroup(host, searchString)

    elif objtype == 'fileset':
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
            elif kwArgs == '--debug':
                fileset(name, searchString, debug=True)
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
            elif kwArgs == '--debug':
                vm(name, searchString, debug=True)
            else:
                print("Unrecognized argument: %s"%(kwArgs))
                usage()
        else:
            vm(name, searchString)
    else:
        print("Unrecognized argument " + objtype + "\nExpected fileset|vm|host" )
        usage()
def usage():
    print("""
        Usage: search.py <cdm_ip> <host> <hostname> <searchString> [--files|--expand]

        Usage: search.py <cdm_ip> <vm> <name> <searchString> [--files|--expand]

        Usage: search.py <cdm_ip> <fileset> <name> <host> <searchString> [--files|--expand]

        --files: view file names only 
        --expand: view all files versions, instead of just oldest / newest
        --debug: print curl commands to screen
    """)

if __name__ == '__main__':
    main()