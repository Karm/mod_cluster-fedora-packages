%{!?_httpd_apxs:       %{expand: %%global _httpd_apxs       %%{_sbindir}/apxs}}
%{!?_httpd_mmn:        %{expand: %%global _httpd_mmn        %%(cat %{_includedir}/httpd/.mmn || echo 0-0)}}
%{!?_httpd_confdir:    %{expand: %%global _httpd_confdir    %%{_sysconfdir}/httpd/conf.d}}
%{!?_httpd_modconfdir: %{expand: %%global _httpd_modconfdir %%{_sysconfdir}/httpd/conf.d}}

%global major_version 1
%global minor_version 3
%global micro_version 1
%global namedreltag .Final
%global namedversion %{version}%{?namedreltag}
%global libdir %{_javadir}/%{name}


# Conditional build, set 0 to disable java support
%define with_java 1

Summary:    Apache HTTP Server load balancer
Name:       mod_cluster
Version:    %{major_version}.%{minor_version}.%{micro_version}
Release:    1%{?dist}
License:    LGPLv3
URL:        http://jboss.org/mod_cluster
Group:      System Environment/Daemons

Source:     https://github.com/modcluster/mod_cluster/archive/%{namedversion}.tar.gz
Source1:    mod_cluster.conf
Source2:    README.fedora

Patch0:     catalina-pom-defaults.patch
Patch1:     catalina-standalone-pom-defaults.patch


Requires:      httpd >= 2.2.26
Requires:      httpd-mmn = %{_httpd_mmn}


BuildRequires: httpd-devel >= 2.2.26
BuildRequires: autoconf
BuildRequires: make
BuildRequires: gcc

%if %{with_java}
BuildRequires: maven-local
BuildRequires: maven-enforcer-plugin
BuildRequires: jboss-parent
BuildRequires: jpackage-utils
BuildRequires: java-devel
BuildRequires: jcip-annotations
BuildRequires: jboss-logging-tools
BuildRequires: jboss-logging
#BuildRequires: jboss-web
BuildRequires: jboss-servlet-3.0-api
BuildRequires: tomcat-lib
%endif


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


%if %{with_java}
%package java
Summary:          Java libs for %{name}
Group:            Development/Libraries
Provides:         %{name}-java = %{version}
%description java
This package contains %{name} core Java libs that can be used with WildFly. 


%package java-catalina
Summary:          Catalina Java libs for %{name} Tomcat integration.
Group:            Development/Libraries
Provides:         %{name}-java-catalina = %{version}
Requires:         %{name}-java = %{version}-%{release}
%description java-catalina
This package contains %{name} Catalina Java libs that are a dependency for Tomcat integration.


%package java-tomcat8
Summary:          Tomcat 8 Java libs for %{name}
Group:            Development/Libraries
Provides:         %{name}-java-tomcat8 = %{version}
Requires:         %{name}-java-catalina = %{version}-%{release}
Requires:         jboss-logging
Requires:         tomcat >= 8
%description java-tomcat8
This package contains %{name} Java libs that can be used with Tomcat 8.


%package java-tomcat7
Summary:          Tomcat 7 Java libs for %{name}
Group:            Development/Libraries
Provides:         %{name}-java-tomcat7 = %{version}
Requires:         %{name}-java-catalina = %{version}-%{release}
Requires:         jboss-logging
Requires:         tomcat >= 7
%description java-tomcat7
This package contains %{name} Java libs that can be used with Tomcat 7.


%package javadoc
Summary:          Javadocs for %{name}
%description javadoc
This package contains the API documentation for %{name}.
%endif

%prep
%setup -q -n mod_cluster-%{namedversion}
%patch0 -p0
%patch1 -p0

%if %{with_java}
%pom_disable_module demo
%pom_disable_module tomcat6 container/pom.xml
%pom_disable_module jbossweb container/pom.xml
%endif

%build
CFLAGS="$RPM_OPT_FLAGS"
export CFLAGS

module_dirs=( advertise mod_manager mod_proxy_cluster mod_cluster_slotmem )

for dir in ${module_dirs[@]} ; do
    pushd native/${dir}
        sh buildconf
        ./configure --libdir=%{_libdir} --with-apxs=%{_httpd_apxs}
        make %{?_smp_mflags}
    popd
done

%if %{with_java}
%mvn_package "org.jboss.mod_cluster:" java

# Tests skipped because of lack of mockito library
%mvn_build -f -- -P default
%endif

%install
install -d -m 755 $RPM_BUILD_ROOT%{_libdir}/httpd/modules
install -d -m 755 $RPM_BUILD_ROOT/etc/httpd/conf.d

%if %{with_java}
%mvn_install
%endif

module_dirs=( advertise mod_manager mod_proxy_cluster mod_cluster_slotmem )

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
%{_libdir}/httpd/modules/mod_cluster_slotmem.so
%config(noreplace) %{_sysconfdir}/httpd/conf.d/*.conf


%if %{with_java}
%files javadoc -f .mfiles-javadoc
%doc lgpl.txt


%files java -f .mfiles-java
%exclude %{libdir}/%{name}-container-tomcat7*
%exclude %{libdir}/%{name}-container-tomcat8*
%exclude %{libdir}/%{name}-container-catalina*

%exclude %{_mavenpomdir}/JPP.%{name}-%{name}-container-tomcat7*
%exclude %{_mavendepmapfragdir}/JPP.%{name}-%{name}-container-tomcat7*
%exclude %{_datadir}/maven-effective-poms/JPP.%{name}-%{name}-container-tomcat7*

%exclude %{_mavenpomdir}/JPP.%{name}-%{name}-container-tomcat8*
%exclude %{_mavendepmapfragdir}/JPP.%{name}-%{name}-container-tomcat8*
%exclude %{_datadir}/maven-effective-poms/JPP.%{name}-%{name}-container-tomcat8*

%exclude %{_mavenpomdir}/JPP.%{name}-%{name}-container-catalina*
%exclude %{_mavendepmapfragdir}/JPP.%{name}-%{name}-container-catalina*
%exclude %{_datadir}/maven-effective-poms/JPP.%{name}-%{name}-container-catalina*

%exclude %{_mavenpomdir}/%{name}-container-tomcat7*
%exclude %{_mavendepmapfragdir}/%{name}-container-tomcat7*
%exclude %{_datadir}/maven-effective-poms/%{name}-container-tomcat7*

%exclude %{_mavenpomdir}/%{name}-container-tomcat8*
%exclude %{_mavendepmapfragdir}/%{name}-container-tomcat8*
%exclude %{_datadir}/maven-effective-poms/%{name}-container-tomcat8*

%exclude %{_mavenpomdir}/%{name}-container-catalina*
%exclude %{_mavendepmapfragdir}/%{name}-container-catalina*
%exclude %{_datadir}/maven-effective-poms/%{name}-container-catalina*
%doc lgpl.txt


%files java-catalina -f .mfiles-java
%exclude %{libdir}/%{name}-container-tomcat7*
%exclude %{libdir}/%{name}-container-tomcat8*
%exclude %{libdir}/%{name}-container-spi*
%exclude %{libdir}/%{name}-core*

%exclude %{_mavenpomdir}/JPP.%{name}-%{name}-container-tomcat7*
%exclude %{_mavendepmapfragdir}/JPP.%{name}-%{name}-container-tomcat7*
%exclude %{_datadir}/maven-effective-poms/JPP.%{name}-%{name}-container-tomcat7*

%exclude %{_mavenpomdir}/JPP.%{name}-%{name}-container-tomcat8*
%exclude %{_mavendepmapfragdir}/JPP.%{name}-%{name}-container-tomcat8*
%exclude %{_datadir}/maven-effective-poms/JPP.%{name}-%{name}-container-tomcat8*

%exclude %{_mavenpomdir}/JPP.%{name}-%{name}-container.pom
%exclude %{_mavenpomdir}/JPP.%{name}-%{name}-container-spi.pom
%exclude %{_mavenpomdir}/JPP.%{name}-%{name}-parent.pom
%exclude %{_mavendepmapfragdir}/JPP.%{name}-%{name}-container-spi*
%exclude %{_mavendepmapfragdir}/%{name}-java*
%exclude %{_datadir}/maven-effective-poms/JPP.%{name}-%{name}-container-spi*

%exclude %{_mavenpomdir}/JPP.%{name}-%{name}-core*
%exclude %{_mavendepmapfragdir}/JPP.%{name}-%{name}-core*
%exclude %{_datadir}/maven-effective-poms/JPP.%{name}-%{name}-core*
%exclude %{_datadir}/maven-metadata/mod_cluster-java*

%exclude %{_mavenpomdir}/%{name}-container-tomcat7*
%exclude %{_mavendepmapfragdir}/%{name}-container-tomcat7*
%exclude %{_datadir}/maven-effective-poms/%{name}-container-tomcat7*

%exclude %{_mavenpomdir}/%{name}-container-tomcat8*
%exclude %{_mavendepmapfragdir}/%{name}-container-tomcat8*
%exclude %{_datadir}/maven-effective-poms/%{name}-container-tomcat8*

%exclude %{_mavenpomdir}/%{name}-container.pom
%exclude %{_mavenpomdir}/%{name}-container-spi.pom
%exclude %{_mavenpomdir}/%{name}-parent.pom
%exclude %{_mavendepmapfragdir}/%{name}-container-spi*
%exclude %{_datadir}/maven-effective-poms/%{name}-container-spi*

%exclude %{_mavenpomdir}/%{name}-core*
%exclude %{_mavendepmapfragdir}/%{name}-core*
%exclude %{_datadir}/maven-effective-poms/%{name}-core*
%doc lgpl.txt


%files java-tomcat8 -f .mfiles-java
%exclude %{libdir}/%{name}-container-tomcat7*
%exclude %{_mavenpomdir}/JPP.%{name}-%{name}-container-tomcat7*
%exclude %{_mavendepmapfragdir}/JPP.%{name}-%{name}-container-tomcat7*
%exclude %{_datadir}/maven-effective-poms/JPP.%{name}-%{name}-container-tomcat7*

%exclude %{libdir}/%{name}-container-spi*
%exclude %{_mavenpomdir}/JPP.%{name}-%{name}-container.pom
%exclude %{_mavenpomdir}/JPP.%{name}-%{name}-container-spi.pom
%exclude %{_mavenpomdir}/JPP.%{name}-%{name}-parent.pom
%exclude %{_mavendepmapfragdir}/JPP.%{name}-%{name}-container-spi*
%exclude %{_mavendepmapfragdir}/%{name}-java*
%exclude %{_datadir}/maven-effective-poms/JPP.%{name}-%{name}-container-spi*

%exclude %{libdir}/%{name}-core*
%exclude %{_mavenpomdir}/JPP.%{name}-%{name}-core*
%exclude %{_mavendepmapfragdir}/JPP.%{name}-%{name}-core*
%exclude %{_datadir}/maven-effective-poms/JPP.%{name}-%{name}-core*

%exclude %{libdir}/%{name}-container-catalina*
%exclude %{_mavenpomdir}/JPP.%{name}-%{name}-container-catalina*
%exclude %{_mavendepmapfragdir}/JPP.%{name}-%{name}-container-catalina*
%exclude %{_datadir}/maven-effective-poms/JPP.%{name}-%{name}-container-catalina*

%exclude %{_mavenpomdir}/%{name}-container-tomcat7*
%exclude %{_mavendepmapfragdir}/%{name}-container-tomcat7*
%exclude %{_datadir}/maven-effective-poms/%{name}-container-tomcat7*

%exclude %{_mavenpomdir}/%{name}-container.pom
%exclude %{_mavenpomdir}/%{name}-container-spi.pom
%exclude %{_mavenpomdir}/%{name}-parent.pom
%exclude %{_mavendepmapfragdir}/%{name}-container-spi*
%exclude %{_datadir}/maven-effective-poms/%{name}-container-spi*

%exclude %{_mavenpomdir}/%{name}-core*
%exclude %{_mavendepmapfragdir}/%{name}-core*
%exclude %{_datadir}/maven-effective-poms/%{name}-core*

%exclude %{_mavenpomdir}/%{name}-container-catalina*
%exclude %{_mavendepmapfragdir}/%{name}-container-catalina*
%exclude %{_datadir}/maven-effective-poms/%{name}-container-catalina*
%doc lgpl.txt


%files java-tomcat7 -f .mfiles-java
%exclude %{libdir}/%{name}-container-tomcat8*
%exclude %{_mavenpomdir}/JPP.%{name}-%{name}-container-tomcat8*
%exclude %{_mavendepmapfragdir}/JPP.%{name}-%{name}-container-tomcat8*
%exclude %{_datadir}/maven-effective-poms/JPP.%{name}-%{name}-container-tomcat8*

%exclude %{libdir}/%{name}-container-spi*
%exclude %{_mavenpomdir}/JPP.%{name}-%{name}-container.pom
%exclude %{_mavenpomdir}/JPP.%{name}-%{name}-container-spi.pom
%exclude %{_mavenpomdir}/JPP.%{name}-%{name}-parent.pom
%exclude %{_mavendepmapfragdir}/JPP.%{name}-%{name}-container-spi*
%exclude %{_mavendepmapfragdir}/%{name}-java*
%exclude %{_datadir}/maven-effective-poms/JPP.%{name}-%{name}-container-spi*

%exclude %{libdir}/%{name}-core*
%exclude %{_mavenpomdir}/JPP.%{name}-%{name}-core*
%exclude %{_mavendepmapfragdir}/JPP.%{name}-%{name}-core*
%exclude %{_datadir}/maven-effective-poms/JPP.%{name}-%{name}-core*

%exclude %{libdir}/%{name}-container-catalina*
%exclude %{_mavenpomdir}/JPP.%{name}-%{name}-container-catalina*
%exclude %{_mavendepmapfragdir}/JPP.%{name}-%{name}-container-catalina*
%exclude %{_datadir}/maven-effective-poms/JPP.%{name}-%{name}-container-catalina*

%exclude %{_mavenpomdir}/%{name}-container-tomcat8*
%exclude %{_mavendepmapfragdir}/%{name}-container-tomcat8*
%exclude %{_datadir}/maven-effective-poms/%{name}-container-tomcat8*

%exclude %{_mavenpomdir}/%{name}-container.pom
%exclude %{_mavenpomdir}/%{name}-container-spi.pom
%exclude %{_mavenpomdir}/%{name}-parent.pom
%exclude %{_mavendepmapfragdir}/%{name}-container-spi*
%exclude %{_datadir}/maven-effective-poms/%{name}-container-spi*

%exclude %{_mavenpomdir}/%{name}-core*
%exclude %{_mavendepmapfragdir}/%{name}-core*
%exclude %{_datadir}/maven-effective-poms/%{name}-core*

%exclude %{_mavenpomdir}/%{name}-container-catalina*
%exclude %{_mavendepmapfragdir}/%{name}-container-catalina*
%exclude %{_datadir}/maven-effective-poms/%{name}-container-catalina*
%doc lgpl.txt


%post  java-tomcat7
if [ "$1" == "1" ]; then
    %{__ln_s} %{libdir}/mod_cluster-container-catalina.jar %{_javadir}/tomcat/mod_cluster-container-catalina.jar
    %{__ln_s} %{libdir}/mod_cluster-container-catalina-standalone.jar %{_javadir}/tomcat/mod_cluster-container-catalina-standalone.jar
    %{__ln_s} %{libdir}/mod_cluster-container-spi.jar %{_javadir}/tomcat/mod_cluster-container-spi.jar
    %{__ln_s} %{libdir}/mod_cluster-core.jar %{_javadir}/tomcat/mod_cluster-core.jar
    %{__ln_s} %{_javadir}/jboss-logging/jboss-logging.jar %{_javadir}/tomcat/jboss-logging.jar
    %{__ln_s} %{libdir}/mod_cluster-container-tomcat7.jar %{_javadir}/tomcat/mod_cluster-container-tomcat7.jar
fi
%post java-tomcat8
if [ "$1" == "1" ]; then
    %{__ln_s} %{libdir}/mod_cluster-container-catalina.jar %{_javadir}/tomcat/mod_cluster-container-catalina.jar
    %{__ln_s} %{libdir}/mod_cluster-container-catalina-standalone.jar %{_javadir}/tomcat/mod_cluster-container-catalina-standalone.jar
    %{__ln_s} %{libdir}/mod_cluster-container-spi.jar %{_javadir}/tomcat/mod_cluster-container-spi.jar
    %{__ln_s} %{libdir}/mod_cluster-core.jar %{_javadir}/tomcat/mod_cluster-core.jar
    %{__ln_s} %{_javadir}/jboss-logging/jboss-logging.jar %{_javadir}/tomcat/jboss-logging.jar
    %{__ln_s} %{libdir}/mod_cluster-container-tomcat8.jar %{_javadir}/tomcat/mod_cluster-container-tomcat8.jar
fi


%postun  java-tomcat7
if [ "$1" == "0" ]; then
    rm -f %{_javadir}/tomcat/mod_cluster-container-catalina.jar
    rm -f %{_javadir}/tomcat/mod_cluster-container-catalina-standalone.jar
    rm -f %{_javadir}/tomcat/mod_cluster-container-spi.jar
    rm -f %{_javadir}/tomcat/mod_cluster-core.jar
    rm -f %{_javadir}/tomcat/jboss-logging.jar
    rm -f %{_javadir}/tomcat/mod_cluster-container-tomcat7.jar
fi
%postun java-tomcat8
if [ "$1" == "0" ]; then
    rm -f %{_javadir}/tomcat/mod_cluster-container-catalina.jar
    rm -f %{_javadir}/tomcat/mod_cluster-container-catalina-standalone.jar
    rm -f %{_javadir}/tomcat/mod_cluster-container-spi.jar
    rm -f %{_javadir}/tomcat/mod_cluster-core.jar
    rm -f %{_javadir}/tomcat/jboss-logging.jar
    rm -f %{_javadir}/tomcat/mod_cluster-container-tomcat8.jar
fi
%endif

%changelog
* Sun Aug 17 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.2.6-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_22_Mass_Rebuild

* Sat Jun 07 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.2.6-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Thu Jan 23 2014 Joe Orton <jorton@redhat.com> - 1.2.6-3
- fix _httpd_mmn expansion in absence of httpd-devel

* Fri Jan 17 2014 Marek Goldmann <mgoldman@redhat.com> - 1.2.6-2
- Add support for conditional build that builds only HTTPD module

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

