#!/usr/bin/python3

"""
Created for assisting with CLI Restoration
restore.py is dependent on admin-credentials file with username/password of user with appropiate permissions to CDM.
see readme.md
"""

import os
import datetime, time

try:
    with open('auth.cfg', 'r') as auth:
        auth_path = auth.readline().rstrip()
except:
    auth_path = None
    pass
auth = '-H "Authorization: Basic $(cat %s | base64)"'%(auth_path) if auth_path is not None else None

headers = " --header 'Content-Type: application/json' --header 'Accept: application/json'"

def jsonify_path(toConvert):
    """
        converts a single or comma separated set of path inputs into a stringified list ["path","path","path"] to be used by curl
    """
    files = '['
    if toConvert.split(',')[0] == toConvert:
        path_split = toConvert
        files = files + '"' + path_split + '"'
    else:
        path_split = toConvert.split(',')
        for f in path_split:
            files = files + '"' + f + '"'
            if not path_split.index(f) == len(path_split) -1:
                files = files + ','
    files = files + ']'
    if '\\' in files:
        if ',' in files:
            multi = []
            multi_files = files.split(',')
            for f in multi_files:
                multi.append('\\\\'.join(f.split('\\')))
            escapedFiles = ','.join(multi)
            return escapedFiles
        else:    
            escapeFiles = '\\\\'.join(files.split('\\'))
            return escapeFiles
    return files

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
def volume_group(hostname, snapshotId, paths, **kw):
    files = jsonify_path(paths)
    pathString = "--data-binary '{"+ '"paths": %s }'%(files) + "'"
    url = " 'https://%s/api/internal/volume_group/snapshot/%s/download_files'"%(host, snapshotId)
    header = "-H 'Content-Type: application/json;charset=UTF-8' -H 'Accept: application/json, text/plain, */*'"
    curl = "curl -s -X POST %s %s %s %s --insecure"%(auth, header, pathString, url)
    before_curl_time = datetime.datetime.utcnow()
    response = get_curl_response(curl, kw)
    if not 'id' in response:
        try:
            log(response['message'], kw)
        except:
            log(response, kw)
        return
    jobInstanceId = response['id']
    get_download(hostname, jobInstanceId, before_curl_time, kw)


def fileset(object_name, snapshotId, paths, **kw):
    files = jsonify_path(paths)
    pathString = "--data-binary '{"+ '"sourceDirs": %s }'%(files) + "'"
    url = " 'https://%s/api/internal/fileset/snapshot/%s/download_files'"%(host, snapshotId)
    header = "-H 'Content-Type: application/json;charset=UTF-8' -H 'Accept: application/json, text/plain, */*'"
    curl = "curl -s -X POST %s %s %s %s --insecure"%(auth, header, pathString, url)
    before_curl_time = datetime.datetime.utcnow()
    response = get_curl_response(curl, kw)
    if not 'id' in response:
        try:
            log(response['message'], kw)
        except:
            log(response, kw)
        return
    jobInstanceId = response['id']
    get_download(object_name, jobInstanceId, before_curl_time, kw)

def vm(object_name, snapshotId, paths, **kw):
 
    files = jsonify_path(paths)
    url = " 'https://%s/api/internal/vmware/vm/snapshot/%s/download_files'"%(host, snapshotId)
    curl = "curl -s -X POST %s %s -d '{%s:%s}'"%(auth, headers,'"paths"', files) + url + ' --insecure'
    before_curl_time = datetime.datetime.utcnow()
    response = get_curl_response(curl, kw)
    if not 'id' in response:
        try:
            log(response['message'], kw)
        except:
            log(response, kw)
        return
    jobInstanceId = response['id']
    get_download(object_name, jobInstanceId, before_curl_time, kw)

def get_download(object_name, jobInstanceId, before_curl_time, kw):
    after_date = '%s-%s-%sT%s%%3A%s'%(before_curl_time.year, before_curl_time.month, before_curl_time.day, before_curl_time.hour, before_curl_time.minute)
    #url1 = "'https://%s/api/internal/event_series?event_type=Recovery&object_name=%s&after_date=%s'"%(host, object_name,after_date)
    url1 = "'https://%s/api/internal/event?event_type=Recovery&object_name=%s&after_date=%s'"%(host, object_name,after_date)
    curl1 = "curl -s -X GET %s %s "%(auth,headers) + url1 + ' --insecure'
    events = get_curl_response(curl1, kw)
    eventSeriesId = None
    version4 = True
    log("jobInstanceId: %s"%(jobInstanceId), kw)
    for event in events["data"]:
        if "jobInstanceId" in event:
            if jobInstanceId == event["jobInstanceId"]:
                log("Detected 5.X CDM", kw)
                version4 = False
    for event in events["data"]:
        if 'eventSeriesId' in event:
            if 'eventStatus' in event:
                if event['eventStatus'] == 'Success':
                    continue
            if 'status' in event:
                if event['stats'] == 'Success':
                    continue
            eventSeriesId = event['eventSeriesId']
            if version4 == True:
                url1_status = "'https://%s/api/internal/event_series/status?ids=%s'"%(host, eventSeriesId)
                curl1_status = "curl -s -X GET %s %s "%(auth, headers) + url1_status + ' --insecure'
            else:
                url1_status = "'https://%s/api/internal/event_series/status'"%(host)
                status_cfg = '[{"id": "%s", "jobInstanceId": "%s"}]'%(eventSeriesId, jobInstanceId) 
                curl1_status = "curl -s -X POST %s %s -d '%s' "%(auth, headers, status_cfg) + url1_status + ' --insecure'
                
            while True:
                ev_status = get_curl_response(curl1_status, kw)
                if 'data' in ev_status:
                    if not ev_status["data"][0]["progress"] == "100.00":
                        print("Waiting for Download Link to be generated %s %% completed"%(ev_status["data"][0]["progress"]))
                    else:
                        print("Successfully Completed Generation of FileDownload\n\n")
                        break
                elif "status" in ev_status:
                    if not ev_status["status"] == "Success":
                        print("Waiting for Download Link to be generated %s %% completed"%(ev_status["progressPercentage"]))
                    else:
                        print("Successfully Completed Generation of FileDownload\n\n")
                        break
                else:
                    print("Successfully Completed Generation of FileDownload\n\n")
                    break
                time.sleep(5)
    # Get generated download link # 
    url2 = "'https://%s/api/internal/event_series/%s?limit=2147483647'"%(host, eventSeriesId)
    curl2 = "curl -s -X GET %s %s "%(auth, headers) + url2 + ' --insecure'
    curl2_events = get_curl_response(curl2, kw)
    if 'eventDetailList' in curl2_events:
        curl2_events = curl2_events['eventDetailList']
    else:
        curl2_events = curl2_events["data"]

    success = None
    for ev in curl2_events: 
        if ev["status"] == "Success":
            success = ev
            break
        if ev["status"] == "Failure":
            print("Restore aborted with error: \n  %s"%(ev["eventInfo"]))
            return
    import json
    # Writes Job result to downloadpath.json to re-open
    with open('downloadpath.json','w') as ev_dl_json:
        log(success, kw)
        if 'eventInfo' in success: # 4.2
            ev_dl_json.write(success['eventInfo']) 
        else: # 5.X
            ev_dl_json.write(success['eventInfo']) 

        
    # reloads result as json
    with open('downloadpath.json', 'r') as f:
        ev_dl = json.load(f)
    
    restoreName = ev_dl['downloadInfo']['name']
    restorePath = ev_dl['downloadInfo']['path']
    url_dload = "'https://%s/%s'"%(host, restorePath)
    curl_dload = "curl -s %s %s -o %s --insecure"%(auth, url_dload, restoreName)
    print ("Use the following command to download the specified files: Note: This link is only valid for the next 24 hours\n %s"%(curl_dload))
    return curl_dload
def usage():
    print("""
    Usage:
        restore.py <cdm_ip> <vm|fileset|host> <object_name> <snapshot_id> <filepaths> [--debug] 
        --debug: print curl commands to screen
    Example:
        VirtualMachine:
            restore.py 192.168.10.100 vm prod-ubuntu 2f386a65-ce27-4a46-ba8d-1c0d3a72281d /home/rksupport/data/10.txt,/home/rksupport/data/100.txt,/home/rksupport/test
        Fileset:
            restore.py 10.35.36.165 fileset data 0b62f222-c332-4920-a2ce-b885c913b49d /home/rksupport/data/67.txt,/home/rksupport/data/64.txt
        VolumeGroup:
            restore.py 10.35.36.165 host 10.35.36.181 0ebfa6f3-3809-425d-b762-f9aa61735613 "F:\\test","F:\TestRestore\ProcessMonitor.zip"
    """)

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
    global host
    kwargs = {}
    try:
        host = args[1]
        print("Host is %s"%(host))
        objType, objName, snapId, filepaths = args[2], args[3], args[4], args[5]
        if len(args) > 6:
            debug = args[6]
            if debug == '--debug':
                kwargs['debug'] = True
            else:
                print("Unknown argument provided")
                usage()

    except:
        usage()
        return
    if objType == 'vm':
        vm(objName, snapId, filepaths, **kwargs)
    elif objType == 'fileset':
        fileset(objName, snapId, filepaths, **kwargs)
    elif objType == 'host':
        volume_group(objName, snapId, filepaths, **kwargs)
    else:
        usage()
if __name__ == "__main__":
    main()