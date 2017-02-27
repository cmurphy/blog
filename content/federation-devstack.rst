:title: Testing Keystone Federation with Devstack
:slug: federation-devstack
:date: 2017-02-27 17:00

If you're interested in working on making keystone federation better or
reviewing federation-related keystone code, you need to have a development
environment that uses a federated identity backend. If you're not an operator
already running a Single Sign On service in production, it may not be obvious
to you how to set up something like this. In this post I'll talk about using
`TestShib`_ as a SAML Identity Provider or Google as an OpenID Connect Identity
Provider with devstack so that you can test out your keystone Service Provider.

See the `keystone federation documentation`_ for full details on setting up
federated keystone.

.. _`TestShib`: http://testshib.org
.. _`keystone federation documentation`: https://docs.openstack.org/developer/keystone/federation/federated_identity.html

Overview
--------

Keystone supports Federated Identity Providers, which means instead of storing
user information in its own database and using its own authentication
mechanisms to grant a token to a user, it calls to an external service to
outsource all of that. This is a step above using LDAP as an identity backend,
since LDAP is more or less just another type of database and keystone still has
to do most of the work authenticating the user.

There are two parts to federated identity. The Identity Provider (often called
the IdP) is the external service that contains users and deals with
authenticating them. Keystone can be an IdP itself but this post will not cover
that. The Service Provider (often called the SP) is the thing the user wants to
access, which here is keystone. The Identity Provider and the Service Provider
need to trust each other, so we provide each with some data about the other so
that they recognize each other when they are making and granting requests.

Keystone supports two federation protocols, SAML_ and `OpenID Connect`_. For
the SAML protocol, keystone supports two implementations, Shibboleth_ and
Mellon_.  Even though TestShib is geared toward the Shibboleth SAML
implementation, it can also be used with a Mellon Service Provider. All of
these Service Providers are implemented as Apache modules.

The end goal for this tutorial is to have keystone and horizon running and to
be able to log in to horizon, be redirected to TestShib or Google to
authenticate (using credentials that keystone has no information about), and
be redirected back to the (logged-in) horizon dashboard.

Terminology: a SAML assertion is the data that a SAML IdP sends as a response
to an authentication request that says that the user is authenticated and
provides data about the user such as their username.

Note that your SP does not need to be public. TestShib and Google do not need
to interface with it directly. All the negotiation happens via your browser, so
the only requirement is that you can reach both your SP and your IdP from your
browser.

.. _SAML: https://wiki.oasis-open.org/security/FrontPage
.. _`OpenID Connect`: http://openid.net/connect/
.. _Shibboleth: https://shibboleth.net/
.. _Mellon: https://github.com/UNINETT/mod_auth_mellon

Getting Started
---------------

This guide will assume you are running devstack on an Ubuntu Xenial virtual
machine. The instructions can be adapted for a RHEL-based machine. They
can probably be adapted for a SUSE-based machine as well but devstack isn't
currently gated on SUSE so it may require some extra work.

A Note about the Keystone Endpoint
``````````````````````````````````

It is important to note that most keystone documentation will refer to the
keystone endpoint with its public port, 5000. Devstack additionally configures
a path endpoint /identity that is equivalent and just uses the standard
HTTP/HTTPS ports. Horizon in devstack is configured to use that path endpoint
rather than the port. Devstack is `likely to stop listening on the port`_ so
where you see ``:5000`` in documentation you should replace it with
``/identity``.  In any case, you must be consistent everywhere, or both horizon
and the IdP will be confused.

.. _`likely to stop listening on the port`: http://lists.openstack.org/pipermail/openstack-dev/2017-February/112879.html

Install Devstack
----------------

We can use a minimal install of devstack running just keystone, horizon, and
the nova-api service (horizon depends on it). See the `devstack
documentation`_ for more information on configuring devstack.

.. code-block:: console

   $ git clone git://git.openstack.org/openstack-dev/devstack
   $ cd devstack
   $ cp samples/local.conf .
   $ echo ENABLED_SERVICES=rabbit,mysql,key,horizon,n-api >> local.conf
   $ ./stack.sh


.. _`devstack documentation`: https://docs.openstack.org/developer/devstack/

Install the Service Provider Apache Module
------------------------------------------

Devstack does most of the heavy lifting for us by installing Apache and
configuring vhosts but we need to make some tweaks.

For **Shibboleth**:

.. code-block:: console

   # apt-get install libapache2-mod-shib2

Also `check the Shibboleth SP Apache docs`_.

For **Mellon** [1]_:

.. code-block:: console

   # apt-get install libapache2-mod-auth-mellon

Also `check the mod_auth_mellon docs`_.

For **OpenID Connect** (the package doesn't automatically enable the module):

.. code-block:: console

   # apt-get install libapache2-mod-auth-openidc
   # a2enmod auth_openidc

Also `check the mod_auth_openidc docs`_.

.. _`check the Shibboleth SP Apache docs`: https://wiki.shibboleth.net/confluence/display/SHIB2/NativeSPApacheConfig
.. _`check the mod_auth_mellon docs`: https://github.com/UNINETT/mod_auth_mellon/blob/master/README
.. _`check the mod_auth_openidc docs`: https://github.com/pingidentity/mod_auth_openidc

Secret and Identifier Exchange
------------------------------

For the SAML SPs, we need to generate a keypair for encrypting the SAML
assertion, and exchange metadata between the SP and the IdP that will identify
the two entities to one another. For Google, we need to use the API tools to
generate an identifier and secret for your SP. Start here for `configuring your
SAML SP`_ or skip to `configuring your OpenID Connect SP`_. After this initial
exchange is done, the configuration for different SPs is very similar to one
another.

Configuring your SAML SP
````````````````````````

Decide on a Service Provider Entity ID
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The concept of an entity ID is not hard to grasp but it is often poorly
explained in documentation. It almost always looks like an HTTP URI. However,
it does not have to be an HTTP URI, and if it is an HTTP URI it does not have
to resolve to anything. The only thing that is required is that it is uniquely
identifiable to the IdP. Since TestShib has many users, you should probably not
try to use something like, for example, `http://example.com`, since it is
likely someone already tried that. In my case, I usually choose the entity ID
to be `http://devstack.colleen.$(uuidgen)`. This way I can always find my SP in
the TestShib logs by searching for devstack.colleen, but each time I create a
new SP (since I do this a lot) it is new to TestShib because it has a unique
UUID. I'll refer to it as `<SP entity ID>` from here.

Generate Keys
~~~~~~~~~~~~~

Your SP needs a public key to give to TestShib to encrypt the SAML assertion
that it will return after the user authenticates.

For **Shibboleth**, the Apache module package provides a utility to do this for
you:

.. code-block:: console

   # shib-keygen

This will generate a key pair and put them in ``/etc/shibboleth``.

For **Mellon**, there is a script that does not come with the package that you will
need to download:

.. code-block:: console

   $ wget https://raw.githubusercontent.com/UNINETT/mod_auth_mellon/master/mellon_create_metadata.sh
   $ chmod +x mellon_create_metadata.sh
   $ ./mellon_create_metadata.sh <SP entity ID> http://<SP fqdn or IP>/identity/v3/OS-FEDERATION/identity_providers/myidp/protocols/mapped/auth/mellon
   # mkdir /etc/apache2/mellon
   # cp *.cert /etc/apache2/mellon/sp.cert
   # cp *.key /etc/apache2/mellon/sp.key

Configure the Service Provider Metadata
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Shibboleth and Mellon have different approaches to generating metadata but the
end result is a SAML compatible XML file that you will upload to TestShib.

Shibboleth
''''''''''

Shibboleth uses ``/etc/shibboleth/shibboleth2.xml`` as its main configuration file.
This will be used both to generate the SP metadata as well as instruct
Shibboleth on how to fetch the IdP's metadata. The Apache module package
provides a decent default config file that you can make a few modifications to,
or you can have TestShib `generate one for you`_.

There are a few things you need to change about the file. First, set the
Service Provider entityID (the one that uniquely identifies your SP to
TestShib):

.. code-block:: xml

   <ApplicationDefaults entityID="<SP entity ID>"
                        REMOTE_USER="eppn persistent-id targeted-id">

Set TestShib's entity ID:

.. code-block:: xml

   <SSO entityID="https://idp.testshib.org/idp/shibboleth">

Add a MetadataProvider block:

.. code-block:: xml

   <MetadataProvider type="XML" uri="http://www.testshib.org/metadata/testshib-providers.xml" />

Upon the next restart Shibboleth will fetch TestShib's metadata from that URI.

Restart the Shibboleth daemon and Apache:

.. code-block:: console

    # service shibd restart
    # service apache2 restart

Download the generated metadata:

.. code-block:: console

   $ wget http://<public ip address>/Shibboleth.sso/Metadata

.. _`generate one for you`: http://www.testshib.org/configure.html

Mellon
''''''

For Mellon, you already generated the SP metadata when you ran
``mellon_create_metadata.sh``. It will have printed the name of the files it
created to the console, of which the metadata was the one ending in .xml.

You're not finished yet though. The metadata generated by this script
references the key it generated as a signing key. TestShib needs a key
specifically for encrypting the SAML assertion. You need to change the line
that say:

.. code-block:: xml

   <KeyDescriptor use="signing">

to:

.. code-block:: xml

   <KeyDescriptor use="encryption">

Now copy that file to the same place you copied the key pair:

.. code-block:: console

   # cp *.xml /etc/apache2/mellon/sp-metadata.xml

That's all. Mellon makes infuriatingly little use of logging so it will not be
obvious what happened from the SP's side if you don't fix the metadata, but it
will be evident from TestShib's logs.

Upload the SP Metadata to TestShib
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

`Upload the metadata to TestShib`_. For Shibboleth it was the Metadata file
that you downloaded, for Mellon it was the .xml file generated by the script.

The metadata file needs to be uniquely named from TestShib's point of view, so
it's a good idea to name it after the unique entity ID that you chose. If you
need to make changes to your metadata and upload it to TestShib again, you must
use the same file name. If you don't, TestShib may see two different records
for your SP's entity ID and get confused.

.. _`Upload the metadata to TestShib`: http://www.testshib.org/register.html

Download the IdP Metadata from TestShib
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For **Shibboleth**, you don't need to do anything here because you already told
Shibboleth where to find the IdP metadata when you modified
``shibboleth2.xml``.

For **Mellon**, download the IdP metadata directly and copy it to the same place
all of your other Mellon configuration is stored:

.. code-block:: console

   # wget -O /etc/apache2/mellon/idp-metadata.xml http://www.testshib.org/metadata/testshib-providers.xml

Configuring your OpenID Connect SP
``````````````````````````````````

Enabling your SP with Google's OpenID Connect server is a little simpler. You
will need a Google account. Use the `Google API console`_ to enable the Google+
API and then create an OAuth client ID. Under "Authorized redirect URIs" add
three URIs:

- ``http://<SP fqdn>/identity/v3/OS-FEDERATION/identity_providers/myidp/protocols/mapped/auth``
- ``http://<SP fqdn>/identity/v3/auth/OS-FEDERATION/websso``
- ``http://<SP fqdn>/identity/v3/auth/OS-FEDERATION/identity_providers/myidp/protocols/mapped/websso``

Google requires your redirect URIs to use a domain name ending in a real TLD,
so if your devstack instance does not have a DNS record you will need to make
sure both your devstack instance and your browser can resolve this domain,
perhaps by modifying your ``/etc/hosts`` files. Again, Google doesn't need to be
able to reach this domain itself, only your browser does.

Make a note of these URIs as well as the Client ID and Client secret that were
just generated.

.. _`Google API console`: https://console.developers.google.com

Configure the Keystone Apache Vhost
-----------------------------------

See the note at the beginning of this post about the keystone endpoint. If you
prefer to use keystone endpoint with port 5000, this additional configuration
belongs within the ``<VirtualHost *:5000>`` block, and you will omit the
``/identity`` from the Location paths. Otherwise, the configuration can go at
the end of the vhost file.

You can more or less copy and paste the Apache configs here. The Location
directives are configuring and protecting endpoints that keystone, horizon, and
TestShib/Google will use when negotiating the authentication of the user. The
important parts to note are that ``mapped`` refers to the **name of the
protocol object in keystone**, and ``myidp`` refers to the **name of the IdP
object in keystone**. These are entities that will be created later using the
keystone API or openstackclient commands.  ``myidp`` is an arbitrary name but
``mapped`` is not. I will explain this more later.

For **Shibboleth**, copy this to the keystone vhost:

.. code-block:: apache

   # Enable Shibboleth
   <Location /Shibboleth.sso>
       SetHandler shib
   </Location>

   # For keystone
   <Location /identity/v3/OS-FEDERATION/identity_providers/myidp/protocols/mapped/auth>
       ShibRequestSetting requireSession 1
       AuthType shibboleth
       ShibExportAssertion Off
       Require valid-user
   </Location>

   # For horizon
   <Location ~ "/identity/v3/auth/OS-FEDERATION/websso/mapped">
       AuthType shibboleth
       Require valid-user
       ShibRequestSetting requireSession 1
       ShibRequireSession On
       ShibExportAssertion Off
   </Location>
   <Location ~ "/identity/v3/auth/OS-FEDERATION/identity_providers/myidp/protocols/mapped/websso">
       AuthType shibboleth
       Require valid-user
   </Location>

   WSGIScriptAliasMatch ^(/identity/v3/OS-FEDERATION/identity_providers/.*?/protocols/.*?/auth)$ /usr/local/bin/keystone-wsgi-public/

Shibboleth works out most of its logic from the configuration in
``/etc/shibboleth`` so there is not that much to explain here, except that
we're declaring which paths need to need to be protected by the Shibboleth
module.

For **Mellon**, copy this:

.. code-block:: apache

   # Enable Mellon
   <Location /identity/v3>
       MellonEnable "info"
       MellonSPPrivateKeyFile /etc/apache2/mellon/sp.key
       MellonSPCertFile /etc/apache2/mellon/sp.cert
       MellonSPMetadataFile /etc/apache2/mellon/sp-metadata.xml
       MellonIdPMetadataFile /etc/apache2/mellon/idp-metadata.xml
       MellonEndpointPath /identity/v3/OS-FEDERATION/identity_providers/myidp/protocols/mapped/auth/mellon
       MellonSubjectConfirmationDataAddressCheck Off
       MellonIdP "IDP"
   </Location>

   # For keystone
   <Location /identity/v3/OS-FEDERATION/identity_providers/myidp/protocols/mapped/auth>
       AuthType "Mellon"
       MellonEnable "auth"
   </Location>

   # For horizon
   <Location ~ "/identity/v3/auth/OS-FEDERATION/websso/mapped">
     AuthType Mellon
     MellonEnable auth
     Require valid-user
   </Location>
   <Location ~ "/identity/v3/auth/OS-FEDERATION/identity_providers/myidp/protocols/mapped/websso">
     AuthType Mellon
     MellonEnable auth
     Require valid-user
   </Location>

   WSGIScriptAliasMatch ^(/identity/v3/OS-FEDERATION/identity_providers/.*?/protocols/.*?/auth)$ /usr/local/bin/keystone-wsgi-public/

There are a few things to note here. Make sure the ``MellonSPPrivateKeyFile``,
``MellonSPCertFile``, ``MellonSPMetadataFile``, and ``MellonIdPMetadataFile``
directives refer to the real locations where you copied your keypair and
metadata earlier. The other oddity is the
``MellonSubjectConfirmationDataAddressCheck`` directive. In my environment, my
virtual machine is a guest on my workstation in a network managed by libvirt,
and when my host makes requests to the SP on the virtual machine it uses the
client address 192.168.122.1, which is the libvirt gateway. When communicating
with the rest of the internet, however, especially TestShib, the client IP
address will present itself as the public address of the NAT in my office.
These are different addresses and Mellon will get confused by them being
different and you'll see something like this in the horizon logs::

  Wrong Address in SubjectConfirmationData.Current address is "192.168.122.1", but should have been "198.51.100.2".

To fix it, I set ``MellonSubjectConfirmationDataAddressCheck`` to off. You can
play with tunnels and proxy settings to avoid needing to do this, or if your
SP is on the public internet you will likely not have this problem at all.

For **OpenID Connect**, copy this:

.. code-block:: apache

   # Configure OIDC
   OIDCClaimPrefix "OIDC-"
   OIDCResponseType "id_token"
   OIDCScope "openid email profile"
   OIDCProviderMetadataURL https://accounts.google.com/.well-known/openid-configuration
   OIDCClientID <Google Client ID>
   OIDCClientSecret <Google Client Secret>
   OIDCCryptoPassphrase openstack
   OIDCRedirectURI http://<SP fqdn>/identity/v3/OS-FEDERATION/identity_providers/myidp/protocols/mapped/auth
   OIDCRedirectURI http://<SP fqdn>/identity/v3/auth/OS-FEDERATION/websso
   OIDCRedirectURI http://<SP fqdn>/identity/v3/auth/OS-FEDERATION/identity_providers/myidp/protocols/mapped/websso

   # For keystone
   <LocationMatch /identity/v3/OS-FEDERATION/identity_providers/.*?/protocols/mapped/auth>
     AuthType openid-connect
     Require valid-user
     LogLevel debug
   </LocationMatch>

   # For horizon
   <Location ~ "/identity/v3/auth/OS-FEDERATION/websso/mapped">
     AuthType openid-connect
     Require valid-user
   </Location>
   <Location ~ "/identity/v3/auth/OS-FEDERATION/identity_providers/myidp/protocols/mapped/websso">
     AuthType openid-connect
     Require valid-user
   </Location>

The ``OIDCClientID``, ``OIDCClientSecret``, and ``OIDCRedirectURI`` directives
should match the data that you noted when you enabled your project in the
Google API Console.

Configure Keystone
------------------

Now keystone needs to be told that we've set up federation.

In ``keystone.conf``, set the ``[federation]/remote_id_attribute``. This is the
key that keystone will use to look up the IdP's unique identifier in the
assertion response, which will be used later to look up the IdP in keystone's
database. Note that keystone will complain in the logs about not finding
``remote_id_attribute`` in the ``[mapped]`` section, but it looks next in the
``[federation]`` section to it's not a concern. To make the log message go
away, create a ``[mapped]`` section and set ``remote_id_attribute`` there
instead.

For **Shibboleth**, it's:

.. code-block:: ini

   [federation]
   remote_id_attribute = Shib-Identity-Provider

For **Mellon**, it's:

.. code-block:: ini

   [federation]
   remote_id_attribute = MELLON_IDP

For **OpenID Connect**, it's:

.. code-block:: ini

   [federation]
   remote_id_attribute = HTTP_OIDC_ISS

Set ``[federation]/trusted_dashboard`` to the horizon endpoint so that
keystone is okay with accepting federation requests from it:

.. code-block:: ini

   [federation]
   trusted_dashboard = http://<fqdn or IP>/dashboard/auth/websso/

The IP address or domain name is the address your browser will use to access
the dashboard.

The ``/dashboard`` path is configured by devstack. The keystone and horizon
documentation may not refer to it, but it is necessary with devstack unless
you change that redirect configuration.

The trailing / is required.

Copy the redirect template provided by keystone to the location given by
``[federation]/sso_callback_template``, which by default is
``/etc/keystone/sso_callback_template.html``:

.. code-block:: console

   $ cp /opt/stack/keystone/etc/sso_callback_template.html /etc/keystone

If you forget to do this, you'll get a 500 error and traceback in the keystone
logs with the error::

   No such file or directory: '/etc/keystone/sso_callback_template.html'

Configure Horizon
-----------------

In ``/opt/stack/horizon/openstack_dashboard/local/local_settings.py`` you need
to change two settings. First, turn on SSO:

.. code-block:: python

   WEBSSO_ENABLED = True

Second, make SAML authentication available as an authentication choice:

.. code-block:: python

   WEBSSO_CHOICES = (
     ("mapped", _("Authenticate Externally")),
   )

You may see ``("saml2", _("Security Assertion Markup Language"))`` and
``("oidc", _("OpenID Connect")`` as some of the example options. The first
entries in these tuples refer to the name of the keystone plugin and the
federation protocol that you will create. Here ``saml2`` could be used as the
name of the SAML2 plugin, and ``openid`` (but not ``oidc`` - this is incorrect)
could be used as the name of the OpenID Connect plugin, but in our examples
we've been using ``mapped`` for both.

Also check the ``OPENSTACK_KEYSTONE_URL`` setting and make sure it is
consistent with the endpoint you are using everywhere else, for example if your
Apache configuration refers to a domain name rather than the IP address, or
uses port 5000, then horizon must use that as well.

Restart Apache
--------------

After all that, we need to restart apache again for the changes to take
effect:

.. code-block:: console

   # service apache2 restart

Create Federated Resources
--------------------------

The last step is to create constructs within keystone's database to map
federated users to the resources they can access. This will all be done with
`python-openstackclient`_ using the local admin user created by devstack. The
credentials for the admin user are stored in ``accrc/admin/admin`` in the
devstack directory, so
source them:

.. code-block:: console

  $ source accrc/admin/admin

And also turn on the V3 API which is not used by default:

.. code-block:: console

   $ export OS_IDENTITY_API_VERSION=3

Create a special domain for the federated users:

.. code-block:: console

  $ openstack domain create federated_domain

Create a group:

.. code-block:: console

   $ openstack group create federated_users

Since keystone doesn't know about the users ahead of time, we need to use
groups to add role-based access control:

.. code-block:: console

   $ openstack role add --group federated_users --domain federated_domain admin

Create an object for the identity provider in keystone. For **Shibboleth** and
**Mellon** it is:

.. code-block:: console

   $ openstack identity provider create --remote-id https://idp.testshib.org/idp/shibboleth myidp

For **OpenID Connect** it is:

.. code-block:: console

   $ openstack identity provider create --remote-id https://accounts.google.com myidp

The remote-id is the unique identifier for the IdP. For TestShib it is always
`https://idp.testshib.org/idp/shibboleth`. If you forget or you want to use a
different SAML IdP, it's identified in ``shibboleth2.xml`` as the ``<SSO
entityID=...>`` node, or for Mellon it can be found in the IdP metadata that we
stored at ``/etc/apache2/mellon/idp-metadata.xml`` in the node
``<EntityDescriptor entityID=...>``. For Google, the unique identifier is
`https://accounts.google.com`, and it and other OpenID Connect providers will
note it as the "Issuer Identifier" or the "iss". Google historically used just
`accounts.google.com` as its Issuer Identifier, even though that `defies the
OpenID Connect protocol`_. It now `claims to support both identifiers`_, but I
found that only the ``https://`` one seems to work.

``myidp`` is an arbitrary name we are assigning to this reference object.  It
is not important what it is, but you must consistently refer to it when
configuring the Apache vhost, when providing the Mellon endpoint path to the
mellon_create_metadata.sh script, and in the following configuration steps.

Create a mapping to map federated users to objects in keystone. Mappings can be
very complicated but we'll just create a simple one.

It's not critical to getting things to work, but the "type" attribute for the
"remote" property is slightly different between Shibboleth, Mellon, and OpenID
Connect. For **Shibboleth**, the assertion data provided back to keystone
refers to the human-readable user identifier by the key ``REMOTE_USER``:

.. code-block:: console

    $ export remote_type=REMOTE_USER

For **Mellon**, it uses the a variable named after the `OID for
eduPersonPrincipalName`_:

.. code-block:: console

   $ export remote_type=MELLON_urn:oid:1.3.6.1.4.1.5923.1.1.1.6

For **OpenID Connect**, the e-mail key is convenient:

.. code-block:: console

   $ export remote_type=HTTP_OIDC_EMAIL

You can still use REMOTE_USER, but it may end up identifying the user by a
seemingly random string rather than something readable.

.. code-block:: console

   $ cat > rules.json <<EOF
   [
       {
           "local": [
               {
                   "user": {
                       "name": "{0}"
                   },
                   "group": {
                       "domain": {
                           "name": "Default"
                       },
                       "name": "federated_users"
                   }
               }
           ],
           "remote": [
               {
                   "type": "${remote_type}"
               }
           ]
       }
   ]
   EOF
   $ openstack mapping create --rules rules.json myidp_mapping

Create a "protocol" object that links the mapping object to the identity
provider object:

.. code-block:: console

   $ openstack federation protocol create mapped --mapping myidp_mapping --identity-provider myidp

The name ``mapped`` is not arbitrary. It is the name of the entrypoint linked
in setuptools, and it is the name of the auth method referenced in
``[auth]/methods`` in ``keystone.conf``. You could also call the protocol
``saml2`` if you are using Shibboleth or Mellon, or ``openid`` for OpenID
Connect, but it is more convenient in these examples to call it ``mapped``
since using that plugin will `use the correct logic for any federation
provider`_. You must be consistent when referring to protocol in all of the
endpoints configured in your Apache vhosts, in your horizon configuration, and
your metadata configuration.

After all that, try logging into the Horizon dashboard. After clicking on the
appropriate "Authenticate using" dropdown (if necessary) and clicking
"Connect", you should be redirected to a login page hosted by TestShib or
Google. After you log in, you should be redirected back to the horizon
dashboard and able to manage keystone resources for the federated_domain
domain.

.. _`python-openstackclient`: https://docs.openstack.org/developer/python-openstackclient/
.. _`OID for eduPersonPrincipalName`: http://www.internet2.edu/products-services/trust-identity/mace-registries/internet2-object-identifier-oid-registrations/
.. _`defies the OpenID Connect protocol`: http://openid.net/specs/openid-connect-core-1_0.html#GoogleIss
.. _`claims to support both identifiers`: https://developers.google.com/identity/protocols/OpenIDConnect#validatinganidtoken
.. _`use the correct logic for any federation provider`: https://specs.openstack.org/openstack/keystone-specs/specs/keystone/juno/generic-mapping-federation.html

Debugging Tips
--------------

Turn logging up to the max everywhere. For keystone, turn on
``insecure_debug``.  For horizon, turn the
``LOGGING['handlers']['console']['level']`` setting in ``local_settings.py`` to
``'DEBUG'``, which will allow the openstack_auth django plugin to emit
debug logs to the horizon log file.

If something went wrong with TestShib, you might see a page that says
"Something went horribly wrong" and provides a link to the log file. Even if
you don't see this page, but your own Apache logs are being less than helpful,
you can still `check the TestShib logs`_. Mellon does not like to provide a lot
of information in the logs: you may see something exceedingly unhelpful like::

   Error processing authn response. Lasso error: [-432] Status code is not success

when you get 400 or 500 error, but this is where the TestShib logs can be
helpful. Keep in mind that these logs are shared by everyone running tests on
TestShib, so you have to fetch the log immediately after the error occurs,
otherwise you might be looking at someone else's login attempts. Also note
that debug messages like::

   No custom relying party configuration found for <your SP entity ID>

are normal messages, they don't necessarily mean that your SP's metadata
couldn't be found or was invalid.

Your browser will store a cookie that will keep you authenticated for a while,
so if you want a fresh start at logging in, you can log out of TestShib by
`visiting the logout page`_. If you had managed to successfully log in to
horizon, you'll need to log out of it as well by clicking the logout button in
the top right. If you've managed to get yourself into a state where you can't
see the dashboard in order to click the logout button, you can go directly to
the logout endpoint at ``/dashboard/auth/logout``.

Finally, use the `SAML tracer`_ plugin for firefox. It is like a souped-up
version of the network console tool, specifically for showing the SAML-related
data passed in web requests.

.. _`check the TestShib logs`: https://idp.testshib.org/cgi-bin/idplog.cgi?lines=300
.. _`SAML tracer`: https://addons.mozilla.org/En-us/firefox/addon/saml-tracer/
.. _`visiting the logout page`: https://www.testshib.org/Shibboleth.sso/Logout

The End
-------

Congratulations, you made it all the way to the end of this blog post! For your
efforts, here is a set of scripts and ansible playbooks that will set all this
up for your automatically. Enjoy.

`github.com/cmurphy/federated-devstack <https://github.com/cmurphy/federated-devstack>`_

.. [1] On Ubuntu Trusty, I needed to install `liblasso`_ and `mod_auth_mellon`_
   from source. When using the Ubuntu Trusty packages, Mellon includes a
   Signature parameter in its initial SAML request that TestShib can't deal
   with, and you'll see warnings like this in TestShib's logs::

      Simple signature validation (with no request-derived credentials) failed
      Validation of request simple signature failed for context issuer: http://devstack.colleen/68594e06-a329-5707-b810-60bcb00725b3

   On Xenial this problem does not occur.

.. _`liblasso`: http://lasso.entrouvert.org/
.. _`mod_auth_mellon`: https://github.com/UNINETT/mod_auth_mellon
