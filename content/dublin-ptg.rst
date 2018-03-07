:title: OpenStack Project Team Gathering: Dublin
:slug: dublin-ptg
:sortorder: 30
:date: 2018-03-09

In spite of the freak weather event in Dublin last week, we had quite a
productive PTG. It was a busy week for me as a member of the keystone team and
the TC. I spent the first two days in the Identity Integration room, the topic
room informally replacing the time spent in what used to be the Baremetal and
Virtual Machines room on identity-specific topics affecting multiple projects.
I also visited the First Contact room on Monday, but unfortunately for me they
had mostly completed their agenda in the first half of the day while I was
occupied in the Identity Integration room. I can't adequately summarize their
conclusions but Kendall posted an `excellent summary`_. The following two days I
spent with the keystone team focusing on keystone-specific topics, though some
of Thursday was spent reshuffling after the event venue kicked us out due to the
snowpocalypse. The final day I spent with the TC.

This was a hugely successful this week for the keystone team, in part because
of the cross-project discussions we lead and in part because we had operators
and architects in the room with us giving us ideas and telling us what they
struggled with. While it is always exhausting to have five full days of
in-person engagement, I find it incredibly valuable for progressing on stuck
issues, building team cohesion, and understanding different points of view.

.. _excellent summary: http://lists.openstack.org/pipermail/openstack-dev/2018-March/127937.html

Cross-project Identity Integration
==================================

Unified Limits
--------------

`Etherpad <https://etherpad.openstack.org/p/unified-limits-rocky-ptg>`__

We started the week discussing Unified Limits, a `proposal to store quota
information within keystone`_. An initial implementation of the REST API in
keystone was `completed this cycle`_. A recurring theme in this session was
questioning how much of what we've been planning and building is an
inappropriate application of a technical solution to a people problem. In fact,
the whole issue of needing to programmatically determine why a project in a
hierarchical system is over quota is built on the assumption that members of
sibling and ancestral projects cannot or don't want to just talk to each other
to negotiate quota usage.

Toward the end of the last development cycle as work on the limits API finished
up, we started having some doubts about its schema, and requested some feedback
on it in this session. The group suggested it would probably be problematic for
the create and update actions, which perform batch operations on registered or
project-specific limits, to return the entire list of limits to the requester.
It was also suggested that registered limits have a description field added. A
counter proposal was to have another library enforcing standardized names,
similar to the service-types-authority library, but this was discarded as it
would hinder projects that aren't yet or will never be "official" OpenStack
projects from being able to register their own limits in keystone, and moreover
allowing user-provided description fields could circumvent the demand for
translations of every limit type.

While it was agreed that the API could probably be reworked a bit, the only
specific action here was to start going through the exercise of writing a new
library in the Oslo family of libraries to consume this API, and to assume that
major problems in the API would shake out in that process. Specific potential
issues we should be keeping an eye on are possibly making the create and update
actions more flexible, so that they could apply to either a list of limits or to
a single one, as well as finding a way to limit the list of resources that are
returned from a create or update if we indeed decide to keep it working that
way. As we've marked the API as "experimental", we can coordinate graduating it
to "stable" with a release of a 1.0.0 version of the new library. To get started
on this, we have volunteers representing keystone, designate, ironic, and CERN
who will start working on this.

A part that we have been struggling with and postponing for a while is the
eventual plan to apply these limit and usage constraints to hierarchical
projects. A possible way forward that we all felt satisfied with was to
implement just a two-level hierarchical model, somewhat ignoring the reseller
use case for now. When assigning a project limit, a flag is set that causes the
whole tree under a node to be counted. The default limit of a project will come
from the registered limit, but that can be set to 0 or -1 (indicating infinite),
whichever makes sense for the individual use case. If the operator wants to
prevent usage of the parent project, they can just not give role assignments on
that project. Once we have something concrete implemented, it will be easier to
come to operators and have them point out specifically which parts of this don't
work for them, for example for the reseller use case. A major player here is
`CERN`_, whose `use case`_ has largely influenced this proposal. We also plan
to go to the User Committee and present this usage design and ask for operators
to provide specifics of whether this would work for their needs or how it would
not.

A part of the current proposal that was mentioned as a "missing piece" is that
in the current proposal, an attempt by an operator to reduce the quota to below
the current usage will not cause an error, rather it will simply not allow new
resource creations until the current usage is below quota. We thought that
perhaps some operators might still want that error reporting, but in following
the discussion we determined that the use case for this would be for a private
cloud operator to be able to better monitor usage by their users. We could
enable this with an external tool to validate and compare resource usage, and
putting it in keystone would not really be any more atomic than creating an
external out-of-band tool since keystone would have to query other services
anyways. In order to enable this tool, services will have to implement a "count"
API that the tool can query.

In order to provide an upgrade path, we'll have to enforce both the limits
registered in keystone as well as the limits registered within the services that
already have limits implementations for a while. We'll also need to think about
what to do with the current 'quota' command in python-openstackclient and
whether we can migrate it to the new keystone-based implementation or if we'll
have to invent a new command to manage these.

.. _proposal to store quota information within keystone: http://specs.openstack.org/openstack/keystone-specs/specs/keystone/ongoing/unified-limits.html
.. _completed this cycle: http://specs.openstack.org/openstack/keystone-specs/specs/keystone/queens/limits-api.html
.. _CERN: http://lists.openstack.org/pipermail/openstack-dev/2017-February/111999.html
.. _use case: https://openstack-in-production.blogspot.ch/2017/07/nested-quota-models.html

Improved RBAC & System Scope
----------------------------

`Etherpad <https://etherpad.openstack.org/p/rbac-and-policy-rocky-ptg>`__

As usual, this topic bled between the cross-project and keystone-specific
discussions, and so this summary covers both.

We made huge achievements in Queens with the implementation of `system scope`_
in keystone and with many projects completing the `community policy in code
goal`_. In the coming cycle, we'll need to work with the remaining projects who
have not met the goal to get them on the same page. We'll also need to start
collaborating with a few volunteer projects to start shaking out how they can
transform their policies to use the new system scope type in their policy
definitions, after which we can start thinking about proposing this
transformation as a community goal.

The next most critical step in our path toward sensible RBAC is implementing
default roles beyond "admin" and the catch-all not-quite-admin role usually
named "Member" (historically named "_member_"). The most obvious one to start
with is a "reader" role (we could theoretically also name this something like
"observer", "auditor", "viewer", etc). Then the three default roles that
keystone could provide out of the box upon bootstrapping would be a read-only
role, a write-enabled role like Member, and an admin role. This would be
implemented by creating an example pattern of policy headers to be shared
between projects. The cross-project room agreed that this was a reasonable goal,
but also voiced a request to implement per-service read-only roles as well.
We've talked about perhaps implementing a "service scope" that would effectively
be a child scope of the "system scope", and would facilitate applying a generic
"reader" role to a particular service's scope and avoid the need for
service-specific roles. It's something we could also accomplish with `implied
roles`_. Eventually, though, we agreed that a sufficient first step is to
document a common example pattern of policy rules for service-specific roles,
which the individual services could then copy into their own policy definitions.
Then, once we have this common reader role and service-specific roles, we can
start going to projects and operators to examine whether there are more
commonalities that we can define by default. For example, having different roles
for constructive versus destructive actions might be a common case.

With the advent of system scope, we now have to start thinking seriously about
what to do about service APIs that rely on the behavior of `bug 968696`_. For
example, nova gives administrators the ability to list all servers in all
projects. Since servers are owned by projects, using and enforcing system scope
for this action would prevent the administrator access to instances. We also
heard from an operator at Oath who has a use case for administrators creating
servers within non-admin projects without scoping to the project. We came up
with an idea of adding an "On Behalf Of" (for lack of a better name at the
moment) HTTP header, which could allow an admin user using system scope to
perform a project-level action without actually getting a role assignment and a
token for that project. We already have precedent for such a header with
`service tokens`_. Alongside this possibility also arose a question of
auditability, both how we could let project members know that an admin without a
role assignment on their project had performed operations in their project and
how to create an audit trail to track potential malicious behavior by a
compromised admin. Nova has no way that we could think of for notifying users of
operational changes on instances beyond the last error field and the console
log. Audit logs are, of course, not exposed to end users, but requiring a role
assignment on a project at least leaves an audit trail for admins to review. We
discussed making this "On Behalf Of" header toggleable, so that deployments that
wanted to enforce that audit-via-role-assignment trail could do so (mostly in
the public cloud use case, where admins are typically not responsible for their
customers' individual instances), but deployments that wanted greater operator
control could enable it (typical for a private cloud use case, where customers
might expect admins to manually tend to instances in some cases). Adding a
toggle raises the problem of interoperability, but since this would be an API
feature only exposed to admins, it's less of a concern.

Finally, we had some architects from Orange in the room who were able to tell us
about their issues with user-defined policies, or their external Policy Decision
Endpoint called `Moon`_. This was a `feature of oslo.policy`_ that I was
completely unaware of, where an external service can be used to centralize
policy rules and allows customization of policies to a level not available in
oslo.policy, such as constraints based on the resource ID or the time of day.
The problem was that metadata that Moon depends on for making policy decisions
was, in recent releases, not always being passed on to oslo.policy by the
OpenStack service, the biggest one being the ID of the resource being acted
upon. The question brought to the room by Orange was how to properly socialize
the need for these properties not to be dropped. We considered proposing a
cross-project spec or a community goal to address this, but decided we could
probably apply a technical solution to this: add a schema in oslo.policy to
require a set of data that external policy enforcers could rely on. This would
require a new major release of oslo.policy and the change would need to be
socialized via the deprecation process.

.. _system scope: http://specs.openstack.org/openstack/keystone-specs/specs/keystone/queens/system-scope.html
.. _community policy in code goal: https://governance.openstack.org/tc/goals/queens/policy-in-code.html
.. _implied roles: https://specs.openstack.org/openstack/keystone-specs/specs/backlog/implied-roles.html
.. _bug 968696: https://bugs.launchpad.net/keystone/+bug/968696
.. _service tokens: https://specs.openstack.org/openstack/keystone-specs/specs/keystonemiddleware/implemented/service-tokens.html
.. _Moon: https://git.opnfv.org/moon/
.. _feature of oslo.policy: https://specs.openstack.org/openstack/oslo-specs/specs/queens/external-pdp.html

Application Credentials
-----------------------

`Etherpad <https://etherpad.openstack.org/p/application-credentials-rocky-ptg>`__

In Queens we implemented `Application Credentials`_, a construct with use cases
similar to trusts but enables a user to delegate access to an application,
rather than to another user. We were able to answer some questions on what the
final result looks like. For example, anyone using keystoneauth can already take
advantage of application credentials by using the application_credential auth
method. Also, application credentials are immutable, which means that creating
one with no roles is not sensible since you can't update the role list later.

Enabling more fine-grained access control than what is currently available was
the next hot topic. It turns out we already had a spec proposed to implement a
`similar idea for trusts`_ and the author was present to talk with us about it.
The idea is for application credential creators to add a list of whitelisted API
paths to their application credentials, and to create a lightweight check in
front of (not replacing) the oslo.policy role and scope check. Application
credentials would still also have a list of one or more traditional role
assignments on projects and are still limited by those role assignments, so for
example I cannot create an application credential to boot servers if I only have
an observer role on a project. We wanted to ensure the whitelist contained API
paths rather than policy targets since one of the main users of this will be
unprivileged end users who have no insights into policy names, but API paths are
discoverable through the api-ref documents. Using API paths could even enable
finer-grained control than policy targets in some cases, since a user could
potentially limit actions to a particular resource UUID or use only certain
filter parameters by specifying this in the whitelisted path. There was a major
sense of deja-vu with this proposal, since the `RBAC in middleware`_ idea had a
lot of the same components. We will get to use a lot of the same ideas and
groundwork from that proposal. The main differences are:

* This is not a replacement or overhaul of the current RBAC model, this will be
  serial layer that superficially validates the whitelist before validating the
  actual policy rules. The audience for this feature is different than standard
  RBAC is: this is targeted at end-users who have no insights into role
  structure or policy rules, whereas changes we make in RBAC are mostly going
  to be visible only to operators.
* This doesn't require a URL mapping of all policies for all services to be
  stored in keystone. Only the list of APIs that the end-user cares about
  enabling will need to be stored in keystone, associated with the application
  credential. (This idea evolved slightly after the PTG, and now giving
  operators more control by allowing them to pre-approve some paths by storing
  them in keystone is the likely direction.)
* This doesn't require a complex tree of roles and implied roles covering every
  possible permutation of access control lists to be created by an operator,
  this can be entirely self-service.

An open question that will need to be discussed and resolved on the spec is how
to handle APIs that have implied behind-the-scenes operations, such as nova
making calls to glance, neutron, cinder, etc.

The problem of having application credentials be `user-owned rather than
project-owned`_ came up again. The summary of the two arguments is that we'd
like for application credentials and the applications that depend on them to
keep working even after the creating user is disabled or transfers teams, but we
do not want to enable users to abuse the ability to create credentials that
outlive their access. In nova there is a desire to give instances themselves
their own identity, distinct from the user who launches them. While we can't
enable this directly without opening it up to massive abuse, we do have the
ability to rotate application credentials much more easily than we can rotate
trusts or change user passwords. The non-keystoners in the room (nova, heat,
magnum) started brainstorming ways to take advantage of configdrive and metadata
services to rotate application credentials automatically and simulate the
behavior they want, and I was personally very happy to see these other teams
feeling empowered to build on this keystone feature.

.. _Application Credentials: http://specs.openstack.org/openstack/keystone-specs/specs/keystone/queens/application-credentials.html
.. _similar idea for trusts: https://review.openstack.org/#/c/396331/1
.. _RBAC in middleware: https://review.openstack.org/#/c/391624/
.. _user-owned rather than project-owned: http://lists.openstack.org/pipermail/openstack-dev/2017-July/119802.html

Keystone Team Topics
====================

API Discovery
-------------

`Etherpad <https://etherpad.openstack.org/p/keystone-rocky-ptg-json-home>`__

A very long time ago keystone grew an `API discovery document`_ built on the
`JSON-home RFC draft`_. We've been dutifully keeping it up to date every time a
new API is added but we've completely neglected to let anybody know about it.
Although the spec is still in draft form, it would be really useful to better
document this discovery mechanism and to better socialize it and promote it
within OpenStack. We could even build on it to create a kind of `capabilities
API`_ that could produce a document based on a user's role assignments.

This discovery document is how we mark the status of our various APIs, such as
designating them as "experimental". We've marked the new limits API as
"experimental" but also noticed that our implied roles API is also still marked
that way. We decided that even though we've marked it that way, the API has been
around for so long that it's unreasonable to still treat it as experimental, no
matter what the tag says. We'll promote implied roles to "stable".

.. _API discovery document: http://adam.younglogic.com/2018/01/using-json-home-keystone/
.. _JSON-home RFC draft: https://mnot.github.io/I-D/json-home/
.. _capabilities API: https://review.openstack.org/#/c/547162/

v2 Testing
----------

`Etherpad <https://etherpad.openstack.org/p/qa-rocky-ptg-remove-deprecated-apis-tests>`__

A number of projects are deprecating APIs, leaving the QA team in the position
of continuing to test these old APIs. The QA team wanted feedback from these
vertical teams about removing these API tests from tempest. In keystone's case,
we have actually not just deprecated but entirely removed the Identity v2 API.
We still want to continue testing the v2 API on the active stable branches where
it still exists, which are stable/ocata and stable/pike, but we can deprecate
those tempest clients and config and prepare for removing the tests. It was
mentioned that it's possible the admin tests have not been running for the v2
API, which is of course concerning since nearly all of our tests are admin
tests. The QA team will follow up on that and make sure the v2 admin tests are
running for the applicable branches.

CI Coverage
-----------

`Etherpad <https://etherpad.openstack.org/p/keystone-rocky-ptg-testing>`__

We have a proposal to `leverage OpenStack-Helm as part of our functional testing
gate`_. One of the appeals of this is that it already supports running an LDAP
server. However, in the course of this discussion, we uncovered the fact that we
had an Outreachy intern who has `already fixed devstack's LDAP support`_ and has
`added a devstack job`_ to run tests using LDAP as an identity backend. (We
really need to do a better job of highlighting major successes like this.) There
were a few changes still needed that I didn't quite catch, but it is overall in
good shape. We also need to address our story for federation testing, which is
still a bit of an open question. OpenStack-Helm is adding support for keystone
federation, OpenStack-Ansible already seems to have it, and we have partial
support for it in our devstack plugin, though it currently relies on an external
service which is not ideal.

Rolling upgrades has been a major topic for a while now, but we are still just
short of achieving the rolling upgrades governance tag. We've partnered with the
OpenStack-Ansible team to have rolling upgrade scenarios tested in our CI, but
it was pointed out to us that it does not cover a slightly niche corner case: if
we have a patch proposed to master that does a migration and that depends on a
patch proposed to a stable branch that also does a migration, the stable
migration is not picked up by the OSA job, which could lead to the tests passing
but actually causing a bricked install. Grenade does support this corner case,
so we either need to work with the OSA team to cover this case or we need to
switch to using Grenade to test rolling upgrades.

As we continue to improve our story around policy, it ought to be actually
tested. `Patrole`_ is an OpenStack project for helping to verify policies, which
would be great to incorporate into our CI. Unfortunately it has some limitations
that need to be worked out first. Without being a Patrole expert I can try to
sum up a design issue as it was relayed to the room: since most policy rules
default to the catch-all role we usually call "Member", they are essentially too
permissive and can cause Patrole to give misleading results. We were calling
these "false positives" but I think it can be better summarized as a suboptimal
interface in Patrole for describing expected results and reporting actual
results, combined with, of course, keystone and oslo.policy's lack of smart ways
to define less-permissive roles. Patrole also has a hard time verifying policies
for projects that don't yet have documented policy in code, like neutron, since
understanding the expected results of these rules requires a lot of guesswork.
Patrole is lacking personpower to keep up with this huge effort, so for the
keystone team to start integrating it in our CI we will need to heavily invest
in helping the Patrole team to improve it.

.. _leverage OpenStack-Helm as part of our functional testing gate:  https://review.openstack.org/#/c/531014/
.. _already fixed devstack's LDAP support: https://medium.com/@wanderleylf/devstack-ldap-plugin-part-1-baf3792e7681
.. _added a devstack job: https://medium.com/@wanderleylf/devstack-ldap-plugin-part-2-d9359f8e14df
.. _Patrole: https://docs.openstack.org/patrole/latest/

Performance
-----------

`Etherpad <https://etherpad.openstack.org/p/keystone-rocky-ptg-testing>`__

We've gotten feedback that keystone's token validation performance is, out of
the box, lacking. However, with proper caching configuration, it can generally
be raised to acceptable levels. We need to invest in documenting caching
configuration for production-grade scenarios.

Beyond the questions from users here and there around "is 200ms considered
normal?", we don't have a way to validate keystone performance. We used to be
able to run an ad-hoc job on a designated hardware node that was provided by a
team member, but we don't have that anymore. Doing performance testing within
the current confines of what the Infra team offers is unrealistic because we
cannot rely on any consistency in sequential test runs; there are characteristic
differences between cloud providers, between racks of one provider, or between
individual hypervisors of a provider, and because of the potential for other
cloud users to be noisy neighbors or for Infra to be its own noisy neighbor at
times. In talking with the Infra team we worked out a possibility of certain
cloud providers - either our current cloud providers or generous community
members with spare hardware - working out a way to get us access to a consistent
environment that is free of noisy neighbors so that we can do some accurate
statistical analysis and identify performance trends as well as catch
performance-impacting patch proposals. This is obviously something that other
projects could use as well and would be generally beneficial to the community.

Deprecations and Removals
-------------------------

`Etherpad <https://etherpad.openstack.org/p/keystone-rocky-ptg-deprecations-and-removals>`__

We made a list of things that we can start removing this cycle in the etherpad.
Some of them we've already started on, and some things we had slated for last
cycle and forgot about. The one notable outcome was deciding not to remove
keystone v2 support from python-keystoneclient, since other clients like
python-openstackclient rely on it, and because someone could easily want to use
the same client to interact with both an old and a new cloud.

Documentation
-------------

`Etherpad <https://etherpad.openstack.org/p/keystone-rocky-ptg-documentation>`__

Our Outreachy intern this cycle completed our task of reorganizing our api-ref
document into a more readable and consistent format, and is now working on
consolidating the duplicate documentation we have leftover from our import of
the openstack-manuals guides. We talked about whether we should go through the
docs to identify and correct violations of the `docs writing guide`_, but my
feeling was that that was a huge task for relatively low return on investment.
We can definitely accept drive-by patches that make these fixes, and we can
file bug reports for egregious violations when we spot them.

We still need to go through the api-ref and audit the declared expected error
codes, since we know many of them are invalid. An easy first step is to clean up
all references to 5XX errors are expected errors, since a 5XX error will always
mean either a keystone bug or an operator error and should never be considered
"expected" to an end user.

An `interesting tweet`_ enlightened us about current Identity v3 usage in the
wild, and the fact that the domain/project versus tenant concept is still hard
for people to get. We have some documentation about `domains and projects`_, but
we need to work on making a more discoverable and simplified explanation.

.. _docs writing guide: https://docs.openstack.org/doc-contrib-guide/writing-style.html
.. _interesting tweet: https://twitter.com/pilgrimstack/status/951860289141641217
.. _domains and projects: https://docs.openstack.org/keystone/latest/getting-started/architecture.html#resource

Release management
------------------

`Etherpad <https://etherpad.openstack.org/p/keystone-rocky-ptg-release-management>`__

In the Queens cycle, we waited until the official feature freeze week to land
all of our major changes, which had a predictable outcome. We agreed that we
should shoot for the week prior, in order to avoid the rush at the end of the
cycle.

We also talked about delegating the release liason work that has so far fallen
on the PTL's shoulders, which led us to also reevaluating our existing liason
assignments that were largely out of date.

Retrospective
-------------

`Trello board <https://trello.com/b/Vo6dRALh/keystone-queens-retrospective>`__

We spent about three hours having a very productive team retrospective. At the
time of this writing, the Trello board we used is not public, which is an
unintentional mistake that we'll have the board administrator rectify ASAP.

I can't sum up everything, but one of the notable outcomes was a resolution to
encourage more friendly cooperation with contributors in Asia who are currently
facing barriers due to timezones, technical challenges, and cultural differences
that we've not been conscious of. IRC is commonly blocked to employees at large
companies, so they cannot communicate synchronously with the team while they are
working in the office. A more surprising revelation was that email to outside of
the company was also blocked by some companies for data protection reasons, so
employees cannot easily send emails to our mailing lists while working in the
office. They can receive emails from mailing lists and often stay engaged that
way, and they can reach Gerrit and Etherpad. But they also commonly do not take
their work home with them, due to either business policy or simply due to a
desire to keep a healthy work-life balance, which means they also don't get on
IRC or the mailing lists after they leave the office. Language barriers further
disincentivize regular communication in English. Finally, it's just not common
in some cultures to use IRC or mailing lists even for technical communication,
but we were told that WeChat is commonly used in China to discuss OpenStack
topics.

Some of the issues mentioned are corporate policies that some North American and
European companies adopt as well, but the combination of corporate policies,
cultural differences, timezone differences, and language barriers seem to make
these challenges disproportionately difficult for Asian contributors. Some ideas
we had to try to ease these problems were:

1. Reschedule our weekly meeting so that at least one of our regular
   contributors living in China has an easier time of attending.
2. Keep on posting weekly team updates in order to broadcast what is going on
   with the team.
3. Try to get some insights into the discussions on the OpenStack WeChat.
4. Try to ensure we have a presence in Asia-based OpenStack events, like the
   OpenStack Operators summit in Tokyo or the OpenStack Days China (neither of
   which we had representation at).
5. Make more use of Etherpad and Gerrit over the mailing lists for discussions.
   Topics can still be announced and promoted on mailing lists.


Roadmap
-------

`Etherpad <https://etherpad.openstack.org/p/rocky-PTG-keystone-policy-roadmap>`__

I wasn't present for the Friday keystone sessions, but a rough cycle roadmap was
discussed and outlined in the above etherpad. We plan to finalize it in a public
Trello board in the next week.

TC
==

`Etherpad <https://etherpad.openstack.org/p/PTG-Dublin-TC-topics>`__

The TC spent all of Friday together discussing a slew of topics. Chris Dent
summarized some of them in `his recap`_. There is really too much to document in
this already long post, so I'll just sum up some of the key points that are
important to me.

Community Goals
---------------

The TC choose two `community goals`_ for the Rocky cycle, one that will be
useful for operators and one that will help reduce technical debt. The second
one, removing mox usage, was a little bit contentious because there is no
visible benefit to end users and operators and hard-to-measure benefit to
developers. Members of some project teams, especially the nova team, were vocal
and honest about the fact that they would probably not prioritize the
significant work it would take to fully complete this goal within one cycle.

A proposal was made at the in-person meeting that I found alarming, which was
for the TC to grant ourselves committer rights for projects that did not have
the review bandwidth to complete community goals. In this discussion, this idea
was framed as a kind of stick to motivate teams to do the work themselves. I
found this idea wildly objectionable. OpenStack teams are not naughty children
that the TC must discipline, rather we are a community that works together. The
nova team's objections to the mox goal are completely reasonable, and while we
do not always collectively agree on the direction or priorities of OpenStack,
punishing projects for not complying is a vastly disproportionate response.

Extended Maintenance
--------------------

The LTS discussion seemed to move in a positive direction earlier in the week in
a session I wasn't present for, but we touched on it again on Friday. There is
`a resolution proposal`_ summarizing what was agreed on in Sydney, which is to
stop deleting stable branches and instead to turn older branches over to
interested parties to maintain. John Dickinson voiced an objection that
resonates with me: OpenStack is not code, it is people. A team of people
collectively drives the direction of the projects they care about. Once that
code is handed over to a different team of people, it stops being the same
project. Therefore, sanctioning this process and continuing to call the project
by the same name in an official manner is confusing and misleading, since the
"LTS" projects could theoretically be driven in a completely different direction
than the project team had in mind, and is then effectively a legitimized fork

In other news, we agreed to stop using the words "stable" and "supported" since
those are vastly overloaded, and to instead call the thing we want "extended
maintenance".

Interop Testing
---------------

There has been another `longstanding resolution proposal`_ to clarify our
guidelines to the Interop team on where Interop tests should come from, which I
`tried to summarize`_ a while back. The current guidelines instruct the Interop
team to accept only tests that live in the Tempest repository, which is
problematic for projects such as Heat and Designate who are seeking admission
into the Trademark program but do not have in-tree tempest tests, and the QA
team has, at best, given mixed messages about whether the tests could be moved
in-tree, and at worst has fully rejected them for a variety of valid reasons,
not the least of which is insufficient maintenance bandwidth. The general but
not 100% unanimous agreement was to loosen the guidelines imposed by the TC to
allow out-of-tree tests to be used for the Interop program and `a new resolution
was proposed`_. After these discussions at the PTG ended, some more discussions
were had, and `a third idea`_ was proposed.

.. _his recap: http://lists.openstack.org/pipermail/openstack-dev/2018-March/127991.html
.. _community goals: https://governance.openstack.org/tc/goals/rocky/
.. _a resolution proposal: https://review.openstack.org/#/c/548916/
.. _longstanding resolution proposal: https://review.openstack.org/#/c/521602/
.. _tried to summarize: http://lists.openstack.org/pipermail/openstack-dev/2018-January/126146.html
.. _a new resolution was proposed: https://review.openstack.org/#/c/550571
.. _a third idea: https://review.openstack.org/#/c/550863
