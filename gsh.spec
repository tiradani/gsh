# Define custom macros
%define is_fedora %(test -e /etc/fedora-release && echo 1 || echo 0)
# From http://fedoraproject.org/wiki/Packaging:Python
# Define python_sitelib
%if ! (0%{?fedora} > 12 || 0%{?rhel} > 5)
%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}
%{!?python_sitearch: %global python_sitearch %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib(1))")}
%endif

Name:               gsh
Version:            0.0.1
Release:            0

Summary:            gsh stands for "grid shell".
Group:              System Environment/Daemons
License:            Fermitools Software Legal Information (Modified BSD License)
URL:                http://tiradani.github.com/gsh/
BuildRoot:          %{_tmppath}/%{name}-buildroot
BuildArchitectures: noarch

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


%changelog
* Mon Mar 12 2012 Anthony Tiradani  0.0.1-3
- Initial Version

