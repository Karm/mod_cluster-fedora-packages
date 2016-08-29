%{!?_httpd_apxs:       %{expand: %%global _httpd_apxs       %%{_sbindir}/apxs}}
%{!?_httpd_mmn:        %{expand: %%global _httpd_mmn        %%(cat %{_includedir}/httpd/.mmn || echo 0-0)}}
%{!?_httpd_confdir:    %{expand: %%global _httpd_confdir    %%{_sysconfdir}/httpd/conf.d}}
# /etc/httpd/conf.d with httpd < 2.4 and defined as /etc/httpd/conf.modules.d with httpd >= 2.4
%{!?_httpd_modconfdir: %{expand: %%global _httpd_modconfdir %%{_sysconfdir}/httpd/conf.d}}

%global namedreltag .Final
%global namedversion %{version}%{?namedreltag}

%if 0%{?fedora}
%bcond_with java
%endif

Name:          mod_cluster
Version:       1.3.3
Release:       5%{?dist}
Summary:       Apache HTTP Server dynamic load balancer with Wildfly and Tomcat libraries
License:       LGPLv3
URL:           http://modcluster.io/
Source0:       https://github.com/modcluster/mod_cluster/archive/%{namedversion}/%{name}-%{namedversion}.tar.gz
Source1:       mod_cluster.conf
Source2:       README.fedora

Patch0:        MODCLUSTER-528-CatalinaContext.java.patch

Requires:      httpd >= 2.2.26
Requires:      httpd-mmn = %{_httpd_mmn}

BuildRequires: httpd-devel >= 2.2.26
BuildRequires: autoconf
BuildRequires: make
BuildRequires: gcc

%if %{without java}
BuildRequires: maven-local
BuildRequires: mvn(net.jcip:jcip-annotations)
BuildRequires: mvn(org.apache.maven.plugins:maven-enforcer-plugin)
BuildRequires: mvn(org.apache.tomcat:tomcat-catalina)
BuildRequires: mvn(org.apache.tomcat:tomcat-coyote)
BuildRequires: mvn(org.apache.tomcat:tomcat-util)
BuildRequires: mvn(org.jboss:jboss-parent:pom:)
BuildRequires: mvn(org.jboss.logging:jboss-logging)
BuildRequires: mvn(org.jboss.logging:jboss-logging-processor)
BuildRequires: mvn(org.jboss.spec.javax.servlet:jboss-servlet-api_3.0_spec)
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

%if %{without java}
%package java
Summary:          Java libraries for %{name}
BuildArch:        noarch

%description java
This package contains %{name} core Java libraries
that can be used with WildFly application server.

%package java-tomcat8
Summary:          Tomcat 8 Java libraries for %{name}
Requires:         tomcat >= 1:8
BuildArch:        noarch

%description java-tomcat8
This package contains %{name} Java libraries that can be used with Tomcat 8.

%package javadoc
Summary:          Javadoc for %{name}
BuildArch:        noarch

%description javadoc
This package contains the API documentation for %{name}.
%endif

%prep
%setup -q -n %{name}-%{namedversion}
%patch0 -p0

%if %{without java}
%pom_disable_module demo
%pom_disable_module tomcat6 container
%pom_disable_module tomcat7 container
%pom_disable_module jbossweb container

%pom_remove_plugin :animal-sniffer-maven-plugin
%pom_remove_plugin :versions-maven-plugin

%pom_change_dep :jboss-servlet-api_3.0_spec org.apache.tomcat:tomcat-util container/catalina

%pom_change_dep org.apache.tomcat: ::'${version.tomcat8}' container/catalina

%pom_change_dep :catalina :tomcat-catalina:'${version.tomcat8}' container/catalina-standalone
%pom_change_dep :coyote :tomcat-coyote:'${version.tomcat8}' container/catalina-standalone

%pom_xpath_remove "pom:dependency[pom:type = 'test-jar']" container/tomcat8
%pom_xpath_inject "pom:profile[pom:id = 'TC8']/pom:modules" "<module>catalina-standalone</module>"  container

%pom_xpath_set "pom:profile[pom:id = 'TC7']/pom:id" TC8 container/catalina

%mvn_package ":mod_cluster-core" java
%mvn_package ":mod_cluster-container-spi" java

%mvn_package ":mod_cluster-container-tomcat8" java-tomcat8
%mvn_package ":mod_cluster-container-catalina-standalone" java-tomcat8
%mvn_package ":mod_cluster-container-catalina" java-tomcat8

# Wildfly/core lib
%mvn_file :mod_cluster-core:jar: mod_cluster/mod_cluster-core tomcat/mod_cluster-core
%mvn_file :mod_cluster-container-spi:jar: mod_cluster/mod_cluster-container-spi tomcat/mod_cluster-container-spi

# Tomcat-ish
%mvn_file :mod_cluster-container-catalina:jar: tomcat/mod_cluster-container-catalina 
%mvn_file :mod_cluster-container-catalina-standalone:jar: tomcat/mod_cluster-container-catalina-standalone
%mvn_file :mod_cluster-container-tomcat8:jar: tomcat/mod_cluster-container-tomcat8

# Disable useless artifacts generation, package __noinstall do not work
%pom_add_plugin org.apache.maven.plugins:maven-source-plugin . '
<configuration>
 <skipSource>true</skipSource>
</configuration>'

%mvn_package "org.jboss.mod_cluster:" java

%endif

%build

CFLAGS="$RPM_OPT_FLAGS"
export CFLAGS

module_dirs=( advertise mod_manager mod_proxy_cluster mod_cluster_slotmem )

for dir in ${module_dirs[@]} ; do
    pushd native/${dir}
        sh buildconf
        %configure --libdir=%{_libdir} --with-apxs=%{_httpd_apxs}
        make %{?_smp_mflags}
    popd
done

%if %{without java}
%mvn_build -s -f -- -PTC8
%endif

%install
install -d -m 755 $RPM_BUILD_ROOT%{_libdir}/httpd/modules
install -d -m 755 $RPM_BUILD_ROOT/etc/httpd/conf.d

module_dirs=( advertise mod_manager mod_proxy_cluster mod_cluster_slotmem )
for dir in ${module_dirs[@]} ; do
    pushd native/${dir}
        cp ./*.so $RPM_BUILD_ROOT%{_libdir}/httpd/modules
    popd
done

%if %{without java}
%mvn_install

ln -sf %{_javadir}/jboss-logging/jboss-logging.jar \
 $RPM_BUILD_ROOT%{_javadir}/tomcat/jboss-logging.jar

%endif

cp -a %{SOURCE1} $RPM_BUILD_ROOT/etc/httpd/conf.d/

install -pm 0644 %{SOURCE2} README

%files
%doc README
%license lgpl.txt
%{_libdir}/httpd/modules/mod_advertise.so
%{_libdir}/httpd/modules/mod_manager.so
%{_libdir}/httpd/modules/mod_proxy_cluster.so
%{_libdir}/httpd/modules/mod_cluster_slotmem.so
%config(noreplace) %{_sysconfdir}/httpd/conf.d/*.conf

%if %{without java}
%files javadoc -f .mfiles-javadoc
%license lgpl.txt

%files java -f .mfiles-java
%license lgpl.txt

%files java-tomcat8 -f .mfiles-java-tomcat8
%{_javadir}/tomcat/jboss-logging.jar
%license lgpl.txt
%endif

%changelog
* Mon Aug 29 2016 gil cattaneo <puntogil@libero.it> 1.3.3-5
- remove pom macro on unavailable mod_cluster-container-catalina-spi

* Mon Aug 29 2016 gil cattaneo <puntogil@libero.it> 1.3.3-4
- fix BR list
- marked as noarch only the java stuff

* Mon Aug 29 2016 Michal Karm Babacek  <karm@fedoraproject.org> 1.3.3-3
- Added mvn(..) BuildRequires for Tomcat libs instead of direct dependency on tomcat package

* Mon Aug 29 2016 gil cattaneo <puntogil@libero.it> 1.3.3-2
- fix pom macros

* Mon Aug 29 2016 Michal Karm Babacek  <karm@fedoraproject.org> - 1.3.3-1
- Upstream release 1.3.3.Final
- Refactored spec file

* Thu Feb 04 2016 Fedora Release Engineering <releng@fedoraproject.org> - 1.2.6-7
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Wed Jun 17 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.2.6-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

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

