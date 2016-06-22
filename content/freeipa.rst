:title: Kerberos and Devstack
:slug: kerberos-devstack
:date: 2016-06-22 17:00

Recently I tackled a `keystoneauth bug <https://bugs.launchpad.net/keystoneauth/+bug/1567257>`_ that required a kerberos-backed keystone to develop against. Jamie Lennox's `blog post on setting up kerberos with packstack <http://www.jamielennox.net/blog/2015/02/12/step-by-step-kerberized-keystone/>`_ was a fantastic resource for setting up this lab environment. OpenStack has changed a bit since that was written, so this post is somewhat a refresh of that one. I also wanted to use devstack rather than packstack, as well as talk about some of the pitfalls that I found and how to resolve them.

This post covers setting up kerberos and devstack all on one server. This is not very realistic for production but it is convenient for development and could be used in a testing scenario. The procedure will be subtly different for a split install.

Getting Started
---------------

`FreeIPA <https://www.freeipa.or>`_ provides LDAP, Kerberos, SSSD and other enterprise information management services packaged together with client utilities. This can only run on a RedHat-based operating system. We're using CentOS 7 here.

::

   $ sudo yum update -y

Install FreeIPA
---------------

Make sure the FQDN is set up correctly. The FreeIPA install and later operations depend on being able to resolve the FQDN. Rabbitmq also depends on the hostname being consistent everywhere.

::

   $ export HOSTNAME=freeipa.openstack.local
   $ hostnamectl set-hostname $HOSTNAME
   $ echo $(ip addr show eth0 | awk '/inet /{gsub("/[0-9]{2,3}$","",$2); print $2}') $HOSTNAME >> /etc/hosts

Install the FreeIPA package as well as the haveged package, which will help with generating entropy in your virtual machine during the IPA server install.

::

   $ sudo yum install ipa-server haveged -y

The IPA installer will ask if you want to configure DNS. Since this is all-in-one, there is no particular need to set up a DNS server if you have your hostname and /etc/hosts configured correctly. If you do want to set up a DNS server you will need an additional package::

   $ sudo yum install ipa-server-dns

Run the installer. If you've set up the hostname correctly, you should be able to accept all the defaults until it comes time to set the directory server admin and kerberos admin passwords.

::

   $ sudo ipa-server-install

If everything worked correctly you'll be prompted with something like this after answering the config questions::

   The IPA Master Server will be configured with:
   Hostname:       freeipa.openstack.local
   IP address(es): 192.168.122.105
   Domain name:    openstack.local
   Realm name:     OPENSTACK.LOCAL

Type 'yes' to accept and start the install. It will take a few minutes.

Install Devstack
----------------

We'll be using a minimally-configured `devstack <http://docs.openstack.org/developer/devstack/>`_.

Since we're installing devstack on the same machine as the kerberos server, there are some interesting conflicts that need to be resolved.

First, devstack installs mod_ssl for apache. The RPM automatically sets up a vhost listening on port 443. However, FreeIPA already set up mod_nss which is already listening on 443. If we let devstack do its thing it will fail trying to restart apache, and you will see ``could not bind to address 0.0.0.0:443`` in the apache logs. We need to get ahead of it::

   $ sudo yum install mod_ssl -y
   $ sudo mv /etc/httpd/conf.d/ssl.conf /etc/httpd.conf.d/ssl.conf.orig

Second, FreeIPA depends on a the python-requests RPM, which will end up causing a confusing conflict with the six package installed with pip::

   AttributeError: 'module' object has no attribute 'add_metaclass'

Even in a split install, this might still happen if your CentOS devstack server has cloud-init installed, which also uses the python-requests and python-six RPMs.

The way I worked around this was to use pip to overwrite the RPM site-package files::

   $ sudo pip uninstall requests six && sudo pip install -U requests

If you followed advice from `this github issue <https://github.com/glue-viz/glue/issues/449#issuecomment-177067560>`_ and just uninstalled and reinstalled six but not requests, devstack might fail with this misleading error::

   Could not determine a suitable URL for the plugin

It's actually caused by an exception in the pkg_resources module, which you can see in the apache log::

   ContextualVersionConflict: (urllib3 1.16 (/usr/lib/python2.7/site-packages), Requirement.parse('urllib3==1.15.1'), set(['requests']))

Uninstalling and reinstalling requests and restarting apache should fix this.
Now you should be able to install devstack without errors. In my example I'm only setting up keystone so I limit the services to mysql, rabbitmq, and keystone in local.conf.

::

   $ git clone git://git.openstack.org/openstack-dev/devstack
   $ cd devstack
   $ cp samples/local.conf .
   $ echo ENABLED_SERVICES=mysql,rabbit,key >> local.conf
   $ ./stack.sh

The ipa-server package installs the client utilities for you. If your devstack server was a separate machine, you would need to install the ``ipa-client`` and ``ipa-admintools`` packages and run the client installer.

At the time of this writing, the v3kerberos entrypoint was just added to keystoneauth, and keystoneauth support was just added to openstackclient, and neither have been released yet, so you will need to reinstall them from source::

   $ cd /opt/stack
   $ git clone git://git.openstack.org/openstack/keystoneauth
   $ git clone git://git.openstack.org/openstack/python-openstackclient
   $ sudo pip install -U keystoneauth/
   $ sudo pip install -U python-openstackclient/

You could have also set ``LIBS_FROM_GIT=python-openstackclient,keystoneauth`` in your devstack local.conf.

LDAP Identity Backend
---------------------

FreeIPA uses LDAP to store kerberos principals, so we need to set up keystone to connect to the LDAP server.

First install the additional packages that keystone needs to interface with LDAP::

   $ sudo yum install openldap-devel -y && sudo pip install ldappool

We want `domain specific identity drivers <http://docs.openstack.org/developer/keystone/configuration.html#domain-specific-drivers>`_ so that we don't have to recreate our admin user or any service users in LDAP. We could use the kerberos admin user as the keystone admin user, but you must first give it the admin role in the admin project, to do which requires having admin privileges via either the deprecated admin token pipeline or an existing admin user, so there's a bit of a chicken-and-egg problem that is solved by continuing to use the SQL backend for the admin user. You can refer to `Dolph Mathews' blog post on domain-specific drivers <http://dolphm.com/deploying-domain-specific-identity-drivers-in-openstack-keystone/>`_, but I'll summarize the parts relevant to our goals.

In `/etc/keystone/keystone.conf`, enable domain specific drivers::

   [identity]
   domain_specific_drivers_enabled = true

Leave the ``[identity]/driver`` parameter set to ``sql``, as this will be the default backend. We're also leaving ``[assignment]/driver`` set to ``sql`` since projects, domains, and roles should still be managed in keystone.

The default domain configuration directory is /etc/keystone/domains, so create that directory::

   $ sudo mkdir /etc/keystone/domains

Create a file called /etc/keystone/domains/keystone.Users.conf. The 'Users' is the domain we're going to create to use with LDAP. Add the following configuration to it, substituting your own IPA server name and domain name::

   [identity]
   driver = ldap

   [ldap]
   url=ldaps://freeipa.openstack.local
   suffix=dc=openstack,dc=local
   user_tree_dn=cn=users,cn=accounts,dc=openstack,dc=local
   user_objectclass=person
   user_id_attribute=uid
   user_name_attribute=uid
   user_mail_attribute=mail
   group_tree_dn=cn=groups,cn=accounts,dc=openstack,dc=local
   group_objectclass=groupOfNames
   group_id_attribute=cn
   group_name_attribute=cn
   group_member_attribute=member
   group_desc_attribute=description
   user_enabled_attribute=nsAccountLock
   user_enabled_default=False
   user_enabled_invert=true

This is just telling keystone what kind of schema the LDAP server is using so that it can interpret the directory. We don't need to set the user or password parameters since the IPA server allows read-only anonymous binds.

Restart keystone by restarting apache::

   $ sudo systemctl restart httpd.service

Create the domain that will be backed by LDAP. If you didn't make any other modifications to your devstack local.conf, you'll use the following admin credentials:

.. code-block:: bash

   $ export OS_PROJECT_NAME=admin
   $ export OS_IDENTITY_API_VERSION=3
   $ export OS_PASSWORD=nomoresecret
   $ export OS_AUTH_TYPE=password
   $ export OS_AUTH_URL=http://127.0.0.1:5000/v3
   $ export OS_USERNAME=admin
   $ openstack domain create Users

Note that at this point we're still using the password auth type.

Check that the LDAP backend is working by looking up the users in the LDAP-backed domain::

   $ openstack user list --domain Users

You should see the admin user that was created during the IPA server install listed.

Configure Keystone to Auth with Kerberos
----------------------------------------

Add kerberos to the auth methods in keystone.conf:: 

   [auth]
   methods = external,password,token,oauth1,kerberos

It's not enough to just leave ``external`` enabled.

Log in as the kerberos admin as the root user::

   $ sudo kinit admin

If you ever see an error like this::

   ipa: ERROR: did not receive Kerberos credentials

it's because you did not log in with kinit.

Create the kerberos service::

   $ sudo ipa service-add HTTP/freeipa.openstack.local@OPENSTACK.LOCAL

If you didn't set up the FreeIPA DNS server you may see a warning like this::

   ipa: ERROR: Host does not have corresponding DNS A/AAAA record

Don't worry about it, things will still work.

Set up the HTTP keytab::

   $ sudo ipa-getkeytab -s freeipa.openstack.local -p HTTP/freeipa.openstack.local@OPENSTACK.LOCAL -k /etc/httpd/conf/ipa.keytab

Normally sudo is not required for kerberos operations, and simply logging in as the kerberos admin with 'kinit admin' is enough. We needed to use sudo here because we need to have permissions to write to `/etc/httpd/conf/`. The kerberos ticket isn't passed upon sudo invocation so we needed to get the kerberos ticket for the root user from the start.

Note the name of the keytab file. FreeIPA already set up a keytab for apache and expects it to be there. If it doesn't match up, you may start seeing errors like this when trying to administer kerberos::

   ipa: ERROR: Insufficient access: SASL(-1): generic failure: GSSAPI Error: Unspecified GSS failure.  Minor code may provide more information (KDC returned error string: 2ND_TKT_SERVER

If you want to change it, you must change the value for the GssapiCredStore parameters in `/etc/httpd/conf.d/ipa.conf`. Make sure the apache system user can read and write to it::

   $ sudo chown apache:apache /etc/httpd/conf/ipa.keytab

Install the kerberos apache mod and enable it::

   $ sudo yum install -y mod_auth_kerb
   $ sudo ln -s /etc/httpd/conf.modules.d/10-auth_kerb.conf /etc/httpd/conf.d/10-auth_kerb.load

Devstack already set up keystone apache vhosts for us, we just need to update them to use the kerberos mod.

In `/etc/httpd/conf.d/keystone.conf` add WSGI mappings to the public and admin vhosts.

Add::

   WSGIScriptAlias /krb /usr/bin/keystone-wsgi-public

above the original public mapping::

   WSGIScriptAlias / /usr/bin/keystone-wsgi-public

and add::

  WSGIScriptAlias /krb /usr/bin/keystone-wsgi-admin

above the original admin mapping::

  WSGIScriptAlias / /usr/bin/keystone-wsgi-admin

and add a new location directive to the end::

   <Location "/krb/v3/auth/tokens">
         LogLevel debug
         AuthType Kerberos
         AuthName "Kerberos Login"
         KrbMethodNegotiate on
         KrbMethodK5Passwd off
         KrbServiceName HTTP/freeipa.openstack.local
         KrbAuthRealms OPENSTACK.LOCAL
         Krb5KeyTab /etc/httpd/conf/ipa.keytab
         KrbLocalUserMapping on
         Require valid-user
         SetEnv REMOTE_DOMAIN Users
   </Location>

Take note of the ``KrbServiceName`` and the ``KrbAuthRealms`` parameters and make sure they match the service you created with ``ipa service-add`` and domain name you set up during the IPA server install. Note the ``SetEnv REMOTE_DOMAIN`` parameter and make sure its value matches the LDAP-backed keystone domain you created.

If you used an alternate path for the keytab file make sure to update the ``Krb5KeyTab`` parameter.

In order to use the kerberos plugin with keystoneauth we need to install the requests-kerberos package::

   $ sudo pip install requests-kerberos==0.8.0

For some reason, with newer versions of requests-kerberos you might see an error like this when you try to get your keystone token::

   argument 2 must be string, not None

This is a bug that needs to be tracked down. For now, 0.8.0 works.

Like the six package earlier, there may be a conflict between the python-kerberos RPM installed with ipa-server and the kerberos pip package that requests-kerberos depends on, which may start causing an ugly error when trying to use the ``ipa`` command line tool::

   AttributeError: 'module' object has no attribute 'authGSSClientInquireCred'

I resolved it by overwriting the python-kerberos RPM site-package files::

   $ sudo pip uninstall kerberos && sudo pip install kerberos

Finally, restart apache::

   $ sudo systemctl restart httpd.service

Ready, Set, Authenticate!
-------------------------

Add a test user to authenticate with (you can keep using ``sudo`` or get a new ticket for your non-root user with ``kinit``)::

   $ ipa user-add --first test --last user --random testuser

It must have a role in some project. We can use the demo project and the Member role that devstack set up. Use the admin user with the password auth type for this::

   $ openstack role add --user testuser --user-domain Users --project demo Member

Now, log in as the user::

   $ kinit testuser

Using the v3kerberos auth plugin, get a token::

   $ export OS_PROJECT_DOMAIN_ID=default
   $ export OS_PROJECT_NAME=demo
   $ export OS_IDENTITY_API_VERSION=3
   $ export OS_AUTH_TYPE=v3kerberos
   $ export OS_AUTH_URL=http://freeipa.openstack.local:5000/krb/v3
   $ openstack token issue

And if everything works...::

   +------------+----------------------------------+
   | Field      | Value                            |
   +------------+----------------------------------+
   | expires    | 2016-06-22T05:31:30.454344Z      |
   | id         | 7a224ffd6a634a5c99ec5e13395dfee2 |
   | project_id | 242c38acedd6464fad0523e215f97857 |
   | user_id    | d55e9576a7914f72a8312a955bbd1cc1 |
   +------------+----------------------------------+

Congratulations! You have a kerberized devstack that you can now use to review and develop kerberos-specific bugfixes and features.
