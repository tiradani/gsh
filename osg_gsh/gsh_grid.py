import urllib
import platform
import libxml2

# Check to see if we are being called from python 2.5.x or greater.  If not,
# import our own subprocess convenience functions.  These functions were 
# introduced in python 2.5
py_ver = platform.python_version_tuple()
if int(py_ver[0]) == 2 and int(py_ver[1]) < 5:  # python version is 2.4.x
    from process_management import call
else:
    from subprocess import call

myosg_url = "http://myosg.grid.iu.edu/rgsummary/xml?datasource=summary&" \
             "summary_attrs_showfqdn=on&downtime_attrs_showpast=&" \
             "account_type=cumulative_hours&ce_account_type=gip_vo&" \
             "se_account_type=vo_transfer_volume&bdiitree_type=total_jobs&" \
             "bdii_object=service&bdii_server=is-osg&start_type=7daysago&" \
             "start_date=04%2F18%2F2012&end_type=now&end_date=04%2F18%2F2012&" \
             "all_resources=on&gridtype=on&gridtype_1=on&gridtype_2=on&" \
             "active_value=1&disable_value=1"

def buildGlobusCommand(site, line, env, cwd):
    """
    globus-job-run is the actual interface between GSH and the remote gatekeeper.
    This function builds the entire command line.  The command line is:
    
    globus-job-run site_fqdn preamble exports cd line postamble
    
    where:
        site_fqdn is the fully qualified domain name of the remote gatekeeper
        preamble is a string that checks the gatekeeper version and sources
            setup.sh if appropriate
        exports is a string containing 'export var=val' for all custom environment
            variables 
        cd is a string that cd's to the current wokring directory
        line is the command line that the user typed in
        postamble is the closing quotes for the entire command

    @param site: The fqdn for the remote gatekeeper
    @type site: string
    @param line: The command line that the user typed in
    @type line: string
    @param env: A dictionary containing any custom environment variables
    @type env: dict
    @param cwd: A directory list that represents the current working directory
    @type cwd: list
    """
    preamble = '/bin/bash -c \'if [ "x$OSG_LOCATION" != "x" ]; then cd $OSG_LOCATION; source setup.sh; fi;'
    postamble = '\''

    exports = ""
    for key in env.keys():
        exports += "export %s=%s; " % (key, env[key])

    cd_cmd = ""
    if cwd:
        cwd = "/".join(cwd)
        cd_cmd = "cd %s;" % cwd

    command = 'globus-job-run %(site)s %(preamble)s %(exports)s %(cd)s %(line)s %(postamble)s'
    command = command % {"site" : site,
                         "preamble" : preamble,
                         "postamble" : postamble,
                         "exports" : exports,
                         "cd": cd_cmd,
                         "line": line}
    return command

def buildGlobusCopy(site, remote_path, local_path):
    """
    This function builds the appropriate globus-url-copy command to copy a remote
    file to the local file system
    
    @param site: A string containing the fully qualified domain name for the 
        remote gatekeeper
    @type site: string
    @param remote_path: A string containing the full path to the file to be 
        copied on the remote gatekeeper
    @type remote_path: string
    @param local_path: A string containing the full local path where the remote
        file will be copied to
    @type local_path: string
    """
    return 'globus-url-copy -r gsiftp://' + site + "/" + remote_path + " " + local_path

def buildGlobusPing(site):
    """
    This function builds the appropriate globusrun command to 'ping' a remote
    gatekeeper
    
    @param site: A string containing the fully qualified domain name for the 
        remote gatekeeper
    @type site: string
    """
    return 'globusrun -a -r ' + site

def getSiteNameFromFQDN(site_fqdn):
    """
    This function parses the xml retrieved from MyOSG to determine the site name
    for a given remote gatekeeper
    
    @param site_fqdn: A string containing the fully qualified domain name for the 
        remote gatekeeper
    @type site_fqdn: string
    """
    site_name = "NONE"
    try:
        myosg_xml = urllib.urlopen(myosg_url).read()
        xml_summary = libxml2.parseDoc(myosg_xml)

        for resource in xml_summary.xpathEval('//ResourceGroup/Resources/Resource'):
            xml_fqdn = resource.xpathEval('FQDN')[0].content
            if xml_fqdn == site_fqdn:
                site_name = resource.xpathEval('Name')[0].content
    except:
        pass

    return site_name
