:title: OpenStack Project Team Gathering: Denver
:slug: denver-ptg
:sortorder: 30
:date: 2017-09-22 05:00

This was my first PTG, and I was lucky to be able to participate and record the
discussions I participated in. My focus this week was primarily on keystone,
but I've also recorded here my involvement in other groups.

Two major themes emerged in keystone land this week. The first was policy,
which has improved leaps and bounds with the new ability to define policy in
code rather than JSON files but still suffers from the omnipresent admin-ness
bug. The second was microversions, which keystone has so far been the stick in
the mud on adoption but always looms ahead.

Policy
======

Policy in Code
--------------

`Etherpad <https://etherpad.openstack.org/p/policy-queens-ptg>`__

The keystone team started the week by opening up a room to the rest of the
OpenStack projects to discuss the `Policy in Code cross-project
goal <https://governance.openstack.org/tc/goals/queens/policy-in-code.html>`_,
which would have all projects move from defining default policies in a JSON
file on disk to registering them in code, emulating the way configuration
defaults are currently implemented. This has a number of huge benefits that are
outlined in the TC goal. Some questions that arose in the room include:

**What are the basic steps to accomplish this in my project?** Basically, the
project should enable a common module to own all of the policies for that
project. Within that module you can chunk things up per API. Maintain test
coverage through normal unit tests. If your policies are currently
under-tested, it would be a good idea to implement unit tests prior to
initiating this refactor. You can look at the work that keystone and nova has
already completed as examples.

**Are we collecting a pool of people to work on this goal for other projects?**
Like a lot of projects these days, the keystone team is understaffed and does
not have the resources to work on this goal for other projects, though Lance
(the keystone PTL) has already started helping glance.

**Can the system coexist with both the old way and the new way?** Yes, this can
be implemented incrementally.

**Is the recommendation as part of moving policies into code to also add
documentation?** Yes, this is part of the community goal. One of the primary
benefits we get from this is allowing the operator be be able to read policy
documentation and understand what they need to change without having to read
internal code. Additionally, the overridden policies can use a YAML format
instead of just JSON, so comments in the config file are welcome.

The trove team voiced concerns over the difficulty it is likely to encounter in
implementing this goal, which is likely shared by other projects. Trove has
APIs that are not well-documented, so seeking out the policies it needs to move
into code will be a challenge. Also, trove in some cases generates policies on
the fly with dynamic names because some of its APIs have URLs whose paths
depend on the database in use. Trove will work on first getting the policy
definitions for the base APIs refactored and will address the driver APIs
later. It is also possible that `the trove project may be rewritten from
scratch
<http://lists.openstack.org/pipermail/openstack-dev/2017-June/118537.html>`_,
so the replacement project will have a chance to do policy-in-code from the
beginning.

Both trove and glance, like nova, have some policies that depend on the JSON
payload in the body of a request and not just the URL path. This initiated
questions about the path property of the DocumentedRuleDefault object and how to
handle this when some APIs use the same path for different actions. This path
property is really just for documentation, it does not have affect the
enforcement of the policy. Nova solved the problem by simply making the path
component of the documented policy rule include a parenthetical description of
the action that the policy rule was guarding, so trove and glance can use this
as an example. It is worth noting that even with the complexity of the nova API
and its policies, nova did not have to change any APIs in order to make this
work.

The glance team had questions on what to do with their property protections
implementation. This is implemented as a separate policy file from the main
policy configuration. However, no default file is needed, and only defaults are
overridden in this policy file, so they can easily keep this as-is for now.

The group asked about the current recommendations for deprecating policies.
While the policy-in-code work will definitely facilitate policy deprecations,
the oslo.policy library does not currently have a deprecation mechanism. Nova
has hooked in some warnings with a wrapper method around the oslo.policy
methods to accomplish this for now. The discussion evolved into a philosophical
discussion around the meaning of deprecation - in some cases we don't really
want to deprecate a named policy, but we want to change the semantic meaning of
a policy, in which case we would like to warn users of the upcoming change. In
other cases we want to do a more standard deprecation in which we remove a
rule, for example when the API it protects no longer exists or is going away.

Role Check in Middleware
------------------------

`Etherpad <https://etherpad.openstack.org/p/queens-ptg-keystone-rbac-in-middleware>`__

`Spec <http://specs.openstack.org/openstack/keystone-specs/specs/keystone/ongoing/role-check-from-middleware.html>`_

The goal behind this proposal was to make modifying policies and introducing
custom roles easier by consolidating policy definitions in the keystone server
instead of within the individual services, with the role check performed by
keystonemiddleware as part of the pipeline in the service's web server. Rules
would be defined by the verb and path in the incoming request and roles would
map to those rules.

There was a lot of uneasiness about this plan because several APIs don't have
distinct policy rules for the verb and path of a request, they differentiate by
properties within the request body, which this spec didn't specifically address
and which was being treated as an afterthought. An idea was brought up to move
this into oslo.policy rather than keystonemiddleware so that the individual
services had more control over it, but this would mean involving other projects
in the solution rather than fixing it for them in a project controlled by the
keystone team. Even with that, keystone still has to be aware of policies for
other services, which lead us to the "capabilities" problem - when a user asks
"what can I do?", they can mean both "what do I have permission to do?" and
"what features are enabled on this cloud?". Keystone can only ever answer the
first question, which if exposed to users could lead to misinformation about
what a user is "capable" of doing.

Another use case the spec hopes to address was how to help users who try to
perform an action and fail due to insufficient privileges. The spec allows them
to ask for the roles needed to perform a given action. However, the room agreed
that exposing this information is a security hazard since it communicates
information that an attacker can use to focus their attacks.

The result of the discussion was that Policy in Code already solves a lot of
the problems that this idea sought to solve - hardship of policy changes,
upgrades, and custom roles. Moreover, storing policies in keystone will make
rolling upgrades harder because in some cases you might have different policies
on different nodes while they are at different stages of the upgrade. We ended
up deciding that this spec should be removed from the backlog.

Bug 968696
----------

`BM/VM Etherpad <https://etherpad.openstack.org/p/queens-PTG-vmbm>`__

`Keystone Etherpad <https://etherpad.openstack.org/p/queens-ptg-policy-notes>`__

The rest of the policy discussions, which occurred both in the RBAC and Policy
session of the BM/VM Working Group room as well as in multiple sessions in the
keystone room, focused on `the infamous admin-ness
problem <https://bugs.launchpad.net/keystone/+bug/968696>`_, where with standard
policy files, a role of "admin" on any project effectively grants users "admin"
powers on any project. We had a number of revelations this week and converged
toward an actual roadmap to fix this problem.

Policy discussions are always difficult to grasp as they deal in very abstract
concepts. I captured some of the high-level themes of the discussions here, but
for more details you can `check out Lance's
recap <https://www.lbragstad.com/blog/keystone-queens-ptg-summary>`_.

There are two ideas that have been put forth to solve this problem. The first
is to create a special project, an "admin" project, on which admin users have
an admin role and to which the user must scope in order to perform admin-level
actions such as live migration. The second is to create a new type of scope,
the "global" scope, and allow users to have roles on that scope. The
admin-project idea is already mostly implemented, but most of the team agrees
that it feels like a hack that overloads the already-overloaded project
concept. The new global scope idea makes more sense semantically but would
require a rewrite of already completed work. We also initially had concerns
that the new scope would require changes in the clients, which as we learned
from the v3 overhaul would be a difficult undertaking. We agreed that since the
admin-project is essentially already out in the wild, we need to come up with a
migration plan from it to the global-scope plan.

It quickly became clear that neither "admin" nor "global" actually accurately
describe what we're talking about, and indeed we found that we had been talking
circles around each other for much of the week due to different assumptions
about what we actually want to accomplish. There are a few use cases that we
want to enable, which can be captured with a few examples:

**List Hypervisors:** This is an operation that has nothing whatsoever to do with
projects. This is effectively a `system` level operation.

**Create image:** Images can be `public` or `private`, so uploading images can
either be a `system` level operation or a `project` level operation.

**Live Migrate:** Live migration of servers involves both knowledge of
hypervisors as well as knowledge of individual servers, so this is *both* a
`system` operation and a `project` operation.

**Create server:** Servers exist solely within a project and so this is just a
`project` level operation.

**List all servers:** An admin who wants to list all of the servers in all
projects on all hypervisors is doing a `project` level operation on `all`
projects. They could accomplish this by looping over all projects or by
ensuring all projects inherit from a top-level parent project on which the
admin has a role.

From this emerged the `system` keyword which we started using instead of either
`admin`, which has the effect of denoting privilege when we might really just
mean read-only access, or `global`, which was being conflated with all-project
actions such as "list all servers in all projects".

The is_admin_project implementation did not make the distinction between
system-level actions and all-project actions, such as listing all servers in
all projects. Once we realized we had been conflating the two scopes we
decided that we did not want that to continue, as these are fundamentally
different operations, so the migration path will have to take that into
consideration.

In thinking about how to implement this from a client perspective we started
wondering whether we might want to introduce new types of scopes beyond the
"system" scope, which lead to an interesting discussion on whether there could
be such a thing as a "service" scope, for example a scope for just nova
operations. Some of the room thought this was sensible while others in the room
believed this would fall into the category of a role, not a scope, since an
entity that can only perform nova operations would be said to only have
permissions to execute nova actions, which is defined by policy rules for a
named role. In any case, a "region" scope seemed like a real possibility and so
we need to make sure that this is written with extensibility in mind.

Policy Roadmap
--------------

We were able to solidify a promising path forward, which in itself is a huge
accomplishment. The path is described in detail in `this
etherpad <https://etherpad.openstack.org/p/queens-PTG-keystone-policy-roadmap>`_.

Microversions
=============

`Spec <https://specs.openstack.org/openstack/api-wg/guidelines/microversion_specification.html>`__

Keystone has been lagging behind other OpenStack projects on implementing
microversioning. A few cycles ago we were hard against the idea entirely, but
with other projects implementing it, it starts to become appealing mainly for
the sake of consistency. Besides this, the main benefit we could get from it is
in inter-cloud interactions, where if we request an unsupported microversion,
we get a clear and obvious 404 instead of what could be an unclear error
related to invalid usage somewhere down the line.

The team is concerned about the hardship for clients. Currently the
project-specific python libraries support microversions only as an environment
variable that the user must set, pushing responsibility for understanding
microversions to the user. Even shade does not yet do this smartly. The horizon
team was in the room and expressed how hard supporting microversions has been
for them. And clients without a voice at the PTG - every SDK written outside of
the OpenStack ecosystem - will have to somehow deal with this.

We didn't come up with a yay/nay decision on microversions, but we did decide
to try to come up with a list of things we could fix if we implemented
microversions that we are currently constrained from due to
backwards-compatibility restrictions. My personal view here is that even if we
come up with a list of fixes that would make our API perfect, we can't prevent
users from using the old APIs nor can we clean up the code and database columns
that implement the old APIs, so we are left with forks in our code paths that
hinder maintainability.

Keystone - In Other News
========================

Other discussions this week had interesting outcomes which are worth noting.

BM/VM Working Group: Application Credentials
---------------------------------------------

`BM/VM Etherpad <https://etherpad.openstack.org/p/queens-PTG-vmbm>`_

`Concerns Thread <http://lists.openstack.org/pipermail/openstack-dev/2017-July/119802.html>`_

`Spec <http://specs.openstack.org/openstack/keystone-specs/specs/keystone/pike/application-credentials.html>`__

`Summary <http://lists.openstack.org/pipermail/openstack-dev/2017-September/122087.html>`_

This was a cross-project session on Tuesday that primarily involved the
keystone, nova, and heat teams. Application Credentials (originally coined API
keys) are a proposed feature in keystone conceived of at the Atlanta PTG and
Boston Summit to solve a number of problems surrounding the usage of automated
applications and service-to-service communication in OpenStack. The main
question we wanted to address in this session was about the life cycle of such
a credential. In the original conception, this resource was scoped to a
project, not a user. The idea behind this was that if a team needs to run an
application, but the team member who creates the credentials is deleted from
the project, the application should live on. At the last minute of the spec
review, the keystone team decided that this would provide users with the
ability to grant themselves access beyond the lifetime of their own user,
inviting the potential to abuse the feature. This, however, prohibited a major
use case of the application credential idea.

On this contentious question, we re-landed in the same place we found ourselves
in when the spec originally landed, which is that in order to prevent abuse,
the credential must become invalid when its creating user is deleted. We could
potentially revisit ways to automatically rotate the key or transfer ownership
at a later date, but in the immediate case, the ability to stop putting
passwords into config files - especially passwords for LDAP or federated users,
which when compromised would grant an attacker access to much more than an
OpenStack cloud, or for users who want to use 2-factor auth for their general
access but which is quite hard to use in automation - is a massive win and more
than enough to justify this feature.

Once the lifecycle question was addressed, we circled around to access control.
There are two different types of access control that we would like to be
grantable to an application credential. One is managed by traditional keystone
roles, and the other would map to REST calls. A question that was brought up
was that given the currently sad state of default roles in keystone, should we
start working on the REST-based access control management first? It was quickly
realized that this could not really work, as an application credential must
behave in nearly all respects the same as a user, and circumventing the role
model could lead to a user creating an application credential with more powers
than the user is allowed by their current roles. We decided that initially this
would work in a mostly non-user-configurable way: the application credential
just receives the role on the project that the creating user is scoped to at
creation time. This fits nicely when we ask what happens when "global" or
"system" roles become a reality, as we can still say that an application
credential receives the scope it was created under, no matter what that is.
Eventually, when roles become more meaningful, we can add the ability for a
user to delegate any of their assigned roles on a given project to the new
application credential.

When we do start addressing the REST-endpoint model of access control, we start
having some deja-vu from the questions we have been asking around policy. For
example, what do we do about the actions API in nova, for which we may want to
impose different restrictions based on the request body? The answer is simply
that we're not going to solve it for the application credential case (unrelated
to the solution for the policy case). This is a new feature and so there are no
expectations or contracts on how it works that we need to meet. Relatedly, what
happens on, for example, a server boot request, which at the front end is just
a nova request but in reality involves multiple services? Must we define access
control for each internal service request involved in the creation of a nova
server - even though the end user who creates this credential might not be
aware of all these internal interactions? The answer here is that, much unlike
our current policy handling, the access control is only going to be defined at
the user entry point, e.g. POST /servers, and therefor implicitly allows such
things as GET /images. The reason this will work without being massively
insecure is that we have already laid the groundwork for `service tokens
<https://specs.openstack.org/openstack/keystone-specs/specs/keystonemiddleware/implemented/service-tokens.html>`_,
creating a trust association between services, and so we can expand on that to
allow application credentials to complete such complex operations securely
without defining at a low level their allowed actions.

Finally, another use case came up that we had not considered before and that
will require another change to the current spec. Heat needs to be able to
create application credentials for the nova servers it creates so that those
servers can make API calls. This is specifically disallowed in the current
version of the spec on the grounds that a compromised credential could
maliciously spawn additional credentials. The means by which it is disallowed
is not mentioned in the spec, and it was brought up that however it is
disallowed, the credential could create a normal user token and then use that
to circumvent the rules. Rather than leaving this open for abuse, we need to
manage heat's use case in a secure way. The spec will need to clarify that
these limitations should be imposed on the token itself by annotating the
tokens when they are created by an application credential, and then adding a
policy mechanism to specifically allow heat or a specific user or role to
create an application credential.

Deprecations and Removals
-------------------------

`Etherpad <https://etherpad.openstack.org/p/queens-ptg-keystone-deprecations>`__

A patch series to almost entirely rip out the Identity v2.0 API was approved
early in the week, while patches to remove the remaining bits, e.g. the auth
path and the EC2 path, are under discussion. These have already been deprecated
along with the rest of the v2.0 APIs, but a time to removal was never given and
so it was unclear whether it was reasonable to remove them at the same time.
The plan is to ask the TC for approval to remove the auth API outside of the
normal deprecation guidelines since its implementation is insecure in its
nature.

We discussed our current token engines, which currently only includes the uuid
and fernet providers, though remnants of support for the PKI(z) providers
remain, especially in keystonemiddleware. We would like to deprecate the uuid
token format as well as the sql token backend on which it depends for
persistency, as the non-persistent token format is practically universally the
preferable option, and moreover the uuid and fernet engines have radically
different code paths, and as such maintaining both is difficult. However, we do
have concerns about the fernet backend. The fernet primitive in the python
cryptography library is essentially unmaintained, which we realized when trying
to propose changes to it to fix its non-sub-second-precision problem. Since we
adopted the fernet backend in keystone, JSON Web Tokens, an encrypted token
model based on an `IETF standard <https://tools.ietf.org/html/rfc7519>`_, has
come into widespread use, and it would be a perfect fit in keystone. Before
kicking out uuid, it would be nice to provide users with another option in case
some sort of issue is discovered in the largely unmaintained and unaudited
fernet implementation. Since JWT is another type of non-persistent token very
similar to fernet, the provider implementation could leverage much of the work
done in the fernet provider and would therefore be less of a maintainability
nightmare. To that end we've set a goal to write a spec for JWT and revisit
removing uuid later.

We would also like to deprecate and remove the template catalog backend, which
since the addition of the v3 API has been completely broken. However the
proposed replacement needs a lot of work and someone will need to step up to
take it on.

Finally, we want to remove the session module from keystoneclient in favor of
the equivalent module in keystoneauth. We still need to chase down a few
libraries that are still using keystoneclient for auth sessions, although
thankfully most of those cases are just in documentation.

Mission Statement and Long-term Vision
--------------------------------------

`Etherpad <https://etherpad.openstack.org/p/queens-ptg-keystone-mission-statement>`__

We set aside time to discuss whether we wanted to define a mission statement
for the keystone team. While there is no impetus for such a statement at the
moment, having one can supposedly come in useful when you least expect it. We
brainstormed some ideas but no actions came out of this discussion. Some of the
ideas had to do with moving keystone away from the identity management space,
instead preferring to simply use federated identity backends for everything and
then focusing on acting as an authorization service as opposed to an
authentication service. Other ideas had to do with lessons learned over the
years: support existing standards instead of rolling our own, and move toward
making defaults production ready as opposed to optimizing for the
proof-of-concept case.

VMT Coverage
------------

`Etherpad <https://etherpad.openstack.org/p/queens-ptg-keystone-vmt>`__

In earlier cycles we coordinated with the security team to start getting all of
our libraries tracked by the Vulnerability Management Team (VMT). Currently,
only `keystone server and python-keystoneclient are under such management
<https://governance.openstack.org/tc/reference/tags/vulnerability_managed.html>`_.
We started the process of getting keystonemiddleware in this group by `drafting
an architecture diagram to undergo security analysis
<https://review.openstack.org/#/c/447139/>`_. Since then the security team
suffered from resource cutbacks this year and the analysis has stalled,
but in this session we decided to start the same process for our other
libraries (keystoneauth, pycadf, oslo.policy, etc) in the hopes that the
security team will soon have the bandwidth to complete this analysis and add
these libraries to their vulnerability tracking.

Libraries
---------

`Etherpad <https://etherpad.openstack.org/p/queens-ptg-keystone-libraries>`__

We didn't have a clear agenda for this topic but instead opened up the room to
general ideas for improvements to our various libraries - keystonemiddleware,
keystoneauth, oslo.policy, pycadf, and python-keystoneclient. Most of our
attention went to keystonemiddleware. Improvements we'd like to make on
keystonemiddleware include moving to oslo.cache instead of our home-rolled
caching, removing leftover PKI bits, removing S3token stuff, and renaming the
confusing auth_uri parameter. Most of this is straightforward, though there was
a question on the effects of removing PKI support from keystonemiddleware. Even
though keystone itself no longer supports PKI/PKIz tokens, it's possible that
someone is using a custom token backend and relying on the PKI code in
keystonemiddleware. We will have to ensure we have proper warnings during the
deprecation period so that people relying on this functionality have sufficient
time to move this logic into their custom backends.

Docs cleanup
------------

`Etherpad <https://etherpad.openstack.org/p/queens-ptg-keystone-doc-cleanup>`__

In the last cycle we made tremendous improvements to our docs with the help of
our Outreachy intern. We would like to build on that momentum and have a number
of ideas for improvements:

- Consolidate redundant articles in our admin and operator guides.
- Make sure that keystone-related articles on wiki.openstack.org are audited
  and either moved to docs.openstack.org if they are still relevant, or removed
  entirely so that they aren't contradicting the docs that are under active
  maintenance.
- Clean up the api-ref. The way it is currently generated from variables stored
  separately from the formatting makes it easy to make mistakes when it is
  edited. We plan to implement a consistent naming scheme for these variables
  that will be of the form
  {request|response}_{attribute}_{location}_{required|not_required} where
  attribute is something like group_id or user_object, and location is the
  place where the property is defined such as the body, the URL path, or the
  query parameters.
- We're inconsistent about how we document error responses: sometimes they are
  documented and sometimes we assume the reader will assume normal error
  responses. We need to make sure they are always documented, because there are
  sometimes cases where we generate error responses that are inconsistent with
  the standardized definitions, so it is best to eliminate any doubt and always
  document.
- Nova has something called an "API guide" that sits alongside their API
  reference that explains in plain prose all the concepts in the API. This type
  of document would be common to all audiences and couldn't be boxed into the
  current contributor/admin/operator/user guides. We'd like to implement
  something similar.

Testing
-------

`Etherpad <https://etherpad.openstack.org/p/queens-ptg-keystone-testing>`__

We would like to make a number of improvements to our testing suites:

- Our unit tests make use of inheritance, which is intended to help with
  reusability but has the effect of running many of our tests multiple times
  unnecessarily. We need to clean this up.
- Federation is only tested with testshib.org, which is not ideal because it
  relies on an external service which can cause irrelevant job failures in the
  event of flaky networks. We're working on setting up an internal identity
  provider for this job.

Federation
----------

`Etherpad <https://etherpad.openstack.org/p/queens-ptg-keystone-federation>`__

We didn't spend a lot of time on this topic because we do not have a lot of
champions stepping up to make federation better, but we did discuss a few
topics.

We would like to support `native SAML
<http://specs.openstack.org/openstack/keystone-specs/specs/keystone/backlog/native-saml.html>`_.
This would benefit clouds supporting domain admins, especially public clouds,
since it would allow for domain admins to configure their own federated
authentication providers without changing the underlying Apache configuration.
We unfortunately don't currently have anyone stepping up to implement this.

The keystone team met with the heat team to talk about a possible flaw with
Trusts assigned to Federated Users, where their experience with it was that it
just `blows up <https://bugs.launchpad.net/keystone/+bug/1589993>`_ because of
the lack of a real user in keystone. We think, however, that perhaps this
predated shadow users, and the action item out of this was to write a tempest
test to create a trust for a shadow user and see if this is really broken.

We also brought up `extending the user API with federated attributes
<http://specs.openstack.org/openstack/keystone-specs/specs/keystone/backlog/support-federated-attr.html>`_,
which would allow us to perform actions such as role assignments on federated
users before they have logged in. Similar functionality already exists with
auto-provisioning through the `mapping API
<https://docs.openstack.org/keystone/latest/advanced-topics/federation/federated_identity.html#mapping-combinations>`_
but this would allow us to deal with users without having to create mappings
based on any federated attributes.

Roadmap
-------

We created a `trello board <https://trello.com/b/5F0h9Hoe/keystone>`_ to
document our roadmap for this current cycle and cycles beyond.

And The Rest
============

I spent some time in other rooms this week.

Infrastructure: Puppet and Testing
----------------------------------

`Etherpad <https://etherpad.openstack.org/p/queens-infra-puppet-functional-testing>`__

Since I was a key contributor to the Infra team's puppet infrastructure in the
past, I proposed and participated in a discussion about the future of
functional testing of the puppet modules that the Infra team maintains. A year
or two ago we added functional tests to Infra's puppet modules using
`beaker-rspec <https://github.com/puppetlabs/beaker-rspec>`_ as the underlying
testing framework. At the time, beaker-rspec was the standard way to do
functional testing of puppet modules and the hope was that using it would spur
contributions from experienced puppet developers as well as facilitate
cooperation between the Infra team and the Puppet-OpenStack team which also
uses beaker-rspec for functional testing. While it has on occasion been useful
to coordinate with the Puppet-OpenStack team in this area, it has not inspired
other puppet developers to contribute to Infra modules, and in fact the
requirement to use Ruby here has dissuaded existing Infra contributors from
making improvements to the test suites.

We came up with a plan to utilize the existing (though still Work in Progress)
ZuulV3 setup to run puppet module tests with ansible. We will experiment with
the puppet-gerrit module and use `the AFS mirror tests
<https://review.openstack.org/#/c/500627/>`_ as a guide to come up with a basic
test provisioner and assertion validator for the puppet modules. This
will benefit us because we no longer have to hack around beaker-rspec's need to
control node provisioning, and if we eventually decide to rewrite these modules
in something other than puppet (like ansible), we can still use the tests to
validate behavior.

API-SIG: Capabilities
---------------------

`Etherpad <https://etherpad.openstack.org/p/api-ptg-queens>`__

`Spec <https://review.openstack.org/#/c/459869/>`__

I stopped by the API-SIG's room while they were discussing what sort of
guidance the SIG should provide to the projects on how to implement a
"Capabilities" document. The point made in the room was that just writing down
capabilities somehow is leaps and bounds forward, so specific guidance on the
format in which it is exposed in a queryable way is not really necessary. This
was countered from a client perspective, with the argument that projects were
not likely to think too hard about consumeability, for example in regards to
cacheability, and were likely to screw the clients if not given specific
guidance. Clients such as openstackclient or shade care about this capabilities
API not just because a user might specifically ask but because they will want
to change behavior depending on the capabilities of the cloud it is connected
to, for example by showing different help messages or by handling assignment of
IP addresses differently. It was decided that the SIG should reach out to
operators and users to figure out how strongly desired such an API even is to
the wider community before recommending this become widely adopted.
