:title: OpenStack Summit Sydney Recap
:slug: sydney-summit
:sortorder: 40
:date: 2017-11-19 15:00

I spent three days in beautiful Sydney, Australia, participating in Forum
sessions at the OpenStack Summit. This was my first time participating as both
a TC member and a keystone contributor, and moreover there was a lot of content
packed in to three days instead of spread across four, and so it was an
especially busy summit for me.

API SIG room
------------

`Etherpad <https://etherpad.openstack.org/p/api-sig-sydney-forum>`__

The session started out by discussing the API SIG's evolution from a Working
Group (WG) to a Special Interest Group (SIG). A SIG is more cross-governance
than a WG, which is governed only by the TC. Since APIs affect not just
projects governed by the TC but also SDKs not under TC governance, as well as
operators and users, a SIG was more appropriate for this group. The room then
focused on how API changes affect SDKs and their users. Deprecations, for
example, are managed server-side, and so there is lower visibility for SDK
developers and users. An idea to improve this was to have an API version
explorer in the api-ref pages to make it clearer what was changing and when it
changed.

Application Credentials Feedback
--------------------------------

`Etherpad <https://etherpad.openstack.org/p/SYD-forum-application-credentials-feedback>`__

In this session we mainly summarized the `agreements made at the Denver PTG`_.
Not much progress has been made in the work on this since then, and so not much
has changed. The operators in the room were receptive to the direction
we plan to head with this. On the issue of project-lived versus user-lived,
operators agreed that in the cases that they really do not care about the
security implications of allowing application credentials to be owned by a
project, they could create special project users to own the credential. When a
user leaves a project team, the project user's password can be changed without
affecting any applications, and the application credentials tied to the project
user can be rotated in their own time.

.. _agreements made at the Denver PTG: http://lists.openstack.org/pipermail/openstack-dev/2017-September/122087.html

Protecting Plaintext Secrets
----------------------------

`Etherpad <https://etherpad.openstack.org/p/plaintext-secrets>`__

Related but separate from the application credentials use case is the problem
of needing to embed many different passwords in service configuration files,
not just for keystone service users but for database and message queue access.
The secrets can't just be hashed, since the service needs to be able to read
the plaintext password in order to use it. Nor can it be encrypted since the
encryption key would also need to be stored securely somehow. Simply obscuring
it somehow does not solve the problem and provides a false sense of security.

This problem in OpenStack is severe, not just because of the danger of
configuration files (and also the deployment tools storing the secrets) being
compromised, but because compliance standards of various organizations prohibit
deployments of OpenStack because of how it is deployed.

The proposal is to use Castellan as an oslo.config driver to talk to a secret
storage service like Vault. Etcd could also be a possible config driver.
Barbican is not really an option here because it is tied to keystone, whereas
this solution must not be tenant-aware.

The solution would need to use something like Kerberos or x509 to access the
secrets, otherwise it's a turtles-all-the-way-down problem where we need to
store some credential in order to access the secrets.

Lazy loading passwords, meaning avoiding reading the password from config until
it was needed, was proposed as a way to avoid Castellan's dependency on
oslo.config, but this would create a point of failure since it would require
the secret storage backend to be up at the time the secret is retrieved.

What do operators want from the stable policy?
----------------------------------------------

`Etherpad <https://etherpad.openstack.org/p/SYD-stable-policy>`__

This discussion was specifically not meant to focus on the LTS problem but
instead to highlight everything else operators want the `Stable Policy`_ to
enforce. Even though this was for operators, the conversation started with
discussions around the proposal by deployment tool projects (specifically
Tripleo) for a modified stable-policy tag to allow for their common need to
backport features after release given the trailing development cycle they have
relative to the other projects they deploy. The summary of their proposal can
be found in `this mailing list thread`_.

For operators, it was clear that they wanted some changes from the stable
policy as well. They thought that new features that are wholly additive should
be allowed to be backported. The stable team reiterated that all backports had
to be weighed against the potential risk of breaking something else. Operators
thought that possibly hiding the new code path behind temporary config options
might help with this, but it could be complicated for deployment tools to
manage such temporary configs like this.

Operators also wanted bugfix authors to be more proactive about backporting
bugfixes before it is too late. For example, a fix could land in master but
also apply to the current release. Often operators won't encounter the bug
until long after the release has reached its end-of-life and changes can't be
backported. If authors who landed bugfixes immediately proposed the patch to
the current stable release, operators would be able to take advantage of it
sooner.

An example from early neutron was brought up, which was that a major security
feature was lacking from it that was present in nova-network. The fix landed
but was not backported, and operators in the room largely thought the neutron
team had misinterpreted the stable policy by not backporting it. Others in the
room felt that not having feature parity with nova-network was really not the
same as a security bug, since operators needing that feature could still use
nova-network at the time.

.. _Stable Policy: https://docs.openstack.org/project-team-guide/stable-branches.html
.. _this mailing list thread: http://lists.openstack.org/pipermail/openstack-dev/2017-October/123624.html

Interop Test Library for Openstack SDKs
---------------------------------------

`Etherpad <https://etherpad.openstack.org/p/SYD-forum-sdk-interop-test-library>`__

Aside from Shade and OpenStackClient, OpenStack has no official SDKs
(OpenStackSDK is not an official OpenStack project). In order to be able to
better evaluate and recommend SDKs to users, it would be nice if there was a
way to verify functionality and capabilities of an SDK. The initial proposal is
to build a new API service that acts as a middle layer between an SDK and an
OpenStack cloud. The new service would know when a test starts and stops and be
able to check a cloud's state after the test is run. This is different from
tempest which has it's own clients implemented within it and so requires no
middle layer.

An alternate proposal in the room was to create a cloud mock framework that
would allow tests to be run without spinning up a cloud. This would allow
humans to run tests locally more easily, and it could also be helpful for
simulating known quirks of various public clouds. However, this would be
complicated to implement and would require functional tests to ensure the mocks
are correct. It would be better in the short term to focus on creating a test
harness against devstack for now.

Shade and OpenStackClient would be excellent (and willing) guinea pigs for this
new common service.

Making OpenStack more Palatable to Part-time Contributors
---------------------------------------------------------

`Etherpad <https://etherpad.openstack.org/p/SYD-part-time-contributors>`__

It is commonly said that getting up to speed with OpenStack development takes
six to twelve months of continuous full-time work. This is far from
sustainable. With our recent drop off of startup sponsorship and large-scale
corporate involvement, we need to attract and retain contributors who may only
be able to contribute 20% of their work time to upstream development, as well
as those who would like to contribute for fun but have no corporate backing and
can only contribute in their free time. This means that we need to find ways
for those contributors to start being successful in a shorter period of time,
and to enjoy the experience and feel productive.

It quickly became clear that there was more than one type of part-time
contributor and that they faced different issues. There are the people who are
new to the project and do not yet have the contacts and context yet to get the
things they need. Then there are former full-time developers who have had to
reduce their output. This discussion was meant to focus on the former, since
the latter has all the knowledge and visibility they need in order to get
things done.

The etherpad has quite a good summary of the problems we think part-time
contributors face and potential solutions, so I won't duplicate it. A major
takeaway is that new contributors often don't have much visibility, and
therefore the respect and trust, of experienced contributors, which is a
hindrance to getting reviews for their work. This visibility is often
developed through face-to-face events which many part-time contributors don't
have the opportunity to attend.

There was no real actionable outcome from this discussion. The new contributor
portal is shaping up to be a way to fast-track new people though the initial
onboarding process, and the proposal to `use the DCO as the CLA`_ could help
people with the legal issues surrounding contribution. Some culture changes
were suggested, such as promoting a making nit changes to someone else's patch
rather than nit comments that might never be addressed, but these are of course
hard to enforce and vary widely across projects. Really we need to be able to
offer more mentorship, but this is not really a policy decision.

.. _use the DCO as the CLA: https://governance.openstack.org/tc/resolutions/20140909-cla.html

Supporting General Federation for Large-Scale Collaborations
------------------------------------------------------------

`Etherpad <https://etherpad.openstack.org/p/Supporting-General-Federation>`__

The Open Research Cloud would like to define a cloud federation vocabulary and
conceptual model at the IEEE level. Given OpenStack and keystone's open nature,
it would make an ideal partner in this endeavor.

While keystone has some support for federating OpenStack clouds, it does not
define any kind of best practice or high-level topology of federated
infrastructure, nor any involvement in the PaaS or SaaS layers. Becoming more
involved in these discussions would help us understand the use cases we need to
support and our place in the larger world of collaborative computing.

A use case that was mentioned as a possible thing to put under this type of
governance was how to evaluate a workload that is being deployed on someone
else's cloud. There's currently no defined way for the recipient to review the
workload and its network functions before allowing it to run. Being able to
certify deployed images would be something these new standards could possibly
cover.

Constellation Brainstorming
---------------------------

`Etherpad <https://etherpad.openstack.org/p/SYD-constellations>`__

Constellations are common OpenStack deployment configurations, kind of like
reference architectures but not necessarily tied to a specific use case, only
to the projects involved. They are a filter of a subset of the available
official projects and could inform reference architectures. Having this would
bridge the gap of operators having too many projects to choose from and
desiring an opinionated model fit for their use case.

This constellation recommendation portal would take the form of an image map on
the OpenStack website that would replace the "browse projects" tab. The already
existing "OpenStack powered" deployment model could serve as the first
constellation.

New constellations will be defined in a new repository that would not
necessarily need to be managed by only the TC, though the TC is a natural
starting point for initial members.

Keystone Operator and User Feedback
-----------------------------------

`Etherpad <https://etherpad.openstack.org/p/SYD-forum-keystone-feedback>`__

In this session we mostly discussed a proposal to allow specifying a project ID
upon project creation. The use case is for VNF with keystones deployed in
separate sites, not using data replication. They would like to be able to
create a token on one site and be able to use it on the second site, but
because a token is scoped to a project by ID, and because a user's ID is based
on the domain in which they were created (and domains are a type of project),
the token for one user and project will not map to the token for the same user
and project on another site.

While it would be easy to implement, the main problem with allowing
user-specified project IDs is the potential for collision. More importantly,
however, there are concerns with the security of the proposed use case. In such
a scenario, a compromised token on one site would compromise the other site as
well. We didn't come to a solid conclusion but we'll continue discussing it.

Upstream LTS Releases
---------------------

`Etherpad <https://etherpad.openstack.org/p/SYD-forum-upstream-lts-releases>`__

This was by far the most well-attended session of the Forum, as there are a
huge number of stakeholders. There were a lot of strong feelings in the room. I
could honestly not do a better job of summarizing the outcome than the followup
email threads do, so I will simply refer you to those:

`Thread from Erik <http://lists.openstack.org/pipermail/openstack-dev/2017-November/124308.html>`__

`Thread from Thierry <http://lists.openstack.org/pipermail/openstack-sigs/2017-November/000148.html>`__

RBAC/Policy Roadmap Feedback
----------------------------

`Etherpad <https://etherpad.openstack.org/p/SYD-forum-policy-roadmap-feedback>`__

We spent this session reviewing the `roadmap we created at the Denver PTG`_,
which mostly focuses on the way toward fixing the adminness bug. The horizon
team brought up the fact that they depend on the bug for showing a
complete admin dashboard and will have to find a new way to display this
information once system scope becomes available. The conversation wandered
toward philosophizing about which actions specifically in keystone would
require system scope or project scope. Creating a user, for example, could be
a system-scoped action since it is traditionally an admin action but it could
also be possible for domain admins to create users within their own domain,
which would be a project-scoped action.

.. _roadmap we created at the Denver PTG: https://etherpad.openstack.org/p/queens-PTG-keystone-policy-roadmap

First Contact SIG
-----------------

`Etherpad <https://etherpad.openstack.org/p/SYD-first-contact-SIG>`__

Every so often, a thread starts on the mailing list about how to deal with
unwanted typo fix patches that on first glance look like Stackalytics points
trolling. The latest one gave rise to the idea of a First Contact SIG to help
define policies for dealing with these and also help brand-new contributors
take their first steps.

The typo fix patches were not the only problem that this SIG could address. New
contributors also face issues when their patches get ignored and they don't
know who to reach out to to get the problem addressed, or what the etiquette is
for doing so. This new group could make introductions between new people and
the project team.

The room thought that following the Kubernetes model would be a good start.
They have a "Contributor Experience" Slack room where both new and existing
contributors can go to ask questions or make complaints, and where they can
actually get answers. We have an #openstack-101 channel that is sort of meant
for that purpose, but hardly anyone who is experienced lurks in that room and
can actually provide answers and so many questions just go completely ignored.
It was mentioned that the "101" in the name is a very US-specific colloquialism
for an introductory portal and so is not the best name for a channel serving a
global community. We decided we should try to guide people toward asking
contributor questions in #openstack-dev. There was some debate over whether
"dev" would turn off non-code contributors from asking questions there, and the
room didn't seem to have consensus over whether we should change the name of
the channel to be more welcoming or if changing the name (and updating all
references to it) would be too costly. The important thing is for it to be a
channel populated by experienced contributors, not a black hole. For now, we'll
update the new contributor portal to point to #openstack-dev.

The only people in the room for this were people either elected to the TC or
employed by the foundation. We decided that the next step should be recruiting
people from Ops and the UC. Other potential actions are to start collecting
mentors from the project teams, and to figure out what to do about
ask.openstack.org, which tends to also be a black hole.
