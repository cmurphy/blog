:title: Denver III: Revenge of the Snowpenstack
:slug: denver-forum-ptg-2019
:sortorder: 30
:date: 2019-05-10 17:00

.. image:: {static}/images/team.jpg

YET AGAIN we returned to Denver, the city that brings snow and trains together.
This time we were here not just for the Project Teams Gathering but also for the
OpenStack Summit and Forum. Although the time allotment for all the activity
this week was very compacted and our brains were fried before the PTG even
started, the keystone team made good progress on several topics.

`Forum Etherpad <https://etherpad.openstack.org/p/DEN-keystone-forum-sessions>`__

`PTG Etherpad <https://etherpad.openstack.org/p/keystone-train-ptg>`__

This recap will cover topics from both the Forum and the PTG, since many topics
were touched on first at the Forum and then followed up upon during the PTG.

Application Credentials
=======================

`Forum Etherpad <https://etherpad.openstack.org/p/DEN-keystone-forum-sessions-app-creds>`__

`PTG Etherpad <https://etherpad.openstack.org/p/keystone-train-ptg-application-credentials>`__

We opened the Forum with a session on the next steps for `application
credentials`_, requesting broader input from the community before diving into
the development details as a team at the PTG.

Access Rules
------------

The first topic was the nearly-completed `access rules`_ (formerly
"capabilities", formerly "white lists") feature for application credentials. The
"Access Rules Config" (formerly "Permissible Path Templates") construct, which
was a major point of contention during the initial draft of the spec, came as an
unpleasant surprise to attendees at the Forum session, as it reduces the
self-service nature of the feature, creates interoperability issues, and is
partially redundant with policies. Curating a list of permitted access rules
would also be impossible for the keystone team to do, since the number of APIs
within OpenStack is unbounded and since keystone could potentially be used
outside of an OpenStack ecosystem. As a team, we agreed to update the spec to
defer this feature in this form, but to modify the data model of access rules to
become individual objects in the database that can be queried and linked to
application credentials after their initial creation, which will help with
re-discovering an access rule after an application credential is deleted without
needing to resort to reading documentation.

Regarding "Chained API Calls", in which e.g. ``POST /v2.1/servers`` requires
additional API calls to other services from the nova user on behalf of the end
user, we agreed that without a discovery model that allows users to find out the
chain of requests that is initiated by the first request, requiring users to add
rules to the app cred for every background API request poses a usability
constraint on the user, so this is also deferred until we see a specific need
for it in the field and have decided on some automatable way to discover the API
call trace needed to create this chain in the access rule.

Regarding the `role check on body key`_ optimization, which is meant to address
the ``actions`` APIs in nova and cinder which need different restrictions based
on the action, we're concerned about special-casing this unique API which the
teams involved may end up fixing anyway, so we agreed to let the access rules
feature bake for a while before investigating the need for it again.

We also discussed adding support for a microversion range to the access rules,
to address a potential case where the behavior of a method/path combination
changes between microversions and needs to be restricted. Again, we will get the
access rules feature merged and socialized for a while and allow some time to
discuss the idea with the other services.

.. _application credentials: https://docs.openstack.org/keystone/latest/user/application_credentials.html
.. _access rules: http://specs.openstack.org/openstack/keystone-specs/specs/keystone/stein/capabilities-app-creds.html
.. _role check on body key: https://review.opendev.org/456974

Renewable Application Credentials
---------------------------------

We introduced the idea of `renewable application credentials`_ at the Forum,
which is meant to address the issue that federated users who have role
assignments only via mapped group membership currently cannot use application
credentials since group membership is ephemeral, and if the role assignments
on the application credential were made permanent in the database it could fall
out of sync with the identity provider and open a vulnerability in which the
application credential could be used after the user is deleted from the backing
identity provider. The Forum attendees pointed out that this seemed like a
band-aid over the real issue, which is that the shadow user implementation
itself fails to account for deleted or modified users in the identity provider
backend, and that pushing the fix into application credentials does nothing to
address the core issue. We agreed during the PTG to push this TTL feature up to
the user object, so that a user becomes disabled if they are not logged in for a
while and application credentials cannot be used when the owner is disabled.

.. _renewable application credentials: https://review.opendev.org/#/c/604201/7

Automating Ownership
--------------------

Operators and heat developers are unhappy with the amount of manual steps needed
to maintain an application credential, from the above need to manually refresh
the application credential (or user) to the long-debated inability to transfer
or share ownership of an application credential. This came up in both the
application credentials Forum session as well as the operator feedback session.
During the PTG session, we discussed a potential way to implement this highly
requested feature via something like "group app creds".  Implementing this would
a fundamental change in keystone's core structure, but it could be accomplished
if we moved to having a kind of inheritable "principal" model. We're not
anywhere close to that yet, so we plan to continue to advocate for and document
the proactive rotation approach to dealing with application credential ownership
changes.

Operator Feedback
=================

`Forum Etherpad <https://etherpad.openstack.org/p/DEN-keystone-forum-sessions-operator-feedback>`__

We had our usual catch-all operator feedback session in which we had the
chance to speak directly with keystone operators about how they use keystone.
The recurring hardship around defining a new role is still the top issue. The
introduction of an OpenStack-wide read-only default role will help, but
operators also want something like a project-manager role by default. This
should already exist in Stein in the form of the admin role on the domain scope,
and is also something that Adjutant handles. Many operators have independently
implemented their own tools and scripts similar to Adjutant to help with
managing keystone. The ability to delete project resources (discussed in another
Forum session) and the ability to manage quota limits in keystone will help
reduce the need for independent scripts.

We talked about multi-region/site deployments and about keystone federation.
Some operators simply run one keystone that is shared to multiple regions.
Others run completely independent keystones. The ideal case is to run federated
or synchronized keystones across sites. Predictable or settable project and user
IDs are explicitly requested to help make this type of deployment easier. We
also got positive support for the `Native SAML`_ backlog spec, which would help
operators to avoid relying on Apache for service provider configuration and
allow them to delegate service provider configuration to domain administrators.
It was also brought up that the SAML specification can allow for a callback that
would help with automatically deleting shadow users when they are removed from
the IdP backend, which is worth investigating but may not be universally
implemented by all IdPs.

An interesting idea that was requested was to implement a keystone-only or
keystone-and-swift-only dashboard to avoid the need for horizon. It sounds like
it is difficult to decouple horizon from nova and so operators who use keystone
just for swift authentication or for other non-OpenStack services have
difficulty using horizon as the graphical UI for keystone. A dashboard like this
should be relatively easy to implement now that we have replaced our controller
and routing code with Flask. We have also already discussed adding some HTML
support which would be necessary to implement SAML2.0 WebSSO.

.. _Native SAML: http://specs.openstack.org/openstack/keystone-specs/specs/keystone/backlog/native-saml.html

Edge and Federation
===================

`PTG Etherpad <https://etherpad.openstack.org/p/keystone-train-ptg-federation>`__

Edge computing continues to be a major topic in OpenStack. Although in theory
autonomous identity servers, connected by federation and utilizing local
application credentials for persistence, is a workable architecture for most
Edge "MVP" models, we've failed to promote this architecture and still face the
perception that keystone doesn't work for Edge and must either be changed or
worked around, for instance using some kind of external broker as discussed in
`this presentation on "localization"`_.

Predictable and Settable IDs
----------------------------

The concrete ask that keystone definitely does not address yet is for
predictable or settable user and project IDs, which are needed to address issues
of resource ownership for glance, swift, and possibly other services across
autonomous sites. We have long rejected proposals to allow explicitly setting
project IDs due to the threat of ID squatting and because it removes keystone's
ability to control the unique ID, and in most cases operators don't want to have
to come up with their own ID generation mechanism anyway. We would like to solve
this problem by using IDs that are generated in a predictable way based on the
name and domain name of the resource, but this doesn't solve the issue for older
deployments.

We will still move forward with predictable IDs, although making this work for
projects is tricky because names are mutable. One idea was to use a user-set
secondary identifier as a kind of salt for the ID generator. Demand is also high
enough at this point for settable IDs that there is probably no way around
implementing this as well.

X.509
-----

We also want to address X.509 authentication as a first-class federated
authentication method to help support PKI-based identity providers like Verizon
Media's (Oath's) Athenz. Verizon Media uses this as an Edge implementation but
in their case they can tolerate network partitions, so supporting X.509
authentication is not really about supporting Edge but simply providing better
federation coverage. In theory this should already work out of the box, but we
need better CI and documentation for it.

.. _this presentation on "localization": https://www.openstack.org/summit/denver-2019/summit-schedule/events/23352/implementing-localization-into-openstack-cli-for-a-free-collaboration-of-edge-openstack-clouds

Policy
======

`Forum Etherpad <https://etherpad.openstack.org/p/DEN-granular-policy-and-default-roles>`_

`Keystone/Tempest Etherpad <https://etherpad.openstack.org/p/keystone-train-ptg-testing-system-scope-in-tempest>`_

`QA Etherpad <https://etherpad.openstack.org/p/qa-train-ptg>`_

`Keystone Etherpad <https://etherpad.openstack.org/p/keystone-train-ptg-scope-and-rbac>`_

`Keystone/Nova Etherpad <https://etherpad.openstack.org/p/ptg-train-xproj-nova-keystone>`_

As system scope and the reader role come closer to becoming a reality, we're
starting to work with other teams to fully flesh out what these changes mean for
OpenStack.

First of all, we need it to be tested. Keystone currently has hundreds of
in-tree unit tests for policies, but we also need to work with the QA team on
integration tests. Tempest will need new client personas, starting with system
admin and project member, which would be essentially the same as the admin and
non-admin personas tempest has now, and gradually add other personas like domain
admin or system reader. Tempest itself does not need to provide 100% coverage
for all nine default personas (system/domain/project admin/member/reader) as
this could be covered by Patrole, but it does need to test some of the different
behaviors that occur with different scopes and roles, such as filtered lists.
For backwards compatibility, tempest's system admin persona will redirect to the
old admin persona if the enforce_scope feature flag in tempest is toggled off.

Second, the nova team is working with us to be our policy guinea pigs and has
created a `spec for their policy overhaul`_. They will be working to remove the
hard-coded ``is_admin`` database check in code and move toward using policy to
check for the admin role and system scope. At the Forum, operators acknowledged
that using the system scope would be a major change, but for the main example of
live migration this is usually limited to operator-ish users already and so the
number of users who would need to be re-trained is limited. At the PTG, we also
discussed what default policies the nova project should provide, and advised
that for some semi-special cases like wanting read-only plus live-migration,
policy adjustments could be addressed in documentation rather than changing the
defaults provided by nova.

For the keystone team, we need to wrap up our own policy overhaul. Along with
that, we'd like to improve our in-tree testing, minimally by speeding up test
setup time by using ``setUpClass`` but ideally by refactoring it into a
generalized testing framework or pattern.

We also have been considering addressing the need for global admins to do
project-specific operations, which system scope currently would not allow: an
admin would have to use system scope grant to themselves a role assignment on a
project and then get another project-scoped token to do an operation within the
project. An alternative is to use the currently unexposed root domain with
inherited roles to allow admin users to inherit a role assignments on any
project. The admin would still need a project-scoped token but would not need to
do a dance around granting and revoking their role assignment on the project.
This would not be the same as impersonating another user, but it may also be
useful to have some way of getting a "view" of another user and assuming their
role assignments.

.. _spec for their policy overhaul: https://review.opendev.org/547850

Limits
======

`Forum Etherpad <https://etherpad.openstack.org/p/DEN-unified-limits>`__

`Keystone PTG Etherpad <https://etherpad.openstack.org/p/keystone-train-ptg-unified-limits>`__

`Cross-Project PTG Etherpad <https://etherpad.openstack.org/p/ptg-train-xproj-nova-keystone>`__

We had a Forum session in which the keystone team, nova team, and operators
could discuss the next steps for unified limits in keystone, especially with
regard to the migration plan. We have never done a service-to-service migration
before, so migrating limits from the nova database to the keystone database is
new territory. We plan to implement an offline migration using the nova-manage
utility to export limits to a file and keystone-manage to import them into the
keystone database. Nova will also change their quota APIs to proxy to keystone
as necessary so that operator tooling will continue to work. There are further
details in the `limits proposal for nova`_.

The migration plan is meaningless until we have an implementation in
``oslo.limit`` to consume the limits API from keystone. So far we have been
unable to get traction on the design. We agreed that we need to land some code,
any code, in order to be able to iterate on it, and that the initial
implementation will be as simple as possible and not use context managers for
managing race conditions.

.. _limits proposal for nova: https://review.opendev.org/602201

Team Cycle Retrospective
========================

We opened our PTG time with a `cycle retrospective`_. There were a few major
takeaways around planning work and empowering contributors.

We need to focus on breaking large work topics into small, independent tasks.
We did a good job of this with the `policy rework bugs`_. The Flask refactor was
also split up well, though if we took on something like that again we should
plan and track each unit of work. This helps spread the load of code and reviews
across the team and encourages 20%-time contributors or new contributors to pick
up chunks of work without needing to have a lot of background knowledge on the
project or needing to commit a lot of time to finishing a massive initiative. We
will discuss evolving the "low-hanging-fruit" bug tag to try to estimate size
and difficulty of a given task.

Relatedly, we also want to continue to participate in Outreachy but we've been
lacking good introductory tasks for applicants to complete as part of their
application. If we can come up with enough bite-sized real-life tasks for
applicants, then great, but we also discussed having a `set of exercises`_ for
applicants to complete that would not necessarily ever be merged.

Another outcome was that we need to do a better job of planning and following up
on work throughout the cycle. We often have ambitious cycle goals that peter out
during the cycle or get deprioritized in favor of other work. For large scale
refactors, like the Flask work or the token model refactor, we need to make sure
we plan for it ahead of time and break it up into distributable chunks. We also
will draw harder lines when it comes to `due dates`_, and do regular check-ins
through the cycle as well as a virtual midcycle to ensure we are keeping a
cadence going, keeping motivation high, unblocking people sooner rather than
later and reevaluating our overall direction. We'll also plan to revamp office
hours by planning ahead of time what the topic will be so that we can make
productive use of the time together outside of the regular meeting.

.. _cycle retrospective: https://trello.com/b/VCCcnCGd/keystone-stein-retrospective
.. _policy rework bugs: https://bugs.launchpad.net/keystone/+bugs?field.tag=policy
.. _set of exercises: https://etherpad.openstack.org/p/keystone-train-ptg-outreachy-brainstorm
.. _due dates: https://releases.openstack.org/train/schedule.html

Technical Vision
================

`Forum Etherpad <https://etherpad.openstack.org/p/forum-technical-vision-doc>`__

`PTG Etherpad <https://etherpad.openstack.org/p/keystone-train-ptg-vision-mission>`__

The TC created a `technical vision for OpenStack`_ and `requested that projects
do a self-reflection`_ against it. So far, only a few projects have done so,
keystone among them. In the Forum session with the TC, it was clear that the TC
had provided no incentive or urgency for projects to complete this
self-evaluation. While the technical vision is in large part about evaluating
new project additions to OpenStack, it is also useful for older projects, like
keystone or nova, to go through this exercise and reaffirm that the direction we
are moving in is in alignment with the overall technical direction of the
OpenStack project, especially since our central role in the ecosystem means that
we have helped set the direction from the beginning and our decisions continue
to have a widespread effect.

In `keystone's self-reflection document`_, we also included a mission statement,
which we have tried to write for a while but had never found the right format
for it. Now we have a starting point, though it is currently very brief. During
the PTG, we discussed adding more wording about keystone being a discovery
service, as well as highlighting multi-tenancy more in light of our focus on
unified limits these past few cycles. We also discussed the possibility of
mentioning something about resiliency, especially with regard to distributed
architectures like Edge systems. We also may want to use the mission statement
to mention our obligations to the OpenStack ecosystem due to our central role in
it.

For the rest of the technical vision, we want to add something to address the
"Bidirectional Compatibility" section of the TC document, since interoperability
and discoverability is a high priority for us. We also want to personalize the
document to keystone somewhat, by adding "secure by design" as part of
keystone's project vision.

.. _technical vision for OpenStack: https://governance.openstack.org/tc/reference/technical-vision.html
.. _requested that projects do a self-reflection: http://lists.openstack.org/pipermail/openstack-discuss/2019-January/001417.html
.. _keystone's self-reflection document: https://docs.openstack.org/keystone/latest/contributor/vision-reflection.html

Cycle Plan
==========

`PTG Etherpad <https://etherpad.openstack.org/p/keystone-train-ptg-cycle-planning>`__

`Train Roadmap <https://trello.com/b/ClKW9C8x/keystone-train-roadmap>`_

.. image:: {static}/images/train.jpg

We have another ambitious cycle planned. Our top goals will be to complete work
started in past cycles, especially around policy, application credentials, MFA,
and unified limits. We'll also be prioritizing federation and Edge-related work.

We also need to plan time to complete community goals, even though the TC has
not approved all of the Train goals yet, and to complete technical debt cleanup
such as cleanup and refactoring of keystonemiddleware.
