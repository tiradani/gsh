import urllib
import platform
import libxml2

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
    return 'globus-url-copy -r gsiftp://' + site + "/" + remote_path + " " + local_path

def buildGlobusPing(site):
    return 'globusrun -a -r ' + site

def getSiteNameFromFQDN(site_fqdn):
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
