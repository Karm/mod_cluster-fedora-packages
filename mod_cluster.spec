%{!?_httpd_apxs:       %{expand: %%global _httpd_apxs       %%{_sbindir}/apxs}}
%{!?_httpd_mmn:        %{expand: %%global _httpd_mmn        %%(cat %{_includedir}/httpd/.mmn || echo missing-httpd-devel)}}
%{!?_httpd_confdir:    %{expand: %%global _httpd_confdir    %%{_sysconfdir}/httpd/conf.d}}
# /etc/httpd/conf.d with httpd < 2.4 and defined as /etc/httpd/conf.modules.d with httpd >= 2.4
%{!?_httpd_modconfdir: %{expand: %%global _httpd_modconfdir %%{_sysconfdir}/httpd/conf.d}}

%global namedreltag .Final
%global namedversion %{version}%{?namedreltag}

Summary:    Apache HTTP load balancer
Name:       mod_cluster
Version:    1.2.6
Release:    1%{?dist}
License:    LGPLv2
URL:        http://jboss.org/mod_cluster
Group:      System Environment/Daemons

Source:     https://github.com/modcluster/mod_cluster/archive/%{namedversion}.tar.gz
Source1:    mod_cluster.conf
Source2:    README.fedora

Requires:      httpd >= 2.2.8
Requires:      httpd-mmn = %{_httpd_mmn}

BuildRequires: maven-local
BuildRequires: maven-enforcer-plugin
BuildRequires: jboss-parent
BuildRequires: jpackage-utils
BuildRequires: java-devel
BuildRequires: jcip-annotations
BuildRequires: jboss-logging-tools
BuildRequires: jboss-logging
BuildRequires: jboss-servlet-3.0-api
BuildRequires: jboss-web
BuildRequires: httpd-devel >= 2.2.8
BuildRequires: autoconf
BuildRequires: make
BuildRequires: gcc
BuildRequires: tomcat-lib

%description
Mod_cluster is an httpd-based load balancer. Like mod_jk and mod_proxy,
mod_cluster uses a communication channel to forward requests from httpd to one
of a set of application server nodes. Unlike mod_jk and mod_proxy, mod_cluster
leverages an additional connection between the application server nodes and
httpd. The application server nodes use this connection to transmit server-side
load balance factors and lifecycle events back to httpd via a custom set of
HTTP methods, affectionately called the Mod-Cluster Management Protocol (MCMP).
This additional feedback channel allows mod_cluster to offer a level of
intelligence and granularity not found in other load balancing solutions.

%package java
Summary:          Java bindings for %{name}
Group:            Development/Libraries

%description java
This package contains Java part of %{name}.

%package javadoc
Summary:          Javadocs for %{name}

%description javadoc
This package contains the API documentation for %{name}.

%prep
%setup -q -n mod_cluster-%{namedversion}

%pom_disable_module demo

%build
CFLAGS="$RPM_OPT_FLAGS"
export CFLAGS

module_dirs=( advertise mod_manager mod_proxy_cluster mod_slotmem )

for dir in ${module_dirs[@]} ; do
    pushd native/${dir}
        sh buildconf
        ./configure --libdir=%{_libdir} --with-apxs=%{_httpd_apxs}
        make %{?_smp_mflags}
    popd
done

%mvn_package "org.jboss.mod_cluster:" java

# Build the AS7 required libs
# Tests skipped because of lack of mockito library
%mvn_build -f -- -P AS7

%install
install -d -m 755 $RPM_BUILD_ROOT%{_libdir}/httpd/modules
install -d -m 755 $RPM_BUILD_ROOT/etc/httpd/conf.d

%mvn_install

module_dirs=( advertise mod_manager mod_proxy_cluster mod_slotmem )

for dir in ${module_dirs[@]} ; do
    pushd native/${dir}
        cp ./*.so $RPM_BUILD_ROOT%{_libdir}/httpd/modules
    popd
done

cp -a %{SOURCE1} $RPM_BUILD_ROOT/etc/httpd/conf.d/

install -m 0644 %{SOURCE2} README

%files
%doc README
%doc lgpl.txt
%{_libdir}/httpd/modules/mod_advertise.so
%{_libdir}/httpd/modules/mod_manager.so
%{_libdir}/httpd/modules/mod_proxy_cluster.so
%{_libdir}/httpd/modules/mod_slotmem.so
%config(noreplace) %{_sysconfdir}/httpd/conf.d/*.conf

%files javadoc -f .mfiles-javadoc
%doc lgpl.txt

%files java -f .mfiles-java
%doc lgpl.txt

%changelog
* Wed Sep 25 2013 Marek Goldmann <mgoldman@redhat.com> - 1.2.6-1
- Upstream release 1.2.6.Final
- Support for Apache 2.4 in mod_cluster.conf

* Mon Aug 05 2013 Marek Goldmann <mgoldman@redhat.com> - 1.2.4-1
- Upstream release 1.2.4.Final

* Sat Aug 03 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.2.1-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_20_Mass_Rebuild

* Thu Feb 14 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.2.1-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Wed Feb 06 2013 Java SIG <java-devel@lists.fedoraproject.org> - 1.2.1-4
- Update for https://fedoraproject.org/wiki/Fedora_19_Maven_Rebuild
- Replace maven BuildRequires with maven-local

* Fri Jul 20 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.2.1-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Tue Jun 05 2012 Marek Goldmann <mgoldman@redhat.com> - 1.2.1-2
- Added missing container.pom

* Mon May 07 2012 Marek Goldmann <mgoldman@redhat.com> - 1.2.1-1
- Upstream release 1.2.1.Final
- Port to httpd 2.4, RHBZ#813871

* Wed Mar 28 2012 Marek Goldmann <mgoldman@redhat.com> - 1.2.0-1
- Upstream release 1.2.0.Final
- Add java subpackage with AS7 required jars

* Tue Mar 27 2012 Marek Goldmann <mgoldman@redhat.com> - 1.1.1-4
- Require httpd-mmn RHBZ#803068

* Fri Jan 13 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.1.1-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Fri Mar 11 2011 Marek Goldmann <mgoldman@redhat.com> - 1.1.1-2
- Another round of cleanup in spec file
- Patch that disables compilation-time warnings

* Thu Mar 10 2011 Marek Goldmann <mgoldman@redhat.com> - 1.1.1-1
- Upstream release 1.1.1
- Cleanup in spec file

* Fri Nov 12 2010 Marek Goldmann <mgoldman@redhat.com> - 1.1.0-1
- Initial release

