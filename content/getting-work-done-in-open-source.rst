:title: How to get work done in open source
:slug: getting-work-done-in-open-source
:sortorder: 40
:date: 2019-07-30 20:00

After working in open source for a while, I've been on both sides of the code
submission dance: proposing a change, and reviewing a change.

Proposing a change to a project can feel harrowing: you don't know how the
maintainers are going to respond to it, you don't know whether you've followed
all the unwritten rules for that project. You may submit a change that no one
reviews for weeks or months, or you may be immediately charged with explaining
yourself and making completely transformative changes until your original change
isn't recognizable as your own any more.

But being a reviewer is not an easy task either. You have to try to put yourself
in the shoes of the submitter, who you most likely have never met, whose skill
level and experience with the code base you cannot judge, and try to understand
their problem and see the solution from their eyes. If the change is
particularly hairy and the submitter has not explained it very well, it's
tempting to gloss over the change and pick on the trivial things, or worse, to
just ignore the change.

While the project maintainers should carry most of the responsibility for
properly guiding a new contributor through the project's contribution processes
and helping them to meet the maintainers' expectations, there is a foolproof way
that code submitters, regardless of the project, can speed the process along:

**Write better commit messages**

The most important part of a code change is not the code itself but the commit
message. The prose you use to prepare the reviewer for the change is your best
opportunity to get them on your side. Consider that project maintainers are
humans just like you, and try to imagine what would make things easier for you
if you were reviewing a change. Perfect spelling and conformity to style
conventions are not what is important here (but I do still recommend you read up
on the `guidelines`_). What matters is getting the discussion off on the right
foot. The following is what has worked for me as a code contributor to get my
work reviewed and merged faster, and what helps me as a reviewer to more quickly
digest and respond to change proposals.

I've also `said these`_ `things before`_.

.. _guidelines: https://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html
.. _said these: https://youtu.be/pU-VasVPNAs
.. _things before: https://youtu.be/8eCxyMKejjQ

How to write good commit messages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A good commit message comes in four parts::

  What changed

  "Without this patch..."

  "This is a problem because..."

  "This patch solves the problem by..."

The subject of the commit message is a brief but clear description of what
changed. It is not enough to say "Fix bug #123". The subject must be descriptive
enough to stand on its own, because in some cases it may be the only resource
available to explain what changed. For instance, the subject line is often the
only part of a change that is pulled into a changelog, whether it's your own
changelog or a downstream package's changelog. It's also extremely useful for
the subject to be descriptive enough that you can look through a git history and
pinpoint a moment in time just by skimming the subject lines. A subject line
that identifies the component that was changed and how is going to be much more
helpful when it comes time to debug a test failure in that component than will a
generic line about fixing a bug.

The body of the commit message has at least three parts. The first part
describes the state of the world as it is today, without the change applied.
This is where you explain the bug you noticed and the symptoms you saw, perhaps
even how to reproduce it. Or discuss how the project is lacking an important
feature. This sets the reviewer up with context; if nothing else in the commit
message or the code is right, with context the reviewer can at least see where
you're coming from and from there can help guide you to where you want to be.

In the next part, you make your case for why the current state is a problem.
It is not enough to just say that the bug is a problem. Rather, you should make
the case that the bug has negatively affected you in some way or has the
potential to affect someone else, or you should show how missing this feature is
making everyone's life unnecessarily difficult. This part of the commit message
is about making it personal to the reviewer, to help them understand the
importance of this change and make them feel responsible for assisting you in
getting the change in.

Finally, in the last part of the commit message, explain how you fixed the
problem. Describe what was required to avert the bug, or what new options or
drivers enable the new feature. This does not need to restate the subject line
or echo the code if the code is self-evident — but if it is not self-evident,
this is the chance to explain what you're doing and why, so that the reviewer
doesn't have to guess or ask.

The majority of my commit messages have exactly three sentences (plus the
subject line) with exactly these three phrases: "Without this patch", "This is a
problem because", "This patch solves the problem by". It's not beautiful prose,
but it's effective communication.

How to write *great* commit messages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When we write code internally for our employers, even when we practice code
review internally (though not everyone does that), we get into bad habits of not
properly explaining ourselves, because we're working within a small team of
people who all know what's in the sprint and what's been prioritized — we're all
headed in the same direction. We know all of our teammates, we trust that they
know the product at least as well as we do, so we let them get away with poor
explanations in commit messages. This is bad practice internally but it
translates especially badly to a global multi-company open source project that
is pulling in a hundred different directions. Someone who has never met you does
not trust that you know what you're doing, and they probably have completely
different ideas of what's important.

That's why a commit message shouldn't just be an explanation; it should be a
fierce argument for why the previous state of the world was suboptimal, and why
your solution is the best solution.

People on the internet do not know you, they don’t know your credentials, and
they don't take for granted that you probably know what you are doing. It is
your job to convince them that you've researched this problem, you’ve tested
your proposal extensively, and that you've considered and rejected all the other
options.

Explain your personal use case for the feature or the particular environment in
which you noticed the bug — even if your code isn’t perfect, framing the message
in this way helps the reviewer understand where you’re coming from and from that
perspective they can offer suggestions to improve the code.

Preemptively predict the questions that reviewers are going to ask you: Why did
you do it this way? Why did you make this change that seems unrelated? Answer
those questions in your commit message so that you can skip the back-and-forth
discussion during code review.

If you start out your proposal with this kind of certainty and compelling
evidence, your reviewers will be carried away by your argument and be less
likely to debate you on it. Long commit messages are not taboo: I encourage
them. If a two-line change requires three paragraphs of exposition to make a
compelling case, don't hesitate.

If you’re structuring your commit message this way, it will get you to think
truly deeply about the problem. Is it really a problem? Is it likely to be a
problem for anyone else? Is it objectively a problem or do you just have a
personal distaste for it? If you’re thinking about it in these terms then it’s
likely that the code is of higher quality and you’ll be prepared for the ensuing
discussion. Very often when I'm writing a commit message, I realize my approach
is wrong and I need to change it; being forced to explain myself uncovered
corner cases and alternatives that I hadn't thought about before.

Conclusion
~~~~~~~~~~

Once you've proposed your change, you're not done: follow through on it. Respond
to reviewers' feedback. Be humble to constructive criticism. Answer their
questions. Keep the dialog going. If the maintainers seem to be MIA, try to
connect with them in whatever communication forum the project uses. Reaching out
to the community — politely, patiently, and respectfully — is a good way to get
attention for your patch, figure out why it fell through the cracks, and to show
that you are engaged and willing to work with people to get the problem solved.
Continuing to follow through and be responsive shows that you care about your
change and that it's important to you, and that will make it important to
others.
