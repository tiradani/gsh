# Define custom macros
%define is_fedora %(test -e /etc/fedora-release && echo 1 || echo 0)
# From http://fedoraproject.org/wiki/Packaging:Python
# Define python_sitelib
%if ! (0%{?fedora} > 12 || 0%{?rhel} > 5)
%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}
%{!?python_sitearch: %global python_sitearch %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib(1))")}
%endif

%define major 0
%define minor 1
%define patchlevel 0

Name:               gsh
Version:            %{major}.%{minor}.%{patchlevel}
Release:            1%{?dist}

Summary:            gsh stands for "grid shell".
Group:              System Environment/Daemons
License:            Fermitools Software Legal Information (Modified BSD License)
URL:                http://tiradani.github.com/gsh/
BuildRoot:          %{_tmppath}/%{name}-buildroot
BuildArchitectures: noarch

Requires:           libxml2
Requires:           libxml2-python
Requires:           /usr/bin/globus-job-run
Requires:           /usr/bin/globus-url-copy
Requires:           /usr/bin/globusrun
Requires:           /usr/bin/grid-proxy-init
Requires:           /usr/bin/voms-proxy-init

Source0:            gsh.tar.gz

%description
gsh stands for "grid shell".  It is a wrapper around glodbus-job-run commands 
that fakes a command line console for a remote gatekeeper.

%prep
%setup -q -n gsh

%build
#make %{?_smp_mflags}

%pre
# pass

%install
rm -rf $RPM_BUILD_ROOT

# "install" the python site-packages directory
install -d $RPM_BUILD_ROOT%{python_sitelib}
cp -arp osg_gsh $RPM_BUILD_ROOT%{python_sitelib}

# install the executables
install -d $RPM_BUILD_ROOT%{_bindir}
install -m 0500 bin/gsh $RPM_BUILD_ROOT%{_bindir}/gsh

# sync gsh version with the RPM version
cat > $RPM_BUILD_ROOT%{python_sitelib}/osg_gsh/gsh_version.py << EOF
MAJOR = %{major}
MINOR = %{minor}
PATCH = %{patchlevel}
EOF

# install man page
install -g 0 -o 0 -m 0644 man/gsh.1 $RPM_BUILD_ROOT%{_mandir}/man1/
gzip $RPM_BUILD_ROOT%{_mandir}/man1/gsh.1

%clean
rm -rf $RPM_BUILD_ROOT

%post
# $1 = 1 - Installation
# $1 = 2 - Upgrade
# Source: http://www.ibm.com/developerworks/library/l-rpm2/

%preun
# $1 = 0 - Action is uninstall
# $1 = 1 - Action is upgrade

if [ "$1" = "0" ] ; then
    rm -rf %{_bindir}/gsh
    rm -rf %{python_sitelib}/osg_gsh
fi

%files
%defattr(-,root,root,-)
%attr(755,root,root) %{_bindir}/gsh
%attr(755,root,root) %{python_sitelib}/osg_gsh
%attr(0644,root,root) %{_mandir}/man1/gsh.1*

%doc README LICENSE

%changelog
* Mon Mar 12 2012 Anthony Tiradani <anthony.tiradani@gmail.com> 0.1.0-0
- Initial Version

