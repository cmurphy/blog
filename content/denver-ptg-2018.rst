:title: OpenStack Project Team Gathering: Denver round 2
:slug: denver-ptg-2
:sortorder: 30
:date: 2018-09-21 17:00

In our return to the Renaissance Denver Hotel, I participated mainly in
`keystone`_ and `Technical Committee`_ tracks.

In keystone land, we spent time on our recurring themes from past cycles, namely
RBAC improvements and unified limits. We focused less on application
credentials, as the plans from last cycle still apply for this cycle. We
revamped plans for federation improvements, given the increasing interest from
the Edge computing groups and feedback from the user survey. We also solidified
plans for implementing `JWT`_ as a new token provider.

The TC discussions were, as usual, wide-ranging and intense. If I had to sum it up
in one tagline, I would say that it centered on dissecting the TC's role or
potential roles in the OpenStack developer and user communities, from observers
of project health to managers of development priorities to ambassadors of
cultural outreach.

I also tried to participate in the First Contact SIG track but ended up being
pulled into other rooms that morning, so `here is Kendall's summary`_.

.. _here is Kendall's summary: http://lists.openstack.org/pipermail/openstack-dev/2018-September/134888.html
.. _keystone: https://docs.openstack.org/keystone/latest/
.. _Technical Committee: https://governance.openstack.org/tc/
.. _JWT: https://jwt.io/

Keystone
========

`Etherpad <https://etherpad.openstack.org/p/keystone-stein-ptg>`__

See also `Lance's summary <https://www.lbragstad.com/blog/openstack-stein-ptg-keystone-summary>`_

Unified Limits
--------------

`Etherpad <https://etherpad.openstack.org/p/keystone-stein-unified-limits>`__

We opened our cross-project day by discussing next steps for `Unified Limits`_,
our effort to centralize resource quota management within keystone. We clarified
that the limits API does support a way of showing the project hierarchy, which
consuming services will need in order to calculate usage when hierarchical
project models are used. In the nova room later in the week, we discussed this
with regard to recreating the same dashboard experience that users have today,
where limits and usage are shown in a combined view: the approach will be to
query the limits API in keystone which will provide the project hierarchy, and
to feed that as input to the usage API in the individual service. This could be
done via successive calls in the client or could be built into the usage API of
the service. There was a feature request to be able to describe a class of
limits, so that for example the nova service could retrieve all limits related
to nova instead of querying them individually.

We discussed the oslo.limit library, and fleshed out some of the
`possible implementations`_. It was agreed that there should only be a single
callback to the service which should handle both usage calculation and cleanup
in the event of a failure or race condition.

We brought up the fact that quotas tend to be incidentally used for user rate
limiting, which is a different problem area than scheduling usage of the
underlying physical resources which quota is intended to help facilitate.
Perhaps these cases should be moved into config instead of quotas. The main case
where nova uses user rate limiting that would not make sense in a project-quota
world is for key-pairs, which could just be handled either in nova config or as
a one-off limit API in nova.

Once the implementation is fleshed out, creating an upgrade path will be a
challenge. We tried to discuss ways that a service could cleverly decide whether
to use keystone limits or in-service limits and decided that was too susceptible
to ambiguity, and the best option was to create a flag in config that would let
the operator decide when to do the switch. A status check could be added to the
upgrade checker to help operators decide when it is safe to switch.

We got feedback about Edge computing use cases in which an operator might want
to ensure that quota is set the same across all edge sites. Unless the
keystone database is replicated across sites, there would be no way to do this
with the current implementation since project IDs will always be different, but
we advised that automation could be set up such that quota is set upon user
signup.

.. _Unified Limits: http://specs.openstack.org/openstack/keystone-specs/specs/keystone/ongoing/unified-limits.html
.. _possible implementations: https://gist.github.com/lbragstad/69d28dca8adfa689c00b272d6db8bde7

RBAC
----

Shockingly, we didn't fill as much time discussing RBAC as we usually do, as we
still have a lot of leftover work from last cycle that remains in the same state
and did not require additional discussion, but we did touch on one idea: to
expose the currently hidden root domain, creatively named
``<<keystone.domain.root>>`` in the database, as a top-level project such that
having an inheritable admin role assignment on this domain would allow effective
project-scoped god-mode across all projects across a deployment. This comes very
close to bringing back the ``is_admin_project`` plan, with the difference that the
inheritance model makes it a bit more natural. This would solve the problem that
system scope currently doesn't solve, which is that operators sometimes need to
administratively operate on a project-level, for example to boot or clean up a
server on behalf of another user. Operations such as live-migration, which
require knowledge of hypervisors and more than one project, would still be
system-scope operations.

Discussions about limits and quotas bled into RBAC discussions as it became
clear that sometimes project or user quotas were essentially being used for RBAC
purposes. For example, creating a load balancer with a certain backend or
booting a server that used CUDA graphics cards is an expensive operation and so
it's useful to be able to limit these operations to certain users by controlling
their quota.

Federation
----------

One of the takeaways from the recent `User Survey`_ was that polishing federated
identity was a top priority for operators. We identified several major usability
bugs that should get top priority this cycle, as well as enhancements like
actual logout support, proper support for linked identities via shadow users,
WebSSO support for keystone-to-keystone federation, and native SAML support with
a pluggable interface in consideration of the potential to eventually support
native OpenIDC or other protocols.

A major topic of discussion was the potential to make keystone better suited to
run as a standalone component by giving it the power to act as a proxy IdP. The
inspiration is a service called `dex`_ which implements the OpenID Connect
protocol as a portal to other identity providers of various protocols. We
whiteboarded a model using OpenStack's infrastructure services as an example;
say a user wants to log into the Gerrit web interface on review.openstack.org.
Currently they are forcibly redirected to launchpad.net to either authenticate
or reauthorize Gerrit to use data from launchpad. In the proposed model, the
user would be redirected to a keystone instance which would present a web form
(fully independent of horizon) where the user could select an identity provider
to log in with, which could be openstackid.org or launchpad.net or google.com,
or could even be the local keystone database. After selecting an identity
provider, authenticating with it and returning to keystone, keystone needs to
send some kind of proof of identity to the service provider that it can
understand: if the service can use keystonemiddleware then this could be an
ordinary keystone token, in the Gerrit case it would probably have to be an OIDC
id_token in the form of a JSON Web Token, for other cases it could be a SAML
assertion.  We might even consider writing new versions of keystoneauth and
keystonemiddleware in languages besides Python to make this more universal.

We've long tried to skirt the idea that keystone's primary purpose is to be an
identity provider, but it's an undeniable fact that "we are in the business of
managing identity" (-Morgan) and taking the extra leap to becoming an IdP proxy
would be very useful. However, it's also undeniable that keystone's particular
flavor of AuthZ, designed mainly to accommodate OpenStack's need for
multitenancy, is an integral part of keystone. If we were to proceed in this
direction, we would need to find a standardized way of applying our "scoped
RBAC" to other non-OpenStack services.

.. _User Survey: http://lists.openstack.org/pipermail/openstack-dev/2018-September/134434.html
.. _dex: https://github.com/dexidp/dex

JWT
---

We revisited the idea of implementing `JSON Web Tokens`_, now with a more
fleshed-out use case that gives us a design direction to go in. The use case is
for supporting multiple regions, where one region contains a master keystone
instance and the other regions contain read-only synchronized keystone instances
that serve to validate tokens. A setup like this comes closer to bridging the
gap between making a round trip to an out-of-region keystone and bringing back
support for offline token validation, for which we haven't yet found a good
solution given the unbounded nature of role assignments which would bloat the
token. The asymmetric signing functionality of JWT is useful in this case
because the public keys of the different instances can be safely distributed
while the private keys never have to be shared.

We discussed whether the tokens need to be encrypted or just signed (Fernet
tokens are symmetrically encrypted). Since the tokens are still bearer tokens,
an attacker gaining access to an unencrypted token does basically the same
amount of harm as would gaining access to an encrypted token. The two concerns
are that (1) users might come to rely on the format of the payload of an
unencrypted token rather than validating it with keystone, which either binds us
to not changing the format or eventually breaks those users relying on it, and
(2) some organizations might consider the content of the payload, such as the
user ID, to be sensitive, which would mean that even a revoked or expired token
could be leveraged. Encryption and decryption of tokens will also very likely
affect token validation performance. Finally, nested JWT (a JWS as the payload
of a JWE) is not natively supported by the predominant JWT library (`PyJWT`_) so
if we implement encryption we will either need to build on top of that library
or try to upstream the feature. We agreed that a first JWT implementation need
only support signing and we can add encryption later if needed.

Key rotation for an asymmetric system will work mostly the same as the current
symmetric system we use with Fernet, just that separate repositories will be
needed for the public and private keys and only the public keys will need to be
distributed. We'll also need to consider how to handle revocation lists.

.. _JSON Web Tokens: https://review.openstack.org/541903
.. _PyJWT: https://pyjwt.readthedocs.io/en/latest/

Release Planning
----------------

`Trello Board <https://trello.com/b/rj0ECz2c/keystone-stein-roadmap>`__

We enumerated all of our priorities for the coming cycle. We need to finish up
work that was put off last cycle, namely `fine-grained access control for
application credentials`_, `receipts for multi-factor auth`_, and auditing work
for `default roles`_ and `system scope`_. We also need to finish the `flask
conversion`_ that was started last cycle.

Additionally, we have the two community goals for this cycle (`python3-first`_
and `pre-upgrade check tooling`_), along with one goal from last cycle (`mutable
config`_) which was postponed due to the flask work.

We also talked about project work we could propose for the `Outreachy`_ program,
such as leveraging flask's testing utilities to clean up our API unit tests,
reorganizing our module subsystems, or some of the federation enhancements.

We also plan to prioritize some basic usability improvements for federation in
advance of starting more in-depth work on things like implementing a proxy IdP.

.. _fine-grained access control for application credentials: http://specs.openstack.org/openstack/keystone-specs/specs/keystone/stein/capabilities-app-creds.html
.. _receipts for multi-factor auth: http://specs.openstack.org/openstack/keystone-specs/specs/keystone/stein/mfa-auth-receipt.html
.. _flask conversion: https://bugs.launchpad.net/keystone/+bug/1776504
.. _default roles: http://specs.openstack.org/openstack/keystone-specs/specs/keystone/rocky/define-default-roles.html
.. _system scope: https://bugs.launchpad.net/keystone/+bugs?field.tag=system-scope
.. _python3-first: https://governance.openstack.org/tc/goals/stein/python3-first.html
.. _pre-upgrade check tooling: https://governance.openstack.org/tc/goals/stein/upgrade-checkers.html
.. _mutable config: https://governance.openstack.org/tc/goals/rocky/enable-mutable-configuration.html
.. _Outreachy: https://wiki.openstack.org/wiki/Outreachy

TC
==

`Etherpad <https://etherpad.openstack.org/p/tc-stein-ptg>`__

Once again, there were many topics discussed on Sunday afternoon and Friday,
which `Doug has already summarized`_, so I'll elaborate on the most passionately
discussed ones.

Joint Leadership Meeting
------------------------

On Sunday, the board chair (Alan Clark) asked for input from the TC on shaping
the future of the joint leadership meetings that usually happen the day before
summits. Open communication with the board and the foundation has always been a
bit of a sore point with the TC, so the invitation for feedback was welcome.

We mentioned that the chaotic atmosphere of what is supposed to be a formal
meeting makes it hard for the more reserved of us to participate. This is a
funny contrast to how usual TC-lead meetings operate, which from my perspective
is pure chaos, but I suppose the difference is the familiar environment and
well-known boundaries. We asked for these formal meetings to act in a more
formal manner: clearly defined turn-taking, better control of the agenda and
time limits, better briefing of the agenda in advance of the meeting, and
detailed minutes following the meeting.

Alan was also able to level-set for us on how best to get a message through in a
board meeting. While most of us on the TC are comfortable with getting
informational updates over email, in this forum we need to get more comfortable
with giving and receiving such updates via presentations. We also need to use
these updates as a way to arm board members with positive messages about
OpenStack to take back to their companies: we should talk more about successes,
even if successes are as simple as "it's stable", and when we talk about issues,
they should be framed in a way that shows the issues are solvable with the right
resources.

We also reaffirmed that, even as the umbrella that the OpenStack Foundation
covers grows, the OpenStack TC remains relevant, especially as we're the oldest
project under the foundation, and still the biggest, and our guidance and advice
is sought by other projects as well as the board and foundation.

.. _Doug has already summarized: http://lists.openstack.org/pipermail/openstack-dev/2018-September/134744.html

Project Health Review
---------------------

We took some time to discuss our process for `assessing project health`_ and
then talked about some of the specific issues that had come up so far. One of
the issues was the concern for team burnout, which I had noted in my assessment
of the keystone team but which is a widespread concern for many teams. I didn't
take many notes on this part because I was doing an uncharacteristic amount of
talking, but to summarize the gist of my concern: the team has lost a lot of
tribal knowledge as longstanding contributors have dropped off, and there is a
noticeably low supply of companies who give developers the necessary agenda-free
leeway to learn a project from the ground up well enough to have a foundational
understanding of the core issues we've been working to solve for the last few
years. It's hard to create a laundry list of things we want help with that a new
person could jump in and get started on, rather we just want more people working
on basic maintenance. The discussion veered toward encouraging more willingness
to trust new people with core responsibilities, which I felt missed the point a
bit, as we're lacking the pool of people showing interest in helping in the
first place.

Another area of interest in these project health reviews was the cyborg
project's use of WeChat as a primary communication medium, which lead to a
passionate discussion on the TC's responsibility in cultural and geographic
outreach.

.. _assessing project health: https://wiki.openstack.org/wiki/OpenStack_health_tracker

Leadership Outreach in China and Asia
-------------------------------------

First of all, when we have these discussions we tend to overuse the abbreviation
"APAC". I think it's important to be very clear that there are actually a range
of barriers faced by contributors within the APAC region. While the whole area
faces timezone barriers, Asian contributors face significant language and
cultural barriers compared to Australian contributors, and Chinese contributors
in particular face additional political barriers that the rest of Asia does not.
China moreover has nearly the most contributors to OpenStack, second to the US,
and therefore when we talk about outreach to "APAC" we almost always mean
"China" and only sometimes also mean "Asia" or "east Asia", and rarely mean
"Australia".

Zhipeng Huang, former cyborg PTL, eloquently made the case that a gesture of
outreach from the OpenStack leadership in the form of a presence on the local
primary social media outlet, specifically WeChat in China, would make a huge
difference in the level of community engagement from that region and would help
to bridge the gap between the different groups. Naturally, there are huge issues
with any official mandate or even recommendation of engagement on such media:
WeChat is a non-free platform that is controlled and surveilled by an
authoritarian government, and so a resolution recommending its use puts an
implicit pressure on TC members to engage in activity that is against many of
our political and philosophical ideologies (including mine), and giving any kind
of blessing to its use could result in community fragmentation and closed
decision making. Zhipeng `proposed a resolution`_ and `started a thread`_ to
capture the request formally and hopefully the discussion will proceed toward a
mutual understanding and a way forward to better engage with this vast pool of
contributors.

.. _proposed a resolution: https://review.openstack.org/602697
.. _started a thread: http://lists.openstack.org/pipermail/openstack-dev/2018-September/134684.html

Cross-Project Management
------------------------

`Matt Riedemann started a thread`_ requesting tangible involvement from the TC
to promote the priorities of SIGs and WGs, and the public cloud WG reiterated
the ask in the afternoon meeting. They would like a coordinated effort to
organize, prioritize, and track multi-cycle multi-project issues and features
identified by SIGs and WGs. This can start with common tooling (such as
storyboard). We already have community goals which track cross-project efforts
that the TC has agreed is important on a per-cycle basis, but this is not
currently suitable for multi-cycle efforts.

Beyond tooling, the SIGs and WGs want the TC to use its position as an
overarching technical body to "nudge" projects in a productive direction. There
was pushback in the room against the TC taking on additional management
responsibilities beyond tooling guidance, with the feeling that SIGs and WGs
should be bringing developers to work on their top priorities: "open source is
not a free source of labor".

.. _Matt Riedemann started a thread: http://lists.openstack.org/pipermail/openstack-dev/2018-September/134589.html
