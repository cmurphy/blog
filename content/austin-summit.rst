:title: OpenStack Austin - Session Summaries
:slug: austin-summit
:sortorder: 20
:date: 2016-05-05 15:10

This summit, I attempted to take notes during design summit sessions
where I played the listen-and-learn role as opposed to the active
decision-influencing role. This is a summary of some of those sessions so that I or
anyone else can get a brief at-a-glance review of what took place.


Deployment Tools - Tuesday, 11:15
---------------------------------

`https://etherpad.openstack.org/p/newton-deployment-tools-discussion <https://etherpad.openstack.org/p/newton-deployment-tools-discussion>`_

The various deployment teams (represented in the room were ansible, kolla,
puppet, fuel, chef, tripleo, and juju) all face similar problems. Let's
identify them, and find a way to help each other.

CI is challenge we could easily coordinate on. Multinode gating is something
all the deployment tools want, though only a few have done the work to
implement. The room expressed that multinode testing was needed for two
reasons: 1) "it's not representative of a real deployment if it's not
multinode", that is, multinode testing will help us uncover bad assumptions
about network connectivity, and 2) deploying all the openstack projects on one
VM with 8GB of RAM is not possible. Docker or other container solutions could
be used to help with the first issue. Having multiple jobs that cover disjunct
scenarios could help with the second issue. The Kolla project is already
successfully running multinode jobs, as is the TripleO team, though they run
their own CI. The Infra team wants to make it clear that we should only really
be using multinode testing when we really have to, and in a lot of cases single
node will be just fine. The Infra team also wants to stress the idea that "we
are all infra", that is, we all have influence over how to run our testing
infrastructure, we do not need to just butt heads with the mean infra team who
always says no.

Packaging is a subject that everyone handles differently, and the group
wondered whether we should be moving toward similar strategies. It was decided
that no, deploying from distro packages versus pip packages versus stable
branches versus master are all valid choices and every group has the right to
make opinionated decisions about this. It is important that, no matter how
deployments are done, whenever one group catches a problem, they work to fix it
and to notify all the other groups.

To this end, a deployment tools group will be created, which will have regular
meetings at some interval. This will give us a chance to talk to each other
about issues we are facing and to talk to the Infra team about how to improve
our CI.

Identity v3 in Devstack - Tuesday, 2:00
---------------------------------------

`https://etherpad.openstack.org/p/newton-keystone-v3-devstack <https://etherpad.openstack.org/p/newton-keystone-v3-devstack>`_

We want to make Identity V3 the default in devstack, but a patch that did this
ended up breaking a lot of things. Reasons things broke include hardcoded use
of the v2.0 endpoint, use of the keystoneclient CLI, requesting V2 tokens, and
not using keystoneauth sessions. Unfortunately it is impossible to know ahead
of time what projects will break. The way forward here is to create messaging
to the projects to ask them to prepare, instruct them on how to prepare, ask
them to add CI jobs that test V3, and propose a cutoff date.

The team is clear that V2 is not going away any time soon, so operators and
especially libraries developed outside of openstack that still depend on V2 can
continue to rely on it, and it will still be tested. It just won't be part of
the integrated gate.

We can help the deployment tools get in line, and in turn they will be huge
assets in helping cover backwards incompatible changes and in catching issues
in their CI.

Conventional Roles for Default Policy Files - Tuesday, 2:50
-----------------------------------------------------------

`https://etherpad.openstack.org/p/newton-default-policy-roles <https://etherpad.openstack.org/p/newton-default-policy-roles>`_

This session is a discussion of the `common-default-policy spec
<https://review.openstack.org/#/c/245629>`_. Deployers are already using very
similar policies in the policy.json file for various projects, and it is
difficult to carry those policies through upgrades. These common policies
should be put upstream in order to support the core 90% of what people are
already doing. This includes creating "observer" roles with read-only access
for auditing, and service-specific "admin" roles to limit privileges for
service users. It was proposed that instead of roles like "<service>_observer"
versus "observer" that the spec proposes, that the spec define hierarchical
roles like "end user observer" and "admin observer". The member role needs to
be actually defined (instead of implied) since "observer" would otherwise
technically be a member. There is a potential conflict between the "admin" role
described in the spec and the is_admin_project global admin implementation
described in `another spec
<https://specs.openstack.org/openstack/keystone-specs/specs/mitaka/is_admin_project.html>`_,
which may cause different interpretations of what "admin" means depending on
how keystone is configured.

Discovery - Tuesday, 3:40
-------------------------

`https://etherpad.openstack.org/p/newton-discovery <https://etherpad.openstack.org/p/newton-discovery>`_

Version discovery varies between projects, and it would be nice it all projects
did it the same way. More importantly, however, was the idea of capabilities
discovery. One way to do this is to provide a common endpoint, say / or
/capabilities, that can be hit with a REST call to discover capabilities. It
was argued that this has the potential to add an extra round-trip to for each
action, but really this would only need to happen once in a session - or even
once in a lifetime. If it turns out to be a thing that happens often, we could
mitigate the round-trip overhead by adding a record number to the header to
indicate a cached response, though this was thought to possibly wreak havoc
when used behind a proxy. Eventually it was decided that probably the
capabilites that we most care about are the one-time major decisions made by
large cloud providers around things like floating IPs, and that this was
probably a once in a lifetime need that could simply be provided by a
downloadable YAML file. We can look to shade, which attempts to abstract away
many of these one-time decisions, for what to include in such a YAML file. It
was noted that we must prioritize improving our documentation over making our
APIs programmatically discoverable - humans are more important than robots.

Insecure Messaging - Tuesday, 4:40
----------------------------------

`https://etherpad.openstack.org/p/newton-secure-messaging <https://etherpad.openstack.org/p/newton-secure-messaging>`_

We should not be able to tcpdump a stream and read message contents. Since
devstack is the reference implementation for all other deployments, TLS needs
to be the baseline there. The question then is, specifically related to
messaging, why is it not? It was suggested that TLS with rabbitmq is unduly
difficult to operate, but it was revealed that the rabbitmq documentation just
makes it look harder than it is. Additionally, if a hypervisor is compromised
it should not be able to manipulate other nodes on the message bus. We can
prevent this by fixing queue and topic names so that a regex can be used to
properly define ACLs.

Keystone New Features - Wednesday, 11:00
----------------------------------------

`https://etherpad.openstack.org/p/newton-keystone-new-features <https://etherpad.openstack.org/p/newton-keystone-new-features>`_

This session attempted to narrow down what new features will be considered for
the next release. The ldap3 driver, PCI-DSS, and shadow users for ldap were a
given. Evolving the service catalog was rejected, as were adding metadata to
domains and projects and multi-factor auth in later work sessions. API keys
were discussed, during which some suggestions for implementations were made,
such as just setting the token expiry for a long period, and using oauth.

Keystone Integration Wednesday, 11:50
-------------------------------------

`https://etherpad.openstack.org/p/newton-keystone-integration <https://etherpad.openstack.org/p/newton-keystone-integration>`_

This largely rehashed the Identity v3 in Devstack discussion from Tuesday.
Additionally, we discussed how the user agent in keystoneauth should be
handled. Originally there was a plan to have it look up the caller's version,
but this was too "magic" to be manageable. The current plan is to make the user
agent a required field so that the caller must pass it in themselves.

Keystone Clients and Libraries - Wednesday, 3:40
------------------------------------------------

`https://etherpad.openstack.org/p/newton-keystone-clients-and-libraries <https://etherpad.openstack.org/p/newton-keystone-clients-and-libraries>`_

We need to define some next steps for keystoneclient and keystoneauth. Sessions
in keystoneclient are already deprecated. We need to make sure that any new API
features, such as domain-specific roles and implied roles, are covered by the
clients, especially openstackclient. OTP needs to be implemented in
keystoneauth, but it should not do interactive prompting itself. Instead, it
should indicate to openstackclient that it ought to prompt, and maybe have a
default prompt string. OTP would not be enabled for automated things.

The S3 middleware will be removed from keystonemiddleware and moved into a
swift repo.

Infra Puppet/Ansible - Thursday, 9:50
-------------------------------------

`https://etherpad.openstack.org/p/newton-infra-robustify-ansible-puppet <https://etherpad.openstack.org/p/newton-infra-robustify-ansible-puppet>`_

Last summit we moved fully to a puppet-apply model which involves a sort of
Rube-Goldberg machine to connect hiera data, config application, logging, and
reporting together. This is largely working but there are many pain points.
Major bugs that taketop priority are, first, that ansible apparently deadlocks
and OOMs on the puppetmaster, and second, that puppetboard never reports
failures any more since failures cause the ansible run to fail entirely before
getting the chance to report. Less critical sticking points are that the
logging situation is not great: right now puppet logs locally to syslog, which
means that in the event of a node failure all evidence of the failure will be
stuck on the node. We'll fix this by also logging to stdout so that ansible can
pick it up and report it back to the puppetmaster. Additionally, the way node
grouping (for hiera data) is done, which is through a text file, is a little
strange and a native ansible solution would be preferable. However, this part
is actually working fairly well so changing how it works is not a priority.

Keystone Fernet Tokens - Thursday, 11:00
----------------------------------------

`https://etherpad.openstack.org/p/newton-keystone-work-session <https://etherpad.openstack.org/p/newton-keystone-work-session>`_

Should fernet be the default token backend, and how can we make it the default?
Making it the default has the potential to upset operator upgrades since an
additional step is required to set up fernet keys. The operators in the room
expressed that this was not really a problem, as no one simply upgrades
blindly, and deployment tools can help. Additionally we can add a safeguard to
make sure keystone fails to start if the keys aren't set up, as opposed to
breaking in strange ways when the user tries to get a token. A proposal to keep
UUID the default for a while and to rewrite it so that it uses the same
codepath as fernet was `floated <https://review.openstack.org/#/c/308063/>`_
but no one liked the idea of changing out the underlying implementation from
under people.

Keystone Metadata - Thursday, 11:00
-----------------------------------

`https://etherpad.openstack.org/p/newton-keystone-work-session <https://etherpad.openstack.org/p/newton-keystone-work-session>`_

Some operators want to add an API call to add extra metadata to projects and
domains. Since there is already an extras field for these things, they are
going to try using that and see if that meets their needs.

Keystone PCI-DSS - Thursday, 1:30
---------------------------------

`https://etherpad.openstack.org/p/newton-keystone-work-session <https://etherpad.openstack.org/p/newton-keystone-work-session>`_

The PCI spec has rules for password requirements which we should be able to
turn on for SQL users for PCI compliance. This would only apply to the SQL
backend, as other IdPs will implement this themselves if they care. It will
apply globally for now but we may be able to refine it to be domain specific in
the future. We'll call the config section something like "compliance" or
"hardening" so that a superset of HIPAA and PCI rules can be opted-into. The
password expiry will be tricky, since an expired password means the user can't
get a token. We can work around this by letting the user getting an unscoped
token and then only allowing the change password action with that token.

Keystone Multi-Factor Authentication - Thursday, 2:20
-----------------------------------------------------

`https://etherpad.openstack.org/p/newton-keystone-work-session <https://etherpad.openstack.org/p/newton-keystone-work-session>`_

The tangential discussion that quickly arose here was the age-old question of
whether keystone should really be an IdP, as opposed to forcing the user to
deploy an external IdP. Since it is possible to deploy an external IdP that can
handle MFA, it was decided to defer implementing MFA in the SQL backend of
keystone.
