:title: Demystifying Keystone Federation
:slug: demystifying-keystone-federation
:sortorder: 40
:date: 2017-12-09 15:00

While I am not one of the people who implemented federated auth in keystone, as
a keystone maintainer I had to learn about it. This post is about all the
things that are not obvious to someone with no background in this stuff,
including what it is and why it is useful, how it works, and how to set it up
in keystone.

What is federated identity?
---------------------------

Federated identity is the ability to share a single authentication mechanism
across many systems, in our case clouds. There are a few scenarios where this
could be needed:

#. Typically, your organization will already have a source of identity, so
   creating another set of credentials just to use on your cloud means a whole
   other set of accounts to manage. It's easier if your cloud understands how to
   talk to your Identity Provider.

#. Alternatively, instead of just having to deal with accounts within a single
   organization, you might have partner organizations with shared resources. You
   might want to give individuals from your partner organization access to your
   resources without creating internal accounts for them. In this case, you could
   set up your cloud to talk to *their* Identity Provider.

#. Finally, you might have a workload that needs to "burst" from your private
   cloud to a public cloud or hosted private cloud. To make this possible, you can
   set up your local keystone as an Identity Provider, and the public or hosted
   private cloud shares that Identity Provider.

Why is this better, or even different, than LDAP? When we use LDAP as an
identity source for an application, it simply acts as a storage backend. The
application must still handle accepting a username and password and making an
authentication decision about whether the user exists in its backend and has
provided the right password. With federation, the authentication step
completely sidesteps the application. Whenever your user logs in to the system,
they do so with a familiar authentication portal instead of giving their
credentials to an unknown application.

How does this work in keystone?
-------------------------------

When we talk about federation in keystone, we could mean two different things:

* Keystone using an external Identity Provider as an auth method (introduced in
  Icehouse)

This type of federation solves the first two cases, where you have an existing
identity management system that needs to hook into keystone. In this case, all
of the hard work is done by a web server module sitting in front of keystone.

* Keystone as an Identity Provider, also called Keystone to Keystone (introduced
  in Kilo)

This type of federation was introduced for the "bursting" use case, though it
could also be used to connect partner organizations that both have OpenStack
clouds.

Vocabulary
----------

There are some terms that are helpful to know up front.

Service Provider (SP)
~~~~~~~~~~~~~~~~~~~~~

A Service Provider is the thing with the resource we need. In our case, this is
keystone, which provides keystone tokens that we use on other OpenStack
services. We do NOT call the other OpenStack services "service providers". The
specific service we care about in this context is the token service, so that is
our Service Provider.

Identity Provider (IdP)
~~~~~~~~~~~~~~~~~~~~~~~

An Identity Provider is the thing that accepts your credentials, validates them,
and generates a yay/nay response. It returns this response along with some other
attributes about you, like your username, your display name, and whatever other
details it stores and you've configured your Service Provider to accept.

Entity ID, or Remote ID
~~~~~~~~~~~~~~~~~~~~~~~

An Entity ID or a Remote ID are both names for a unique identifier string for
either a Service Provider or an Identity Provider. It usually takes the form of
a URN, but do not let that confuse you: the URN does not need to be a
resolvable URL. The only requirement is that it uniquely identifiers the IdP to
the SP, or the SP to the IdP. So if you have a lot of Service Providers sharing
on Identity Provider, they can't all have the ID "example.com".

SAML2.0
~~~~~~~

SAML2.0 is an XML-based federation protocol. There are other types of federation
protocols, but this tutorial will only focus on SAML2.0 because it is very
common and also somewhat more painful to deal with.

Assertion
~~~~~~~~~

An assertion is a formatted statement from the Identity Provider that asserts
that a user is authenticated and provides some attributes about the user. The
Identity Provider always signs the assertion and typically encrypts it as well.

Frequently Asked Questions
--------------------------

Before diving in too deep, it might be good to go over some points that either I
have been asked a lot or was confused about while I was learning this.

What federated protocols are supported?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you look at our documentation, it kind of looks like we support two
federation protocols, SAML (two different implementations) and OpenID Connect.
The reality is that keystone is doing almost none of the work, the entire
authentication process is handled by a web server auth module. So as long as you
can get a web server auth module perform some kind of auth sequence turn it into
a REMOTE_USER environment variable, keystone can support it. Some examples are
SAML2.0 (using the mod_auth_mellon or Shibboleth Apache modules), OpenID
Connect, x509, or Kerberos.

The exception is when we're talking about keystone as an Identity Provider, in
which case all it can speak is SAML. Even then, it has pretty limited
functionality, so you could not really say it's fully implementing the SAML2.0
spec.

Can I have LDAP and fedeation at the same time?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Yes, you could have both of these in a single keystone deployment. LDAP is an
identity backend and federation is an auth method. They can coexist.

What if my Identity Provider is behind a firewall?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For a SAML2.0 system, no direct connection is needed between the Identity
Provider and the Service Provider. All negotiation is done through the client,
e.g. the user's browser.

What are shadow users?
~~~~~~~~~~~~~~~~~~~~~~

A shadow user is a local copy of a federated user's attributes, like their
username, as well as an internally generated ID so that keystone can assign
roles to the user. If the user only lived within the IdP and no where else,
keystone would not be able to do anything with it besides issue it an unscoped
token. So we keep a copy of everything we know about the user (which does not
include their password).

Keystone does this automatically so that we have a way of dealing with ephemeral
users. However, you can also manually create keystone users and use mapping
rules to map federated users to local keystone users. You might do this if you
wanted a little more control over how keystone handles users.

If you're diving into the keystone code and looking for the "shadow users" table, you
won't really find it. The name "shadow users" applies to both LDAP users and
federated users, but we've given them different SQL tables, called
`nonlocal_user` for LDAP users and `federated_user` for federated users.

Auth Flows
----------

Now we can get into the nitty-gritty stuff. Flow diagrams can be tough to absorb
but it is helpful to have a picture of it for debugging later.

Normal keystone
~~~~~~~~~~~~~~~

.. image:: {filename}/images/normal-keystone.png

In a normal keystone flow, the user requests a scoped token directly from
keystone. Keystone accepts their credentials and checks them against its local
storage or against its LDAP backend. Then it checks the scope that the user is
requesting, ensuring they have the correct role assignments, and produces a
scoped token. The user can use the scoped token to do something else in
OpenStack, like request servers, but everything that happens after the token is
produced is irrelevant to this discussion.

SAML2.0 WebSSO
~~~~~~~~~~~~~~

.. image:: {filename}/images/websso.png

WebSSO is one of a few SAML profiles. It is entirely based on the idea that a
web browser will be acting as an intermediary and so the whole flow involves
things that a browser can understand, like HTTP redirects and HTML forms.

First, the user uses their web browser to request some secure resource from the
Service Provider. The Service Provider detects that the user isn't authenticated
yet, so it generates a SAML Request which it base64 encodes, and then issues an
HTTP redirect to the Identity Provider.

The browser follows the redirect and presents the SAML Request to the Identity
Provider. The user is prompted to authenticate, probably by filling out a
username and password in a login page. The Identity Provider responds with an
HTTP success and generates a SAML Response with an HTML form.

The browser automatically POSTs the form back to the Service Provider, which
validates the SAML Response. The Service Provider finally issues another
redirect back to the original resource the user had requested.

SAML2.0 ECP
~~~~~~~~~~~

.. image:: {filename}/images/ecp.png

ECP is another SAML profile. Generally the flow is similar to the WebSSO flow,
but it is designed for a client that natively understands SAML, for example the
keystoneauth library (and therefore also the python-openstackclient CLI tool).
I call out ECP specifically because it is slightly different from the
browser-based flow, and so while it is often tempting to, during debugging, drop
down to the shell and try to get things working from there, they are different
enough that getting one working does not necessarily mean the other works. They
could also both be broken but for different reasons. For instance, ECP support
must often be turned on explicitly in the Identity Provider, so if your identity
management team has not enabled it, it will not work and therefore not get you
any closer to understanding why your browser flow is broken.

WebSSO with keystone and horizon
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. image:: {filename}/images/websso-keystone-horizon.png

When we apply WebSSO to keystone using an external Identity Provider, things get
a little more complicated. Keystone is still the Service Provider, but keystone
is not a web front-end. This means we need to teach horizon how to handle some
parts of being a Service Provider.

In the diagram above, in addition to adding horizon into the mix, I've split out
keystone and Apache from each other to distinguish which parts each are in
charge of, even though we would typically refer to both of them together as the
Service Provider.

In this model, the user requests to log in to horizon by selecting a federated
authentication method from a dropdown menu. Horizon automatically generates a
keystone URL based on the Identity Provider and protocol selected and redirects
the browser to keystone. That location is equivalent to the ``/secure`` resource
in the SAML2.0 WebSSO diagram. The browser follows the redirect, and the Apache
module detects that the user isn't logged in yet and issues another redirect to
the Identity Provider with a SAML Request. At this point, the flow is the same
as in the normal WebSSO model. The user logs into the Identity Provider, a SAML
Response is POSTed back to the Service Provider, where the Apache module
validates the response and issues a redirect back to the location that horizon
had originally requested, which is a special federation auth endpoint. At this
point keystone is able to grant an unscoped token, which it hands off as another
HTML form. The browser will POST that back to horizon, which triggers the normal
login process, picking a project to scope to and getting a scoped token from
keystone.

Note that here, horizon is acting as a middle-man for us, since it knows the
endpoint of the secure resource it requests from keystone.

Keystone to Keystone
~~~~~~~~~~~~~~~~~~~~

.. image:: {filename}/images/k2k.png

When keystone is used as an Identity Provider, the auth flow is pretty unique.
It doesn't follow any of the SAML standards, though you could say it's similar
to an IdP-initiated auth flow. In this case, the user goes directly to the
Identity Provider first before requesting any resource from the Service
Provider. The user will get a token from keystone, then use that to request a
SAML Response via ECP. When it gets that response back, it POSTs that to the
Service Provider, which will grant a token for it.

Notice that the Service Provider has to accept data from the Identity Provider
and therefore needs to have a way of trusting it. The Identity Provider, on the
other hand, never has to accept data from the Service Provider. There is no back
and forth, the user simply completes the auth process on one side and presents
the result to the other side.

Setting up Keystone with an External Identity Provider
------------------------------------------------------

For this proof of concept, I used `this node.js app`_ as my Identity Provider.
You could also use `testshib.org`_ as an Identity Provider (if you're not
concerned about the demo gods killing your wifi connection mid-presentation).
Testshib supports ECP so it may be more useful depending on what you want to
test out. Obviously neither of these are meant for production use.

I'm also using `devstack`_ for my OpenStack implementation, which uses uwsgi to
run keystone and Apache as a proxy in front of it.

Make sure to turn on debug logging, and also turn on the ``insecure_debug``
option in ``keystone.conf``. Since we are dealing with authentication, normal
operating mode deliberately does not provide detailed information on the cause
of auth failures. While this proof of concept is being set up, detailed
information is crucial. Remember to turn this off before putting this into
production.

.. _this node.js app: https://github.com/mcguinness/saml-idp
.. _testshib.org: http://www.testshib.org/
.. _devstack: https://docs.openstack.org/devstack/latest/

Set up horizon
~~~~~~~~~~~~~~

First, configure horizon to expect a federated login. This will enable a
dropdown menu for the user to select how to authenticate.

In horizon's ``local_settings.py`` config file turn on WEBSSO and configure the
dropdown menu:

.. code-block:: python

   WEBSSO_ENABLED = True
   WEBSSO_CHOICES = (
       ("credentials", "Keystone Credentials"), 
       ("saml2", "My Awesome IdP")
   )

``"credentials"`` is a special keyword in horizon that means to log in directly
with keystone. ``"saml2"`` is the name of the federated protocol that we will
configure later. There are some other ``WEBSSO_*`` options you can investigate.

After this, you can restart Apache and visit the horizon login page to see the
new dropdown menu. Of course this won't be functional yet since we haven't set
up keystone yet.

.. image:: {filename}/images/dropdown.png

Create federation resources in keystone
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We need to create three resources via the keystone API to identify the Identity
Provider to keystone and align remote user attributes with keystone objects.
First, the Identity Provider:

.. code-block:: console

   $ openstack identity provider create demoidp --remote-id=urn:example:idp

Aside from a name, an Identity Provider needs a remote ID, also called an entity
ID. You can obtain this value from the Identity Provider by querying its
metadata endpoint:

.. code-block:: console

   $ curl -s http://idp.saml.demo:7000/metadata | grep entityID
   <EntityDescriptor entityID="urn:example:idp" xmlns="urn:oasis:names:tc:SAML:2.0:metadata">

Next, we create a mapping. A mapping is a set of rules that link the attributes
of a remote user to user properties that keystone understands. It is especially
useful for granting remote users authorization to keystone resources, either by
associating them with a local keystone group and inheriting its role
assignments, or dynamically provisioning projects within keystone based on these
rules. Mappings can be quite complicated, but we are only going to use simple
ones here. For more information on advanced mappings, `see the documentation`_.

.. _see the documentation: https://docs.openstack.org/keystone/latest/advanced-topics/federation/federated_identity.html#mapping-combinations

Create a file named ``rules.json`` that looks like this:

.. code-block:: json

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
                   "type": "email"
               }
           ]
       }
   ]

The remote type in this example is an attribute set by the Identity Provider
I've chosen, it will not be the same for all Identity Providers. It's common to
use the REMOTE_USER variable, set by the web server auth module, as the username
attribute. The available properties are also dependent on the Service Provider
auth module we use, and in this case we'll need to configure our auth module to
allow the ``email`` attribute through.

Create the mapping in keystone with:

.. code-block:: console

   $ openstack mapping create demomap --rules=rules.json

Create a federation protocol resource to link the Identity Provider to the
mapping.

.. code-block:: console

   $ openstack federation protocol create \
     --identity-provider demoidp \
     --mapping demomap \
     saml2

The name of the federation protocol here, ``saml2``, is not arbitrary. It must
match the name of an federated auth method in keystone. Those auth methods are
entrypoints to the Mapped auth plugin, listed in `keystone's setup file`_.

.. _keystone's setup file: http://git.openstack.org/cgit/openstack/keystone/tree/setup.cfg?h=12.0.0#n100

Set up Apache
~~~~~~~~~~~~~

First you'll need to install the Service Provider auth module. In these
examples, I'm using the Shibboleth implementation of a SAML2.0 Service Provider.
On OpenSUSE you can install this with:

.. code-block:: console

   # zypper install shibboleth-sp

On other distros the package will be called something different. You can also
use a different SAML2.0 implementation, like `mod_auth_mellon`_, but the
configuration will be different.

.. _mod_auth_mellon: https://github.com/UNINETT/mod_auth_mellon

Next, you can set up protected Locations in your keystone vhost file:

.. code-block:: apache

   Proxypass Shibboleth.sso !
   <Location /Shibboleth.sso>
       SetHandler shib
   </Location>

   <Location /identity/v3/OS-FEDERATION/identity_providers/demoidp/protocols/saml2/auth>
       AuthType shibboleth
       Require valid-user
       ShibRequestSetting requireSession 1
       ShibExportAssertion Off
   </Location>

   <Location /identity/v3/auth/OS-FEDERATION/websso/saml2>
       AuthType shibboleth
       Require valid-user
       ShibRequestSetting requireSession 1
       ShibExportAssertion Off
   </Location>

The first block sets up a special Shibboleth-specific endpoint for
administrative things, like retrieving metadata. In devstack, Apache is set up
with mod_proxy to proxy to keystone's uwsgi service, and we need to bypass that
with "``Proxypass Shiboleth.sso !``". You might not need this line if you've
configured your keystone differently.

The next two blocks set up auth endpoints, one for ECP and one for WebSSO,
protected by Shibboleth. Notice the name of the identity provider ``demoidp``
and the name of the federation protocol ``saml2``, which we set up in the last
section.

On some distros you will need to set up a PKI pair for Shibboleth to use.
Ubuntu, for example, provides a utility for this:

.. code-block:: console

   # shib-keygen

On openSUSE, the ``shibboleth-sp`` package sets up a key pair for you upon
installation. The certificate does not need to be signed by a certificate
authority since we are going to directly exchange keys with the Service Provider
later.

Configure Metadata
~~~~~~~~~~~~~~~~~~

Shibboleth uses a config file at ``/etc/shibboleth/shibboleth2.xml``. You need
to change three settings in it.

First, set the entity ID. Choose something that will uniquely identify your
Service Provider to your Identity Provider.

.. code-block:: xml

   <ApplicationDefaults entityID="http://sp.keystone.demo/shibboleth"
       REMOTE_USER="eppn persistent-id targeted-id">

Then set the entity ID, or remote ID, of the Identity Provider. It is the same
as the value given for the ``--remote-id`` parameter when you created the
Identity Provider resource in keystone before.

.. code-block:: xml

   <SSO entityID="urn:example:idp">

Tell Shibboleth where to find the metadata of the Identity Provider. You could
either tell it to fetch it from a URI or point it to a local file. For example,
pointing to a local file:

.. code-block:: xml

   <MetadataProvider type="XML" file="/etc/shibboleth/idp.saml.demo.xml" />

We also need to configure Shibboleth to accept the ``email`` attribute from the
Identity Provider. In ``/etc/shibboleth/attribute-map.xml`` add a new attribute:

.. code-block:: xml

   <Attribute name="email" nameFormat="urn:oasis:names:tc:SAML:2.0:attrname-format:basic" id="email" />

Exchange Metadata
~~~~~~~~~~~~~~~~~

Copy the Identity Provider's metadata to the path where the Service Provider can
find it.:

.. code-block:: console

   # curl -o /etc/shibboleth/idp.saml.demo.xml http://idp.saml.demo:7000/metadata

Restart the Shibboleth daemon and Apache:

.. code-block:: console

   # systemctl restart shibd apache2

For most Identity Providers, you will also need to upload the Service Provider's
metadata as well. You can find that here:

.. code-block:: console

   $ curl http://sp.keystone.demo/Shibboleth.sso/Metadata

The method of uploading metadata will differ between Identity Providers. In the
case of the node.js-based one I've chosen, it doesn't do any strict validation
and so doesn't need the Service Provider's metadata, but you do have to set the
"SP Audience URI" to the Service Provider's Entity ID.

Finish set up
~~~~~~~~~~~~~

There are a few more settings to set in keystone. We need to enable the
federated auth method ``saml2``, the same as the name of the federated protocol
we created with keystone. In ``keystone.conf``, add an auth method:

.. code-block:: ini

   [auth]
   methods = external,password,token,oauth1,saml2

Create a new section named after the auth method, and set a
``remote_id_attribute`` for it. This is the key that keystone will look for in
the request to obtain the remote ID (entity ID) of the Identity Provider so it
can associate it with its own Identity Provider resource. The key is decided by
the Service Provider software: for Shibboleth it is Shib-Identity-Provider.

.. code-block:: ini

   [saml2]
   remote_id_attribute = Shib-Identity-Provider

Set horizon as the trusted dashboard. Recall that horizon is acting as a kind of
middle-man in the WebSSO flow, so in order to prevent man-in-the-middle attacks,
we authorize its source URL. The exact path will depend on your Apache
configuration. The easiest way to not set it at all and look for the message
"... is not a trusted dashboard host" in the error output or keystone logs.

.. code-block:: ini

   [federation]
   trusted_dashboard = http://sp.keystone.demo/dashboard/auth/websso/

Restart keystone. On devstack you need to restart the keystone systemd service:

.. code-block:: console

   # systemctl restart devstack@keystone

Recall that the mapping we created mapped federated users to a local group
called ``federated_users``. Create that group now, and assign it some role on a
project:

 .. code-block:: console

    $ openstack group create federated_users
    $ openstack role add --group federated_users --project demo Member

Copy the callback template into place. This is the HTML form that keystone will
send to horizon with the token:

.. code-block:: console

   $ cp /opt/stack/keystone/etc/sso_callback_template.html /etc/keystone/

Now, log in to your horizon dashboard using your new authentication method.

If you have ECP enabled on your Identity Provider (the node.js app I am using
does not, but Testshib does), you can also use the command line to get a token:

.. code-block:: console

   $ openstack \
   --os-auth-type v3samlpassword \
   --os-identity-provider testshib \
   --os-identity-provider-url https://idp.testshib.org/idp/profile/SAML2/SOAP/ECP \
   --os-protocol saml2 \
   --os-username myself \
   --os-password myself \
   --os-auth-url http://sp.keystone.demo/identity/v3 \
   --os-project-name demo \
   --os-project-domain-name Default \
   --os-identity-api-versione 3 \
   token issue

Setting up Keystone to Keystone
-------------------------------

To set up Keystone to Keystone, it is helpful to set up your keystone Service
Provider first, as shown above, with a dummy Identity Provider. This minimizes
the number of variables in play. Once this is done, bring up another OpenStack
instance. For a proof of concept, this technically only needs keystone and
horizon, not nova and friends, but your production needs are likely more
complex.

You do not need to change any horizon settings on your Identity Provider server,
all new menus will be added automatically.

Configure the Identity Provider
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

First, install the ``xmlsec1`` package on the Identity Provider:

.. code-block:: console

   # zypper install xmlsec1

On openSUSE Leap 42.2 I also had to install ``libxmlsec1-openssl1``.

Configure your Identity Provider's metadata in the ``[saml]`` section of
``keystone.conf`` (not to be confused with the ``[saml2]`` section which you
just added to your Service Provider's ``keystone.conf``). There are a
minimum of two options that need to be set:

.. code-block:: ini

   [saml]
   idp_entity_id=http://idp.keystone.demo/idp
   idp_sso_endpoint=http://irrelevant

The first, ``idp_entity_id`` is your Identity Provider's entity ID, a string of
your choosing that uniquely identifies it to your Service Provider. The second,
``idp_sso_endpoint``, must be set in order to have valid metadata, but in a
Keystone to Keystone deployment, it is completely meaningless. If, someday, we
turn keystone into a fully-fledged Identity Provider, this option would be used
to set the HTTP-POST binding, but we don't currently use it for anything.

Also note the default values of the ``[saml]/certfile``, ``[saml]/keyfile``, and
``[saml]/idp_metadata_path`` options and change them if you need to. There are
also a number of ``idp_`` settings that control the metadata values if you want
to change them.

Generate a PKI key pair and add the cert and key to the paths given in the
keystone config.

.. code-block:: console

   $ mkdir -p /etc/keystone/ssl/{certs,private}
   $ openssl req -x509 -newkey rsa:4096 \
     -keyout /etc/keystone/ssl/private/signing_key.pem \
     -out /etc/keystone/ssl/certs/signing_cert.pem \
     -days 365 -nodes

Generate the metadata:

.. code-block:: console

   $ keystone-manage saml_idp_metadata > /etc/keystone/saml2_idp_metadata.xml

The output of the ``keystone-manage`` command is redirected to the local file,
but a quirk of this command is that errors are also in stdout and will end up in
the file, so make sure to check that the file contains XML metadata and not
error messages.

Once the metadata is created, restart the keystone service.

.. code-block:: console

   # systemctl restart devstack@keystone

Last, create a Service Provider resource in the keystone Identity Provider:

.. code-block:: console

   $ openstack service provider create keystonesp \
   --auth-url http://sp.keystone.demo/identity/v3/OS-FEDERATION/identity_providers/keystoneidp/protocols/saml2/auth \
   --service-provider-url http://sp.keystone.demo/Shibboleth.sso/SAML2/ECP

The ``--auth-url`` value is the federated auth endpoint, specific to this
identity provider. The ``--service-provider-url`` value is the PAOS binding to
handle ECP requests, which you can find in the Service Provider's metadata:

.. code-block:: console

   $ curl -s http://sp.keystone.demo/Shibboleth.sso/Metadata | grep urn:oasis:names:tc:SAML:2.0:bindings:PAOS
   <md:AssertionConsumerService Binding="urn:oasis:names:tc:SAML:2.0:bindings:PAOS" Location="http://sp.keystone.demo/Shibboleth.sso/SAML2/ECP" index="4"/>

Configure the Service Provider
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

I'm assuming the Service Provider was already set up with a dummy Identity
Provider, so we're just making modifications so that it works with the new
keystone Identity Provider.

First, create a new Identity Provider resource, a mapping, and federation
protocol in the keystone Service Provider. Recall the entity ID you set for the
Identity Provider:

.. code-block:: console

   $ openstack identity provider create keystoneidp \
   --remote-id http://idp.keystone.demo/idp

Create a new mapping. In this case, the attributes from the keystone Identity
Provider are not the same as those from any other Identity Provider, so the
remote type that maps to the username will be different:

 .. code-block:: json

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
                    "type": "openstack_user"
                }
            ]
        }
    ]

.. code-block:: console

   $ openstack mapping create --rules rules.json k2kmap

And create the federation protocol. We are still giving it the same name,
``saml2``, but now associating it with our new Identity Provider and mapping:

.. code-block:: console

   $ openstack federation protocol create \
     --identity-provider keystoneidp \
     --mapping k2kmap \
     saml2

Now we need to protect that federated auth path that we associated with the
Service Provider resource that was created on the keystone Identity Provider. In
your keystone vhost file, add a new Location stanza or modify the existing one
to point to the right Identity Provider:

.. code-block:: apache

   <Location /identity/v3/OS-FEDERATION/identity_providers/keystoneidp/protocols/saml2/auth>
       AuthType shibboleth
       Require valid-user
       ShibRequestSetting requireSession 1
       ShibExportAssertion Off
   </Location>

Update ``/etc/shibboleth/shibboleth2.xml`` to point to the right Identity
Provider and get its metadata (which you generated with ``keystone-manage``,
either from a local file or a remote URI:

.. code-block:: xml

   <SSO entityID="http://idp.keystone.demo/idp">
   ...
   <MetadataProvider type="XML" uri="http://idp.keystone.demo/identity/v3/OS-FEDERATION/saml2/metadata" />

Allow the ``openstack_user`` attribute through the Service Provider by adding it
to ``/etc/shibboleth/attribute-map.xml``:

.. code-block:: xml

   <Attribute name="openstack_user" id="openstack_user" />

Restart Shibboleth and Apache:

.. code-block:: console

   # systemctl restart shibd apache2

Log in
~~~~~~

Now, log in to the horizon on the Identity Provider with your normal keystone
credentials. In the top right of the dashboard, there should be a new panel:

.. image:: {filename}/images/k2klogin.png

You can select your keystone Service Provider from the dropdown and log in to
the Service Provider cloud.

You can also use the command line to get a token:

.. code-block:: console

   $ openstack \
   --os-service-provider keystonesp \
   --os-remote-project-name demo \
   --os-remote-project-domain-name Default \
   token issue
