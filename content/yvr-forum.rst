:title: Vancouver OpenStack Forum 2018
:slug: yvr-forum
:sortorder: 30
:date: 2018-06-02

Another busy summit back in beautiful Vancouver, BC. I spent my time split
between keystone topics, TC discussions, and general community topics.

Keystone
========

Default Roles
-------------

`Etherpad <https://etherpad.openstack.org/p/YVR-rocky-default-roles>`__

This session was for discussing the `plan to implement a set of default roles`_
across OpenStack. The plan is to leverage the new power of oslo.policy to
deprecate policies and start introducing the named roles `reader` and `member`,
in addition to the existing `admin` role, into policy files, replacing the
default-wildcard policies we have now. Keystone itself won't add any new
features except to explicitly create the roles during the `keystone-manage
bootstrap` command, so this proposal is mainly about gathering feedback on the
names and intent of the explicit roles.

Some of the feedback in the room was that this step does not go nearly far
enough. It doesn't do much to help operators who were doing anything non-trivial
in their policy files. It doesn't help the strange situation we have with
horizon where the policy files must be copied. It doesn't address the problem
that distros often regard policy files as non-config files and overwrite them at
will, though the policy-in-code community goal does help address that since
distros won't have to ship policy files (once all projects accomplish this).

There was some discussion on the chosen names, especially with regard to the
read-only role which the spec had previously designated `auditor`. There was
some feeling that the auditor name implies having more details on the cloud than
we actually expose. Since then, we changed the name to `reader`, but in any case
it's clear that the intent behind the names should be clearly documented.

Many people were interested in enhanced policy testing, specifically with
Patrole. We want to build this regression testing for policies into our gate,
but we want to wait until after we have these default roles settled so that we
don't accidentally lock ourselves into the old behavior.

.. _plan to implement a set of default roles: http://specs.openstack.org/openstack/keystone-specs/specs/keystone/rocky/define-default-roles.html

Operator Feedback
-----------------

`Etherpad <https://etherpad.openstack.org/p/YVR-rocky-keystone-feedback>`__

We had our usual session for sitting down with keystone operators and came away
with a few actionable items to improve on.

Operators from one company brought up their issues with replicating data across
sites. They are using a proprietary database replication solution that does not
handle schema changes very well. While we can't fix their replication issues
directly, the general ask was for better multiregion support, which has been a
common request as Edge computing continues to gain traction.

A performance issue with database migrations was discussed, where the number of
rows being operated on in a migration is either inefficient on large datasets or
too large for Galera to handle in a transaction. This turned into a `bug
report`_ and even a `patch`_.

We discussed an issue with domain-scoped tokens created by Heat, where the
tokens would not have a catalog when endpoint filtering was enabled. Endpoint
filtering is very under-tested so it's not surprising that there may be bugs
with it, but it's also possible that having the catalog be optional was
intentional behavior. We need to investigate.

We need to address `an issue we still have`_ with federation mapping rules where
the group membership created by a mapping does not actually correctly persist
the role assignment for the user when using either trusts or application
credentials. The alternative to group membership via federation mapping is
auto-provisioning direct role assignments, which also seems to have its own
problems since the role assignment doesn't exist before the user logs in and
also lasts long after the user has logged out. Application credentials are
currently immutable, but we think having "refreshable" application credentials
that are re-upped when they are used will help improve the story around
persistent role assignments for federated users.

.. _bug report: https://bugs.launchpad.net/keystone/+bug/1772988
.. _patch: https://review.openstack.org/570247
.. _an issue we still have: https://bugs.launchpad.net/keystone/+bug/1589993

Edge Architecture for Keystone
------------------------------

`Etherpad <https://etherpad.openstack.org/p/YVR-edge-keystone-brainstorming>`__

Edge computing was a dominant topic at this summit, and keystone plays a major
role in these use cases. In an Edge configuration, multiple sites or regions are
connected somehow, and keystone's involvement is ambiguous in this un-pioneered
territory. Some edge sites might not have a local keystone deployment and rely
entirely on keystonemiddleware, which either means they must make a request to a
keystone located at a central hub or they rely on a PKI token (which was removed
from keystone a few cycles ago) or some other mechanism of offline validation.
Some sites might have their own keystone, which means the keystone database must
be synced across sites somehow (Galera replication may or may not be adequate).
Finally, there might be independent keystones connected by keystone-to-keystone
federation, but this relies on a source of truth that may not be accessible when
sites are disconnected.

Which keystone data needs to be shared between sites hasn't been precisely
defined, but in general a site must be able to continue to operate autonomously
- for example, must be able to continue to manage the lifecycle of local VMs -
when sites are disconnected, and latency between sites must be considered even
when they are connected.

The question is whether to implement some kind of synchronization service,
either at the database or API layer, to sync data between sites, or if we can
leverage the existing federation models to share data between sites. In
particular, the cases where we want to support users making local changes to
sites makes federation a better option than purely syncing the databases. One
idea is to improve the application credentials story to better support federated
users creating application credentials for use at local sites even when the
federated identity source is unreachable.

TC
==

S Release Goals
---------------

`Etherpad <https://etherpad.openstack.org/p/YVR-S-release-goals>`__

We opened this session with some meta-discussion about choosing goals and why we
have community goals. Goals should be a net benefit to the whole community, i.e.
something that only benefits anyone once everyone has completed it. A secondary
purpose of community goals is to give potential contributors who might otherwise
be directionless something meaningful to work on. We need to do better at
considering the breadth of a goal and how it will impact individual projects,
especially ones struggling to complete old goals. We also should start
considering a "wow" factor for goals, and give some weight to goals that are
reasonably interesting to work on or will provide an exciting benefit.

The goal proposal that seemed to be the most agreeable in the room was the
"python 3 first" goal. Universal support for cold upgrades was also well
supported, but we might want some improvements to grenade or to support a new
upgrade tool before making it a community goal.

Official projects and the boundary of "what is OpenStack"
---------------------------------------------------------

`Etherpad <https://etherpad.openstack.org/p/YVR-forum-TC-project-boundaries>`__

There were many possible topics for this forum discussion, but we mainly
discussed `why` projects want to become official, i.e. what they gain - and lose
- by joining OpenStack. If we provided unofficial projects with some of these
things, like documentation publishing and forum space, would that alleviate some
of the perceived necessity to join? Part of the incentives are also driven by a
desire for visibility, but with OpenStack's already-wide scope many official
projects don't really get much visibility.

The flip side of the discussion is, what does OpenStack gain by adding a new
project? It's mainly the ability to showcase new features of OpenStack the
product - which means we need to have a fully fleshed-out understanding of what
the product really is and what it should be. OpenStack could be seen either as
an "IaaS" product or a "cloud" product, the latter being the wider-scoped
definition. A vision document that clarified what we see OpenStack as
encompassing and what direction we think it should go would help with evaluating
new project applications; if a project is clearly described in the document, it
should be accepted. If it is not, the project drivers could submit a change to
the document to discuss whether the mission should be broadened to include their
potential project.

TC Retrospective
----------------

`Etherpad <https://etherpad.openstack.org/p/YVR-tc-retrospective>`__

Doug Hellmann did an excellent job of `capturing this retrospective`_.

.. _capturing this retrospective: http://lists.openstack.org/pipermail/openstack-dev/2018-May/130835.html

Adjutant and StarlingX
----------------------

`Etherpad <https://etherpad.openstack.org/p/YVR-forum-TC-Adjutant>`__

We talked to the drivers for the Adjutant project which is `seeking to become an
official OpenStack project`_. While it is very clearly a useful project, members
of the TC have concerns about admitting it as an official project. The concerns
are about the wideness of the scope that was proposed, which is, in a sense, to
be the glue for any business operation a cloud operator might want to implement,
and about the stated pluggability of Adjutant which would allow different public
cloud deployments to implement different APIs for the same operations. We agreed
that a first step toward making everyone feel more comfortable with the project
application was to reduce the stated scope of the project to simply what it
accomplishes now, and we can reevaluate the scope later as needed.

While it wasn't planned, we also discussed `StarlingX`_, a project which is
seeking hosting space on OpenStack's infrastructure and incubation within the
OpenStack Foundation's Edge Computing strategic focus area. The project consists
of a number of repositories that are forks of existing OpenStack projects or
even other open source projects. The biggest concern with StarlingX was the
forking of non-OpenStack projects, since hosting those could be seen as a slight
against those other communities. Hosting forks of our own repositories also
seems to be a blessing of an ugly situation that we really don't want to
endorse. While not ideal, the drivers have at least said that the eventual goal
is not to continue to maintain a divergent fork but to eventually converge it,
while at the same time they don't expect special treatment when submitting their
changes to the upstream projects. The situation is complicated by the fact that
all of the history in these repositories has been squashed due to legal issues,
but the StarlingX team is intending to make a sanitized set of patches available
to make it easier to submit them. Ultimately, the TC has no legitimate say in
StarlingX's future, but we do have the ear of the Foundation and advised them
that it might be a good idea to hold off on helping with branding and marketing
until some of these issues are figured out, and maybe to set up a website
explicitly for providing messaging about the plan for convergence.

.. _seeking to become an official OpenStack project: https://review.openstack.org/553643
.. _StarlingX: http://lists.openstack.org/pipermail/openstack-dev/2018-May/130715.html

Community
=========

Python Project Testing Interface
--------------------------------

`Etherpad <https://etherpad.openstack.org/p/YVR-python-pti>`__

A few months ago a change was made to the Python Project Testing Interface
`community guidelines`_ to instruct projects to use `stestr`_ rather than `testr`
or `ostestr` which are largely unmaintained. The session was meant to discuss
why `so many projects`_ haven't switched yet, with the assumption that there
must be some technical reason. The reality that was revealed in the discussion
was just that the change and the reasoning behind it hadn't been widely
communicated. Possible avenues to get this done are either submitting a mass
patch bomb to all projects to do the work (which must include a commit message
providing the rationale for the change), or using the community goals to
broadcast to everyone that this is worth doing.

.. _community guidelines: https://governance.openstack.org/tc/reference/pti/python.html#python-test-running
.. _stestr: http://stestr.readthedocs.io/en/latest/
.. _so many projects: http://paste.openstack.org/show/720791/

First Contact SIG: Operator Inclusion
-------------------------------------

`Etherpad <https://etherpad.openstack.org/p/FC-SIG-Ops-Inclusion>`__

The `First Contact SIG`_ was borne out of a need to serve new contributors and
guide them toward being productive community members. At first this was
generally geared toward potential code contributors, but there is also a need to
reach out to other types of contributors. The focus of this session was
operators as contributors.

One area to target is building out the operators section of the contributor
guide, such as expanding resources around bug reporting.

There was also a discussion on the need to make patch submissions easier for
operators. This might mean including tools training at operators meetups.
Another thought was to try to partner operators with experienced code
contributors; if an operator has a patch that works in their environment, the
developer could take the burden of shepherding the patch through the code review
process.

.. _First Contact SIG: https://wiki.openstack.org/wiki/First_Contact_SIG

First Contact SIG: Requirements for Contributing Organizations
--------------------------------------------------------------

`Etherpad <https://etherpad.openstack.org/p/Reqs-for-Organisations-Contributing-to-OpenStack>`__

The First Contact SIG met again to discuss writing a document directed at
contributing organizations to outline the technical and non-technical
requirements that a contributor in their organization needs to be successful as
an open source contributor, since we've come to realize that some potential
contributors face barriers to contribution due to restrictions within their own
organization. We discussed rephrasing the idea as a "recommendation" rather
than a "requirement" to avoid inadvertently putting ourselves in a combative
position with these organizations.

Technical needs include access to our collaboration tools like IRC, email, and
our gerrit instance, and exceptions to common email restrictions like being
allowed to use external email services that are better equipped to handle
significant traffic or being permitted to not include, or have tacked on by the
email gateway, standard footers. Non-technical needs are things like permission
to work outside of typical working hours in order to collaborate in real time
with other contributors, permission to agree to the Individual Contributor
License Agreement, and a clear understanding of ownership of contributions.

The discussion veered into topics that are outside the scope of what should be
in this particular document to other topics of education for contributing
organizations, such as deemphasizing contribution metrics and community titles,
and on how to make the most meaningful impact in the community.

Ops/Devs: One Community
---------------------------

`Etherpad <https://etherpad.openstack.org/p/YVR-ops-devs-one-community>`__

This session scratched the surface of our operator/developer division. We
questioned how distinct this division really is; many of us wear both hats. An
interesting assertion that came up was that many operators are intimidated to
dive into the python code, which was met with disbelief by other operators in
the room who saw reading the code as a critical part of debugging. The
difference may be due to differing levels of support from distributors and
differences in how early on operators got in to the OpenStack game.

The main topic was whether and how to merge our various mailing lists. We
currently split our discussions into primarily the openstack, openstack-dev,
openstack-operators, and openstack-sigs mailing lists. This means that messages
intended for multiple audiences usually get cross-posted which causes a messy
discussion history, and posting messages to only one list when the topic is
suitable for multiple audiences reinforces the silos.

The Zuul project uses only two mailing lists, zuul-discuss and zuul-announce.
This seemed like a good model to follow, but it was pointed out that the Zuul
project is much lower traffic than the OpenStack project which makes it hard to
compare. Mailman3, which the infra team is looking into moving to, might make
it easier to participate in conversations without subscribing to a firehose of a
list.

If we decide to go through with this, the effect will be marginally less traffic
for people using the openstack-dev mailing list but it will be a significant
traffic influx for people using the openstack-operators mailing list.

Diversity SIG
-------------

The Diversity SIG met without an agenda but discussed some important topics. One
of the first things we talked about was broadening our axes of diversity to
focus on, especially with regard to queer representation in our community. We
want to ensure we are more sensitive to people already in the community but also
to help grow the community by having visible representation of various
minorities, even for those who exhibit no outward traits. One of the key issues
identified in the room was transphobia exhibited by community members, and we
want to ensure that we have ways of combatting problems like this.

The question of why primarily non-men attend diversity-related events like the
forum session or the Women of OpenStack lunch was brought up. While some were
quick to accuse the community of not placing a high enough priority on diversity
discussions, it was pointed out that there is not always clear communication on
who is invited to such events. Specifically, it was not clear whether the Women
of OpenStack breakfast or lunch events were intended to be "safe spaces" or
whether they were meant to be all-inclusive. Clearer messaging around these
events would help.

Missing Features in OpenStack for Public Clouds
-----------------------------------------------

`Etherpad <https://etherpad.openstack.org/p/YVR-forum-missing-features-pc>`__

The discussion started with some meta-discussion on processes around gathering
requests and feedback. The SIG `uses launchpad`_ for tracking their major issues
and the room agreed that was sufficient for now. Gathering the scale of issues
reported, i.e. how many people need a particular feature, is important for
prioritizing issues, so making more use of launchpad's "affects me" button
should be promoted. Providing agile-style user stories when requesting features
was stressed, since understanding context behind an issue can open up more
avenues for solutions. These strategies are useful for operators to make
requests at developers but we don't have a good process for getting feedback
in the other direction. One possibility is to extend the user survey to get more
precise feedback.

The discussion then shifted to directly discussing pain points and missing
features. This included things like ipv6 support, performance problems in
horizon, and updating keypairs in instances.

Some of the major requests were for keystone. The community needs better quota
management support, which we hope to `address in keystone`_ this cycle. We also
need a better way of cleaning up resources orphaned by a deleted keystone
project. And better MFA support, which is also `on the way`_ this cycle, was a
key request.

.. _uses launchpad: https://bugs.launchpad.net/openstack-publiccloud-wg
.. _address in keystone: https://review.openstack.org/540803
.. _on the way: http://specs.openstack.org/openstack/keystone-specs/specs/keystone/rocky/mfa-auth-receipt.html

Extended Maintenance
--------------------

`Etherpad <https://etherpad.openstack.org/p/YVR-extended-maintenance>`__

There were two back-to-back sessions on Extended Maintenance to recap and
reaffirm `the direction`_ that was agreed on since the Dublin PTG and to discuss
next steps. Starting with Ocata, branches that reach the end of the 18-month
maintenance span will no longer be immediately deleted. Who maintains those
branches at that point is an open question. One suggestion is to have people
"sign up" to maintain branches, but this not really effective and doesn't
guarantee that the people who sign up will actually do the work. There's already
a process in place for giving core responsibilities to the people who step up to
do the work. It would be good, however, to have a way to build a community
around branch maintenance so that people who are interested in maintaining
particular branches can identify other people who are similarly interested. This
could eventually evolve into an unofficial LTS model if people end up clustering
around particular releases.

The proposed plan is not to do any more releases after the 18-month lifespan,
but this reveals an oversight with regard to libraries and clients, since we
typically only test services against the released versions of libraries.
However, it was pointed out that at least devstack makes it easy to test against
the source versions of libraries with the `LIBS_FROM_GIT` option.

Tempest also poses a problem since it is branchless and until now has been
guaranteed to support all live branches. The result of this change is that
branches in extended maintenance mode will have to have their CI jobs pin to an
old enough version of tempest, but master of tempest itself need only provide
the same level of branch support it does now.

.. _the direction: https://governance.openstack.org/tc/resolutions/20180301-stable-branch-eol.html

Getting Serious on Maintainers
------------------------------

`Etherpad <https://etherpad.openstack.org/p/YVR-openstack-maintainers-maint-pt3>`__

This session ended up being mostly about developer retainment by reducing
frustration in the code review process, especially by changing our review
culture to avoid discouraging nitpicks. A `thread`_ was started and a `new
guiding principle`_ was proposed in response to this.

.. _thread: http://lists.openstack.org/pipermail/openstack-dev/2018-May/130802.html
.. _new guiding principle: https://review.openstack.org/570940
