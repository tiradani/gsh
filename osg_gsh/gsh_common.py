import sys
import os
import re
import shlex
import platform

py_ver = platform.python_version_tuple()
if int(py_ver[0]) == 2 and int(py_ver[1]) < 5:  # python version is 2.4.x
    from process_management import check_output
else:
    from subprocess import check_output

from gsh_grid import buildGlobusCommand

def print_error(err):
    print >> sys.stderr, err

class CommandHandler:
    def __init__(self, console):
        self.console = console

    def customCommand(self, line, workfile):
        if line.startswith("|"):
            # remove pipe and pass along to be executed
            line = line[1:]
        else:
            if not line.startswith("!"):
                try:
                    line = line.strip()
                    if line.startswith("less"):
                        remote_path = line.split()[1]
                        self.cacheData(remote_path, workfile)
                        line = "!less " + workfile
                    if line.startswith("vim"):
                        remote_path = line.split()[1]
                        self.cacheData(remote_path, workfile)
                        line = "!vim " + workfile
                    if line.startswith("emacs"):
                        remote_path = line.split()[1]
                        self.cacheData(remote_path, workfile)
                        line = "!emacs " + workfile
                    if line.startswith("cp"):
                        line = self.parse_cp(line)
                    #if line.startswith("cd"):
                    #    line = self.parse_cd(line)
                except:
                    print sys.exc_info()[0]
                    print sys.exc_info()[1]
                    line = ""

        if (line != "" and (not line.startswith("!"))):
            line = "!" + buildGlobusCommand(self.console.site, line)

        return line

    def run(self, cmd):
        return check_output(shlex.split(cmd), env=os.environ)

    def get_vdt_location(self):
        line = "echo $VDT_LOCATION"
        cmd = buildGlobusCommand(self.console.site, line)
        results = self.run(cmd)
        return results
    
    def cacheData(self, remote_path, local_path):
        r = re.compile('(\$[A-Za-z_]*)')
    
        var_list = r.findall(remote_path)
        for v in var_list:
            remote_path = remote_path.replace(v, self.get_env(v))
    
        line = "cat " + remote_path
        cmd = buildGlobusCommand(self.console.site, line)
        results = self.run(cmd)
        self.writeworkfile(results, local_path)
    
    def writeworkfile(self, contents, path):
        file_write = open(path, "w")
        file_write.write(contents)
        file_write.close()
    
    def parse_cp(self, line):
        """ executes the cp command
            usage:
                cp path1 path2
            
            Caveats:
                both paths must be absolute paths.
                paths ending in a directory must also contain a trailing slash
        """
        #@TODO add processing for path symbols like .. or ~
        
        remote_to_local = "globus-url-copy gsiftp://%(server)s/%(remote_abs_path)s file:///%(local_abs_path)s"
        local_to_remote = "globus-url-copy file:///%(local_abs_path)s gsiftp://%(server)s/%(remote_abs_path)s"
        
        #globus-url-copy gsiftp://osg.rcac.purdue.edu//opt/osg/gip/etc/add-attributes.conf file:////tmp/aa.conf
         
        pieces_parts = line.split()
        first_path = pieces_parts[1]
        second_path = pieces_parts[2]
        
        is_first_path_local = os.path.exists(first_path)
        is_second_path_local = os.path.exists(second_path)
        
        if is_first_path_local and is_second_path_local:
            # local to local copy
            line = "!%s" % line
        elif is_first_path_local and not is_second_path_local:
            # local to remote copy
            path_dict = {"server" : self.console.site,
                    "remote_abs_path" : second_path,
                    "local_abs_path" : first_path
                    }
            line = local_to_remote % dict
            line = "!%s" % line
        elif not is_first_path_local and is_second_path_local:
            # remote to local copy
            path_dict = {"server" : self.console.site,
                    "remote_abs_path" : first_path,
                    "local_abs_path" : second_path
                    }
            line = remote_to_local % path_dict
            line = "!%s" % line
        elif not is_first_path_local and not is_second_path_local:
            # remote to remote copy
            line = buildGlobusCommand(self.console.site, line)
            print self.run(line)
            line = ""
        else:
            print "Houston, we have a problem..."
            line = ""
            
        return line
    
    def parse_cd(self, line):
        line += "; echo $PWD"
        cmd = buildGlobusCommand(self.console.site, line)
        result = self.run(cmd)
        print result 
        if len(result.strip().split("\n")) == 1:
            self.console.site_env["PWD"] = result.strip() 
        return ""

    def get_env(self, var):
        var2 = var.replace("$", "")
        val = ""
        try:
            val = self.console.get_env(var2)
        except:
            if len(val.strip()) <= 0:
                cmd = buildGlobusCommand(self.console.site, "echo %s" % var2)
                val = self.run(cmd).replace("\n","")
                self.console.set_env(var2, val)
        return val
