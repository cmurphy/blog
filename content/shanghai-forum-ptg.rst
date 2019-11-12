:title: Shanghai Open Infrastructure Forum and PTG
:slug: shanghai-forum-ptg
:sortorder: 30
:date: 2019-11-12 17:00

.. image:: {static}/images/shanghai.jpg

The Open Infrastructure Summit, Forum, and Project Teams Gathering was held last
week in the beautiful city of Shanghai. The event was held in the spirit of
cross-cultural collaboration and attendees arrived with the intention of
bridging the gap with a usually faraway but significant part of the OpenStack
community. Yet I left the event feeling somewhat unfulfilled in that regard:
very few people attended the "`meet the leaders
<https://www.openstack.org/summit/shanghai-2019/summit-schedule/events/24426/meet-the-project-leaders>`_"
events apart from the leaders themselves, and, especially disappointingly to me,
no new community members attended the keystone onboarding session. The general
atmosphere was subdued, with key players missing from the event due to travel
constraints and even those in attendance admitting that their focus will soon be
shifting away from OpenStack.

Nevertheless, from a keystone perspective the event was productive in spite of
the majority of the team not being present. I used the time to spread the gospel
of policy and was encouraged that most teams are ready to take the plunge with
their policy overhauls.

Next Steps for Policy in OpenStack
==================================

Forum
-----

`Forum Etherpad <https://etherpad.openstack.org/p/PVG-keystone-forum-policy>`__

Now that the keystone team has laid down a path forward to overcome the
longstanding plague of `the admin-ness problem
<https://bugs.launchpad.net/keystone/+bug/968696>`_ as well as the lack of a
consistent read-only role and has itself completed the policy migration that can
be used as an example, my top priority this week was to evangelize our proposed
RBAC overhaul. We started the week with a forum session to ensure we had
alignment on the path forward. The outcome was positive: everyone seemed to be
familiar with the changes needed and was on board with the proposal, and we even
had a large number of people volunteer to take on the work. We agreed to form a
`pop-up team <https://governance.openstack.org/tc/reference/popup-teams.html>`_
to coordinate the work initially. The team will produce a document of best
practices that will be used as a basis for a `community goal
<https://governance.openstack.org/tc/goals/index.html>`_ in 1-2 cycles. Using
the pop-up team structure first rather than jumping straight into a community
goal is preferable because the team will be able to uncover, solve and document
issues that the keystone team may not have faced itself.

We also discussed the possibility of operator tooling to help operators secure
their deployments while projects are in transition, since the migration will be
a long-term effort but there will be no net benefit to operators until all
projects they have deployed have completed the migration. It would be helpful if
tooling existed to somehow automatically block unfinished policies, but writing
such an insightful tool would most likely be very difficult. We didn't come to a
tangible conclusion on this.

QA
--

`QA PTG Etherpad <https://etherpad.openstack.org/p/shanghai-ptg-qa>`__

I met with the QA team to discuss forming a common testing interface for new
policy changes. During keystone's policy migration, we implemented unit tests to
perform regression testing for the new default policies. This had the advantage
of allowing us to implement tests in the same patch as the policy changes, but
a quirk in keystone's implementation caused these tests to be extremely
expensive. It's also not suitable as a common framework that other projects
could share, as it is based on the Python-Flask TestClient utility and other
projects will have their own unique web framework implementations. I proposed
adding functionality to tempest to provide new personas that could exercise all
available scopes and all default roles for every policy rule. This has the
advantage of being common to all service projects, but runs the risk of being
too heavyweight for many projects. One possibility to make tests less
heavyweight could be to implement a decorator similar to `osprofiler
<https://docs.openstack.org/osprofiler/latest/>`_ to only check policy on API
calls and bail out without performing the rest of the logic in the call. This
would be useful in many cases but would not help for some tests where the result
of the call is significant, such as resource list calls under different token
scopes. `Patrole <https://docs.openstack.org/patrole/latest/>`_ is another
option for testing policy, but it would need work to become aware of the changes
we are making in how policy works. Moreover, its main use case is testing custom
policies in active deployments, and it's not currently well-suited for
regression testing of the new default policies that services will be
implementing. We agreed that making the new personas available in tempest is
useful and projects can choose to use them or choose to implement unit tests. If
using tempest, projects can implement the new tests in their own tempest plugins
and create non-voting CI jobs to validate them. Once the migration work is
completed and the jobs are green, they can become voting.

We also needed to address how to handle existing tempest tests once projects
become scope-aware, remove deprecated policies and set enforce_scope to true.
Since tempest is branchless, the old admin credentials will have to work for
both new system-scoped admin calls as well as old project-scoped admin calls
that behave as admin-everywhere calls. We agreed to use config flags to enable
forwarding of the admin client to either system-scoped or project-scoped admin
credentials.

Barbican
--------

The barbican team already completed Step 1 of the policy migration by
`evaluating <https://wiki.openstack.org/wiki/Barbican/Policy>`_ all of their
existing API rules for whether they fit under system or project scope or admin,
member, or reader roles, and so are already well on their way to completing the
migration.

Cinder
------

`Cinder PTG Etherpad <https://etherpad.openstack.org/p/shanghai-ptg-cinder>`__

The cinder team had questions about testing and we recapped our discussions with
the QA team. We also discussed how to handle cinder's existing database-level
project checks. I clarified that the scope_types option in oslo.policy's rules
class is not overridable by operators, so for APIs that can only make sense in
the context of a project, it may be okay for in-code project checks to remain.
However, for policies that should be system-scope, requiring a project will
clearly need to be reworked.

Nova
----

`Nova PTG Etherpad <https://etherpad.openstack.org/p/nova-shanghai-ptg>`__

The nova team's main concern was with how a multi-cycle policy migration will
affect operators, given that the keystone team took two cycles to complete its
migration which resulted in an extra cycle with deprecation warnings in the logs
that operators could do nothing about. We discussed various technical means of
doing this, mainly by modifying oslo.policy, but landed on simply keeping an
unmerged stack of changes under review until the stack was complete and only
merging it then. It will be interesting to see how this goes and whether we can
recommend it to other projects or if we will need to handle this in oslo.policy.
We also agreed that the keystone team will need to help review at least the
first few changes to help ensure the migration proceeds in the right direction.

Neutron
-------

`Neutron PTG Etherpad <https://etherpad.openstack.org/p/neutron-ptg-temp>`__

The discussion with the neutron team was straightforward. They also had
questions about testing and I again recapped the discussion from the QA meeting.
There was some question about how to handle the stadium projects that I couldn't
quite answer.

Glance
------

I did not meet with the glance team but glance was a topic of concern because it
has not completed the migration to `policy in code
<https://governance.openstack.org/tc/goals/selected/queens/policy-in-code.html>`_
which is a prerequisite for being able to deprecate and change default policies.
It seems there was a misunderstanding of how big a challenge that would be, and
given the lack of people-power in the project it went untackled. It turns out it
should not be that much work and is now even `in progress
<https://review.opendev.org/693129>`_.

Keystone-Adjacent Forum Topics
==============================

Project Resource Cleanup
------------------------

`Session Etherpad <https://etherpad.openstack.org/p/PVG-Deletion-of-resources>`__

Deletion of OpenStack resources owned by a keystone project is a regular topic
of discussion. Last time it was decided that the implementation should be done
in openstacksdk, but no progress was made on that implementation. Recently there
was renewed interest in the `ospurge <https://opendev.org/x/ospurge>`_ tool and
there is now a maintainer for it, so it now seems feasible to put backing behind
this tool. There is a plan to lift the ospurge logic into openstacksdk. There
should be no change needed in keystone, but there was some question about
whether the tool should disable or delete the project in keystone, but in the
end this seemed like a workflow-specific choice that the tooling shouldn't be
opinionated about.

Change of Ownership of Resources
--------------------------------

`Session Etherpad <https://etherpad.openstack.org/p/PVG-Change-ownership-of-resources>`__

This is another recurring topic, but the room expressed that it is not nearly so
critical as resource cleanup, and in fact is a cloud anti-pattern that can be
somewhat solved by educating customers about cloud patterns. It was agreed that
since it was not important enough to anyone to dedicate an engineer to it, it
won't be actively pursued this cycle, but the current status still needs to be
documented in case someone wants to step up in the future. Changing resource
ownership directly is a hard problem to solve, but being able to `reparent
projects <https://bugs.launchpad.net/keystone/+bug/1840090>`_ may be an
alternative (but perhaps not easier) way of accomplishing a similar result for
operators making use of using keystone domains or hierarchical project
structures.
